import socket
import time

import machine
import network

import config
import status_led


REQUEST_BUFFER_SIZE = 1024
START_TIME = time.time()


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
    print("Backend Ethernet connected: %s" % ip_address)
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


def status_body():
    uptime_seconds = int(time.time() - START_TIME)
    return (
        '{"service":"lan-gateway-backend-pico",'
        '"device":"%s",'
        '"status":"ready",'
        '"uptime_seconds":%s}\n'
    ) % (config.DEVICE_NAME, uptime_seconds)


def discover_body(ip_address):
    return "DEVICE=%s;IP=%s;PORT=%s;MODE=backend\n" % (
        config.DEVICE_NAME,
        ip_address,
        config.HTTP_PORT,
    )


def is_allowed_client(client_ip):
    return client_ip == config.ALLOWED_GATEWAY_IP


def handle_client(client, address, ip_address):
    client_ip = address[0]

    try:
        client.settimeout(config.CLIENT_TIMEOUT_SECONDS)
        request_bytes = client.recv(REQUEST_BUFFER_SIZE)
        method, path = parse_request(request_bytes)
        print("Backend request from %s: %s %s" % (client_ip, method, path))

        if method != "GET" or path is None:
            status_led.error()
            send_response(client, "400 Bad Request", "text/plain", "bad_request\n")
            return

        if not is_allowed_client(client_ip):
            print("Blocked direct backend access from %s" % client_ip)
            send_response(client, "403 Forbidden", "text/plain", "blocked\n")
            status_led.request_handled()
            return

        if path == "/status":
            send_response(client, "200 OK", "application/json", status_body())
        elif path == "/api":
            send_response(client, "200 OK", "application/json", '{"message":"Hello from backend Pico"}\n')
        elif path == "/discover":
            send_response(client, "200 OK", "text/plain", discover_body(ip_address))
        else:
            send_response(client, "404 Not Found", "text/plain", "not_found\n")

        status_led.request_handled()
    except Exception as exc:
        print("Backend client error: %s" % exc)
        status_led.error()
    finally:
        time.sleep(0.05)
        client.close()


def run_http_server(ip_address):
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((config.HTTP_HOST, config.HTTP_PORT))
    server.listen(2)

    print("Backend HTTP server listening on port %s" % config.HTTP_PORT)

    while True:
        client, address = server.accept()
        handle_client(client, address, ip_address)


def main():
    print("Starting %s..." % config.DEVICE_NAME)
    ip_address = start_ethernet()
    run_http_server(ip_address)


if __name__ == "__main__":
    main()
