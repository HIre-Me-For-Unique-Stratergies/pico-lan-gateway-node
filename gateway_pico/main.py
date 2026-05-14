import time
import socket

import machine
import network

import config
import auth
import audit_log
import discovery
import local_backend
import metrics
import rules
import status_led
import ui


REQUEST_BUFFER_SIZE = 1024
ACCEPT_TIMEOUT_SECONDS = 1
CLIENT_TIMEOUT_SECONDS = getattr(config, "CLIENT_TIMEOUT_SECONDS", 5)
MAX_REQUEST_BYTES = getattr(config, "MAX_REQUEST_BYTES", 2048)
MAX_BODY_BYTES = getattr(config, "MAX_BODY_BYTES", 512)
REQUEST_LOG_LIMIT = 25
REQUEST_LOG = []
RATE_LIMITS = {}
LOGIN_FAILURES = {}


def validate_config():
    errors = []

    if config.HTTP_PORT < 1 or config.HTTP_PORT > 65535:
        errors.append("HTTP_PORT must be between 1 and 65535")

    if config.MIN_ADMIN_PASSWORD_LENGTH < 8:
        errors.append("MIN_ADMIN_PASSWORD_LENGTH must be at least 8")

    if config.PASSWORD_HASH_ROUNDS < 100:
        errors.append("PASSWORD_HASH_ROUNDS must be at least 100")

    if config.SESSION_TIMEOUT_SECONDS < 60:
        errors.append("SESSION_TIMEOUT_SECONDS must be at least 60")

    if config.MAX_BODY_BYTES > config.MAX_REQUEST_BYTES:
        errors.append("MAX_BODY_BYTES must be less than or equal to MAX_REQUEST_BYTES")

    required_paths = ("/", "/setup", "/login", "/logout", "/metrics", "/health", "/export")
    configured_paths = [rule[1] for rule in config.RULES]

    for path in required_paths:
        if path not in configured_paths:
            errors.append("Missing route rule for %s" % path)

    if errors:
        for error in errors:
            print("Config error: %s" % error)
        raise ValueError("configuration validation failed")


def start_ethernet():
    spi = machine.SPI(
        config.SPI_ID,
        baudrate=config.SPI_BAUDRATE,
        sck=machine.Pin(config.SPI_SCK_PIN),
        mosi=machine.Pin(config.SPI_MOSI_PIN),
        miso=machine.Pin(config.SPI_MISO_PIN),
    )

    nic = network.WIZNET5K(
        spi,
        machine.Pin(config.W5500_CS_PIN),
        machine.Pin(config.W5500_RST_PIN),
    )
    nic.active(True)

    while not nic.isconnected():
        print("Waiting for Ethernet connection...")
        status_led.waiting_for_network()
        time.sleep(1)

    ip_address = nic.ifconfig()[0]
    print("Ethernet connected: %s" % ip_address)
    status_led.ready()
    return ip_address


def send_response(client, status, content_type, body, extra_headers=None):
    if isinstance(body, str):
        body = body.encode("utf-8")

    response = (
        "HTTP/1.0 %s\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %s\r\n"
        "Connection: close\r\n"
    ) % (status, content_type, len(body))

    if extra_headers:
        for name, value in extra_headers:
            response += "%s: %s\r\n" % (name, value)

    response += "\r\n"

    send_all(client, response.encode("utf-8") + body)


def send_all(client, data):
    total_sent = 0

    while total_sent < len(data):
        sent = client.send(data[total_sent:])
        if sent is None:
            return
        if sent == 0:
            raise OSError("socket send failed")
        total_sent += sent


def _split_header_body(request_bytes):
    marker = b"\r\n\r\n"
    marker_index = request_bytes.find(marker)

    if marker_index < 0:
        return request_bytes, b""

    body_start = marker_index + len(marker)
    return request_bytes[:marker_index], request_bytes[body_start:]


