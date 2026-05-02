import time
import socket

import machine
import network

import config
import discovery
import metrics
import proxy
import rules
import status_led


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


def send_response(client, status, content_type, body):
    if isinstance(body, str):
        body = body.encode("utf-8")

    response = (
        "HTTP/1.0 %s\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %s\r\n"
        "Connection: close\r\n"
        "\r\n"
    ) % (status, content_type, len(body))

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


def parse_request(request_bytes):
    request = request_bytes.decode("utf-8")
    request_line = request.split("\r\n", 1)[0]
    parts = request_line.split()

    if len(parts) < 2:
        return None, None

    method = parts[0]
    path = parts[1].split("?", 1)[0]
    return method, path


def check_rule(client_ip, path):
    action = rules.check(client_ip, path)

    if action != rules.ALLOW:
        metrics.increment("blocked_requests")
        return False

    metrics.increment("allowed_requests")
    return True


def handle_discover(client, ip_address):
    body = discovery.build_message(ip_address) + "\n"
    send_response(client, "200 OK", "text/plain", body)


def handle_metrics(client):
    send_response(client, "200 OK", "text/plain", metrics.as_text())


def handle_load_test(client):
    result = proxy.run_load_test("/status", 10)
    body = (
        "requests=%s\n"
        "successes=%s\n"
        "failures=%s\n"
        "elapsed_ms=%s\n"
    ) % (
        result["requests"],
        result["successes"],
        result["failures"],
        result["elapsed_ms"],
    )
    send_response(client, "200 OK", "text/plain", body)


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
        method, path = parse_request(request_bytes)

        if method != "GET" or path is None:
            send_response(client, "400 Bad Request", "text/plain", "bad_request\n")
            status_led.error()
            return

        if not check_rule(client_ip, path):
            send_response(client, "403 Forbidden", "text/plain", "blocked\n")
            status_led.request_handled()
            return

        if path == "/discover":
            handle_discover(client, ip_address)
        elif path == "/metrics":
            handle_metrics(client)
        elif path == "/test/start":
            handle_load_test(client)
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
