import socket
import time

import config


MODE = "proxy"


def build_message(ip_address):
    return "DEVICE=%s;IP=%s;PORT=%s;MODE=%s" % (
        config.DEVICE_NAME,
        ip_address,
        config.HTTP_PORT,
        MODE,
    )


def send_once(ip_address):
    message = build_message(ip_address)
    address = (config.DISCOVERY_BROADCAST_IP, config.DISCOVERY_PORT)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(message.encode("utf-8"), address)
    finally:
        sock.close()

    return message


def run(ip_address):
    while True:
        send_once(ip_address)
        time.sleep(config.DISCOVERY_INTERVAL_SECONDS)