def _content_length_from_header(header_bytes):
    try:
        header_text = header_bytes.decode("utf-8")
    except UnicodeError:
        return 0

    for line in header_text.split("\r\n")[1:]:
        if ":" not in line:
            continue

        name, value = line.split(":", 1)
        if name.strip().lower() == "content-length":
            try:
                return int(value.strip())
            except ValueError:
                return 0

    return 0


def read_request(client):
    request_bytes = b""

    while b"\r\n\r\n" not in request_bytes:
        chunk = client.recv(REQUEST_BUFFER_SIZE)
        if not chunk:
            break
        request_bytes += chunk

        if len(request_bytes) > MAX_REQUEST_BYTES:
            raise ValueError("request too large")

    header_bytes, body_bytes = _split_header_body(request_bytes)
    content_length = _content_length_from_header(header_bytes)

    if content_length < 0 or content_length > MAX_BODY_BYTES:
        raise ValueError("request body too large")

    while len(body_bytes) < content_length:
        chunk = client.recv(min(REQUEST_BUFFER_SIZE, content_length - len(body_bytes)))
        if not chunk:
            break
        body_bytes += chunk

        if len(header_bytes) + len(body_bytes) > MAX_REQUEST_BYTES:
            raise ValueError("request too large")

    return header_bytes + b"\r\n\r\n" + body_bytes[:content_length]


def parse_query(query_string):
    params = {}

    if not query_string:
        return params

    for pair in query_string.split("&"):
        key_value = pair.split("=", 1)
        key = url_decode(key_value[0])
        value = ""

        if len(key_value) == 2:
            value = url_decode(key_value[1])

        params[key] = value

    return params


def url_decode(value):
    value = value.replace("+", " ")
    result = ""
    index = 0

    while index < len(value):
        if value[index] == "%" and index + 2 < len(value):
            try:
                result += chr(int(value[index + 1:index + 3], 16))
                index += 3
                continue
            except ValueError:
                pass

        result += value[index]
        index += 1

    return result


def parse_request(request_bytes):
    request = request_bytes.decode("utf-8")
    head_body = request.split("\r\n\r\n", 1)
    request_lines = head_body[0].split("\r\n")
    body = ""

    if len(head_body) == 2:
        body = head_body[1]

    request_line = request_lines[0]
    parts = request_line.split()
    headers = {}

    if len(parts) < 2:
        return None, None, {}, {}, ""

    method = parts[0]
    target_parts = parts[1].split("?", 1)
    path = target_parts[0]
    query = {}

    if len(target_parts) == 2:
        query = parse_query(target_parts[1])

    for line in request_lines[1:]:
        if ":" in line:
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()

    return method, path, query, headers, body


def parse_form_body(body):
    return parse_query(body)


def log_request(client_ip, method, path, status):
    REQUEST_LOG.append(
        {
            "time": int(time.time()),
            "client_ip": client_ip,
            "method": method,
            "path": path,
            "status": status,
        }
    )

    while len(REQUEST_LOG) > REQUEST_LOG_LIMIT:
        REQUEST_LOG.pop(0)

    audit_log.append(client_ip, method, path, status)


def rate_limit_allows(client_ip):
    now = time.time()
    window = getattr(config, "RATE_LIMIT_WINDOW_SECONDS", 60)
    max_requests = getattr(config, "RATE_LIMIT_MAX_REQUESTS", 30)
    entry = RATE_LIMITS.get(client_ip)

    if not entry or now - entry["started"] >= window:
        RATE_LIMITS[client_ip] = {"started": now, "count": 1}
        return True

    entry["count"] += 1
    return entry["count"] <= max_requests


def login_lockout_remaining(client_ip):
    now = time.time()
    entry = LOGIN_FAILURES.get(client_ip)

    if not entry:
        return 0

    locked_until = entry.get("locked_until", 0)
    if locked_until > now:
        return int(locked_until - now)

    if locked_until:
        LOGIN_FAILURES.pop(client_ip, None)

    return 0


