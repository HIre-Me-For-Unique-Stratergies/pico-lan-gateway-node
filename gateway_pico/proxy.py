import socket
import time

import config
import metrics


RECV_SIZE = 1024
MAX_RESPONSE_BYTES = 8192


def _send_all(sock, data):
    total_sent = 0

    while total_sent < len(data):
        sent = sock.send(data[total_sent:])
        if sent is None:
            return
        if sent == 0:
            raise OSError("backend socket send failed")
        total_sent += sent


def _open_backend_socket():
    address_info = socket.getaddrinfo(config.BACKEND_HOST, config.BACKEND_PORT)[0][-1]
    sock = socket.socket()
    sock.settimeout(config.BACKEND_TIMEOUT_SECONDS)
    sock.connect(address_info)
    return sock


def forward_get(path):
    sock = _open_backend_socket()

    try:
        request = (
            "GET %s HTTP/1.0\r\n"
            "Host: %s:%s\r\n"
            "Connection: close\r\n"
            "\r\n"
        ) % (path, config.BACKEND_HOST, config.BACKEND_PORT)

        _send_all(sock, request.encode("utf-8"))

        response = b""
        while len(response) < MAX_RESPONSE_BYTES:
            try:
                chunk = sock.recv(RECV_SIZE)
            except OSError as exc:
                if response:
                    break
                raise exc

            if not chunk:
                break
            response += chunk

        if not response:
            raise OSError("empty backend response")

        return response
    finally:
        sock.close()


def run_load_test(path="/status", request_count=10):
    successes = 0
    failures = 0
    started = time.ticks_ms()

    for _ in range(request_count):
        metrics.increment("load_test_requests")

        try:
            response = forward_get(path)
            if response.startswith(b"HTTP/1.0 200") or response.startswith(b"HTTP/1.1 200"):
                successes += 1
                metrics.increment("load_test_successes")
            else:
                failures += 1
                metrics.increment("load_test_failures")
        except Exception:
            failures += 1
            metrics.increment("load_test_failures")

    elapsed_ms = time.ticks_diff(time.ticks_ms(), started)

    return {
        "requests": request_count,
        "successes": successes,
        "failures": failures,
        "elapsed_ms": elapsed_ms,
    }
