# Troubleshooting

<!--
Purpose: captures the common hardware, firmware, and network failures seen
while building the project, with direct checks for each one.
-->

## `ImportError: no module named 'socket'`

The Pico is running normal MicroPython firmware instead of the W5500 EVB firmware.

Flash both Picos with:

```text
W5500_EVB_PICO
```

Expected check in Thonny:

```python
import socket
import network
print(hasattr(network, "WIZNET5K"))
```

Expected result:

```text
True
```

## Pico Not Detected After Flashing

Try:

- unplug and replug without holding BOOTSEL
- use a known data USB cable
- use another USB port
- hold BOOTSEL and confirm `RPI-RP2` appears
- reflash the UF2 file

## LED Keeps Blinking

The code is running but Ethernet is not connected.

Check:

- W5500 power from `3V3(OUT)`
- common ground
- SCLK, MOSI, MISO, CS, and RST wiring
- Ethernet cable
- switch/router port
- switch port set to auto negotiation

## Direct Backend Works But Should Be Blocked

Check `backend_pico/config.py`:

```python
ALLOWED_GATEWAY_IP = "GATEWAY_IP"
```

This must match the gateway Pico IP, not the laptop IP.

## Gateway Returns `blocked`

The laptop IP is not allowed by `gateway_pico/config.py`.

Check:

```python
RULES = [
    ("LAPTOP_CLIENT_IP", "/status", "allow"),
]
```

Replace `LAPTOP_CLIENT_IP` with the laptop IPv4 address.

## Gateway Returns `proxy_error`

The gateway could not reach the backend.

Check:

- backend Pico is powered and solid LED
- `BACKEND_HOST` matches the backend Pico IP
- backend HTTP server is listening on port `8080`
- backend config allows the gateway IP
- both Picos are on the same LAN/subnet

## `ECONNRESET`

The gateway reached the backend, but the backend closed the socket during proxying.

Check the backend Thonny terminal for:

```text
Backend request from GATEWAY_IP: GET /status
```

If it prints a different client IP, update:

```python
ALLOWED_GATEWAY_IP = "GATEWAY_IP"
```