def record_login_failure(client_ip):
    now = time.time()
    window = config.LOGIN_FAILURE_WINDOW_SECONDS
    entry = LOGIN_FAILURES.get(client_ip)

    if not entry or now - entry["started"] >= window:
        entry = {"started": now, "count": 0, "locked_until": 0}
        LOGIN_FAILURES[client_ip] = entry

    entry["count"] += 1

    if entry["count"] >= config.LOGIN_FAILURE_LIMIT:
        entry["locked_until"] = now + config.LOGIN_LOCKOUT_SECONDS


def clear_login_failures(client_ip):
    LOGIN_FAILURES.pop(client_ip, None)


def check_rule(client_ip, path):
    action = rules.check(client_ip, path)

    if action != rules.ALLOW:
        metrics.increment("blocked_requests")
        return False

    metrics.increment("allowed_requests")
    return True


def handle_home(client, ip_address):
    discovery_message = discovery.build_message(ip_address)
    send_response(
        client,
        "200 OK",
        "text/html",
        ui.dashboard_page(
            ip_address,
            discovery_message,
            metrics.snapshot(),
            REQUEST_LOG,
            auth.session_seconds_remaining(),
        ),
    )


def send_setup_page(client, error=False):
    csrf_token = auth.ensure_csrf_token()
    send_response(
        client,
        "200 OK",
        "text/html",
        ui.setup_page(error, csrf_token),
        [("Set-Cookie", auth.csrf_cookie_header())],
    )


def send_login_page(client, error=False, message=""):
    csrf_token = auth.ensure_csrf_token()
    send_response(
        client,
        "200 OK",
        "text/html",
        ui.login_page(error, csrf_token, message),
        [("Set-Cookie", auth.csrf_cookie_header())],
    )


def handle_setup(client, method, headers, form):
    if auth.is_configured():
        send_response(client, "302 Found", "text/plain", "already_configured\n", [("Location", "/login")])
        return

    if method != "POST":
        send_setup_page(client)
        return

    if not auth.csrf_token_is_valid(headers, form):
        send_setup_page(client, True)
        return

    username = form.get("username", config.DEFAULT_ADMIN_USERNAME)
    password = form.get("password", "")

    if auth.save_first_run_setup(username, password):
        send_response(
            client,
            "302 Found",
            "text/plain",
            "setup_complete\n",
            [
                ("Location", "/"),
                ("Set-Cookie", auth.session_cookie_header()),
                ("Set-Cookie", auth.client_token_cookie_header()),
                ("Set-Cookie", auth.logout_csrf_cookie_header()),
            ],
        )
        return

    send_setup_page(client, True)


def handle_login(client, method, headers, form, client_ip):
    username = form.get("username", "")
    password = form.get("password", "")

    if method != "POST":
        send_login_page(client)
        return

    locked_for = login_lockout_remaining(client_ip)
    if locked_for > 0:
        send_login_page(client, True, "Too many failed attempts. Try again in %s seconds." % locked_for)
        metrics.increment("blocked_requests")
        return

    if not auth.csrf_token_is_valid(headers, form):
        record_login_failure(client_ip)
        send_login_page(client, True, "Login form expired. Try again.")
        return

    if auth.credentials_are_valid(username, password):
        clear_login_failures(client_ip)
        auth.begin_session()
        send_response(
            client,
            "302 Found",
            "text/plain",
            "login_ok\n",
            [
                ("Location", "/"),
                ("Set-Cookie", auth.session_cookie_header()),
                ("Set-Cookie", auth.client_token_cookie_header()),
                ("Set-Cookie", auth.logout_csrf_cookie_header()),
            ],
        )
        return

    record_login_failure(client_ip)
    send_login_page(client, True)


def handle_logout(client):
    auth.clear_session()
    send_response(
        client,
        "302 Found",
        "text/plain",
        "logout_ok\n",
        [
            ("Location", "/login"),
            ("Set-Cookie", auth.logout_cookie_header()),
            ("Set-Cookie", auth.logout_client_token_cookie_header()),
            ("Set-Cookie", auth.logout_csrf_cookie_header()),
        ],
    )


