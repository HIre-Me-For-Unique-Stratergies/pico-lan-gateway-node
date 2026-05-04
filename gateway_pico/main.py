import time
import socket

import machine
import network

import config
import auth
import discovery
import metrics
import proxy
import rules
import status_led
import ui


REQUEST_BUFFER_SIZE = 1024
ACCEPT_TIMEOUT_SECONDS = 1
CLIENT_TIMEOUT_SECONDS = 5


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
    request_lines = request.split("\r\n")
    request_line = request_lines[0]
    parts = request_line.split()
    headers = {}

    if len(parts) < 2:
        return None, None, {}, {}

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

    return method, path, query, headers


def check_rule(client_ip, path):
    action = rules.check(client_ip, path)

    if action != rules.ALLOW:
        metrics.increment("blocked_requests")
        return False

    metrics.increment("allowed_requests")
    return True


def handle_home(client, ip_address):
    discovery_message = discovery.build_message(ip_address)
    send_response(client, "200 OK", "text/html", ui.dashboard_page(ip_address, discovery_message))


def handle_login(client, query):
    username = query.get("username", "")
    password = query.get("password", "")

    if not username and not password:
        send_response(client, "200 OK", "text/html", ui.login_page())
        return

    if auth.credentials_are_valid(username, password):
        send_response(
            client,
            "302 Found",
            "text/plain",
            "login_ok\n",
            [
                ("Location", "/"),
                ("Set-Cookie", auth.session_cookie_header()),
            ],
        )
        return

    send_response(client, "401 Unauthorized", "text/html", ui.login_page(True))


def handle_logout(client):
    send_response(
        client,
        "302 Found",
        "text/plain",
        "logout_ok\n",
        [
            ("Location", "/login"),
            ("Set-Cookie", auth.logout_cookie_header()),
        ],
    )


def handle_metrics(client):
    send_response(client, "200 OK", "text/html", ui.metrics_page(metrics.snapshot()))


def handle_load_test(client):
    result = proxy.run_load_test("/status", 10)
    send_response(client, "200 OK", "text/html", ui.load_test_page(result))


def handle_proxy(client, path):
    try:
        print("Proxying %s to %s:%s" % (path, config.BACKEND_HOST, config.BACKEND_PORT))
        response = proxy.forward_get(path)
        metrics.increment("proxied_requests")
        send_all(client, response)
    except Exception as exc:
        metrics.increment("proxy_failures")
        status_led.error()
        send_response(client, "502 Bad Gateway", "text/plain", "proxy_error=%s\n" % exc)


def handle_client(client, address, ip_address):
    client_ip = address[0]

    try:
        client.settimeout(CLIENT_TIMEOUT_SECONDS)
        request_bytes = client.recv(REQUEST_BUFFER_SIZE)
        method, path, query, headers = parse_request(request_bytes)

        if method != "GET" or path is None:
            send_response(client, "400 Bad Request", "text/plain", "bad_request\n")
            status_led.error()
            return

        if not check_rule(client_ip, path):
            send_response(client, "403 Forbidden", "text/plain", "blocked\n")
            status_led.request_handled()
            return

        if path == "/login":
            handle_login(client, query)
        elif path == "/logout":
            handle_logout(client)
        elif not auth.is_authenticated(headers):
            send_response(client, "200 OK", "text/html", ui.login_page())
        elif path == "/":
            handle_home(client, ip_address)
        elif path == "/metrics":
            handle_metrics(client)
        elif path == "/test/start":
            handle_load_test(client)
        elif path == "/backend":
            handle_proxy(client, "/")
        elif path == "/status" or path == "/api":
            handle_proxy(client, path)
        else:
            send_response(client, "404 Not Found", "text/plain", "not_found\n")

        status_led.request_handled()
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

        if now - last_discovery >= config.DISCOVERY_INTERVAL_SECONDS:
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
    ip_address = start_ethernet()

    print("Discovery broadcasts enabled on UDP port %s" % config.DISCOVERY_PORT)
    run_http_server(ip_address)


if __name__ == "__main__":
    main()