def handle_metrics(client):
    send_response(client, "200 OK", "text/html", ui.metrics_page(metrics.snapshot(), REQUEST_LOG))


def safe_config_text():
    return (
        "device=%s\n"
        "mode=%s\n"
        "http_port=%s\n"
        "discovery_enabled=%s\n"
        "session_timeout_seconds=%s\n"
        "rate_limit_window_seconds=%s\n"
        "rate_limit_max_requests=%s\n"
        "login_failure_limit=%s\n"
        "login_lockout_seconds=%s\n"
        "audit_log_max_lines=%s\n"
    ) % (
        config.DEVICE_NAME,
        config.MODE,
        config.HTTP_PORT,
        config.DISCOVERY_ENABLED,
        config.SESSION_TIMEOUT_SECONDS,
        config.RATE_LIMIT_WINDOW_SECONDS,
        config.RATE_LIMIT_MAX_REQUESTS,
        config.LOGIN_FAILURE_LIMIT,
        config.LOGIN_LOCKOUT_SECONDS,
        config.AUDIT_LOG_MAX_LINES,
    )


def handle_health(client, ip_address):
    text = fetch_backend_text("/health", ip_address)
    send_response(client, "200 OK", "application/json", text)


def handle_export(client, ip_address):
    body = (
        "# LAN Gateway Node Status Export\n"
        "\n"
        "## Identity\n"
        "%s\n"
        "\n"
        "## Metrics\n"
        "%s"
        "\n"
        "## Safe Config\n"
        "%s"
        "\n"
        "## Health\n"
        "%s"
        "\n"
        "## Recent Audit Log\n"
        "%s\n"
    ) % (
        discovery.build_message(ip_address),
        metrics.as_text(),
        safe_config_text(),
        fetch_backend_text("/health", ip_address),
        "\n".join(audit_log.tail(25)),
    )
    send_response(client, "200 OK", "text/plain", body)


def handle_load_test(client, ip_address):
    result = local_backend.run_load_test("/status", ip_address, 10)
    metrics.increment("load_test_requests", result["requests"])
    metrics.increment("load_test_successes", result["successes"])
    metrics.increment("load_test_failures", result["failures"])
    send_response(client, "200 OK", "text/html", ui.load_test_page(result))


def fetch_backend_text(path, ip_address):
    try:
        text = local_backend.fetch_text(path, ip_address, auth.backend_token())
        metrics.increment("proxied_requests")
        return text
    except Exception as exc:
        metrics.increment("proxy_failures")
        status_led.error()
        raise exc


def handle_backend_summary(client, ip_address):
    try:
        status_text = fetch_backend_text("/status", ip_address)
        api_text = fetch_backend_text("/api", ip_address)
        send_response(
            client,
            "200 OK",
            "text/html",
            ui.backend_summary_page(status_text, api_text),
        )
    except Exception as exc:
        send_response(client, "502 Bad Gateway", "text/plain", "proxy_error=%s\n" % exc)


def handle_backend_data(client, path, title, ip_address):
    try:
        text = fetch_backend_text(path, ip_address)
        send_response(
            client,
            "200 OK",
            "text/html",
            ui.backend_data_page(title, "Gateway-rendered backend data from %s." % path, text),
        )
    except Exception as exc:
        send_response(client, "502 Bad Gateway", "text/plain", "proxy_error=%s\n" % exc)


def handle_client(client, address, ip_address):
    client_ip = address[0]

    try:
        client.settimeout(CLIENT_TIMEOUT_SECONDS)
        request_bytes = read_request(client)
        method, path, query, headers, body = parse_request(request_bytes)
        form = parse_form_body(body)

        if path is None or method not in ("GET", "POST"):
            send_response(client, "400 Bad Request", "text/plain", "bad_request\n")
            log_request(client_ip, method, path, "400")
            status_led.error()
            return

        if not rate_limit_allows(client_ip):
            metrics.increment("blocked_requests")
            send_response(client, "429 Too Many Requests", "text/plain", "rate_limited\n")
            log_request(client_ip, method, path, "429")
            status_led.request_handled()
            return

        if not check_rule(client_ip, path):
            send_response(client, "403 Forbidden", "text/plain", "blocked\n")
            log_request(client_ip, method, path, "403")
            status_led.request_handled()
            return

        if not auth.is_configured() and path != "/setup":
            send_response(client, "302 Found", "text/plain", "setup_required\n", [("Location", "/setup")])
            log_request(client_ip, method, path, "302")
        elif path == "/setup":
            handle_setup(client, method, headers, form)
            log_request(client_ip, method, path, "200")
        elif path == "/login":
            handle_login(client, method, headers, form, client_ip)
            log_request(client_ip, method, path, "200")
        elif path == "/logout":
            handle_logout(client)
            log_request(client_ip, method, path, "302")
        elif not auth.is_authenticated(headers) or not auth.client_token_is_valid(headers):
            send_login_page(client)
            log_request(client_ip, method, path, "200")
        elif path == "/":
            handle_home(client, ip_address)
            log_request(client_ip, method, path, "200")
        elif path == "/metrics":
            handle_metrics(client)
            log_request(client_ip, method, path, "200")
        elif path == "/health":
            handle_health(client, ip_address)
            log_request(client_ip, method, path, "200")
        elif path == "/export":
            handle_export(client, ip_address)
            log_request(client_ip, method, path, "200")
        elif path == "/test/start":
            handle_load_test(client, ip_address)
            log_request(client_ip, method, path, "200")
        elif path == "/backend":
            handle_backend_summary(client, ip_address)
            log_request(client_ip, method, path, "200")
        elif path == "/status":
            handle_backend_data(client, "/status", "Backend Status", ip_address)
            log_request(client_ip, method, path, "200")
        elif path == "/api":
            handle_backend_data(client, "/api", "Backend API", ip_address)
            log_request(client_ip, method, path, "200")
        else:
            send_response(client, "404 Not Found", "text/plain", "not_found\n")
            log_request(client_ip, method, path, "404")

        status_led.request_handled()
    except ValueError as exc:
        send_response(client, "413 Payload Too Large", "text/plain", "request_rejected=%s\n" % exc)
        log_request(client_ip, "UNKNOWN", "UNKNOWN", "413")
        status_led.error()
    except UnicodeError:
        send_response(client, "400 Bad Request", "text/plain", "bad_request\n")
        log_request(client_ip, "UNKNOWN", "UNKNOWN", "400")
        status_led.error()
    finally:
        client.close()


def run_http_server(ip_address):
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((config.HTTP_HOST, config.HTTP_PORT))
    server.listen(2)
    server.settimeout(ACCEPT_TIMEOUT_SECONDS)

    print("HTTP server listening on port %s" % config.HTTP_PORT)

    last_discovery = 0

    while True:
        now = time.time()

        if config.DISCOVERY_ENABLED and now - last_discovery >= config.DISCOVERY_INTERVAL_SECONDS:
            try:
                discovery.send_once(ip_address)
                status_led.discovery_sent()
            except Exception as exc:
                print("Discovery error: %s" % exc)
                status_led.error()
            last_discovery = now

        try:
            client, address = server.accept()
            handle_client(client, address, ip_address)
        except OSError:
            pass
        except Exception as exc:
            print("HTTP server error: %s" % exc)
            status_led.error()


def main():
    print("Starting %s..." % config.DEVICE_NAME)
    validate_config()
    ip_address = start_ethernet()

    if config.DISCOVERY_ENABLED:
        print("Discovery broadcasts enabled on UDP port %s" % config.DISCOVERY_PORT)
    else:
        print("Discovery broadcasts disabled")
    run_http_server(ip_address)


if __name__ == "__main__":
    main()
