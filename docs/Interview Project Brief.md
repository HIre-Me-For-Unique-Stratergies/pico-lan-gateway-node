# LAN Gateway Node - Interview Project Brief

## Project Summary

LAN Gateway Node is a small two-device embedded networking project built with Raspberry Pi Pico boards and W5500 Ethernet modules.

The project demonstrates a protected LAN service architecture:

```text
Laptop browser -> Gateway Pico -> Backend Pico
```

The laptop cannot access the backend service directly. It must go through the gateway. The gateway checks simple rules, forwards approved requests, blocks disallowed paths, and records basic metrics.

## Purpose

The purpose of the project is to show how a small embedded device can act as a lightweight policy gateway for another LAN device.

It is not designed to be a full firewall or enterprise reverse proxy. Instead, it demonstrates practical networking concepts on constrained hardware:

- wired Ethernet with W5500 modules
- DHCP addressing and router reservations
- HTTP request handling
- TCP socket forwarding
- source IP and path-based access rules
- backend isolation
- simple UDP discovery
- runtime status indicators using onboard LEDs
- gateway metrics and basic load testing

## What Was Built

The system uses two Raspberry Pi Pico devices.

| Device | IP address | Role |
| --- | --- | --- |
| Gateway Pico | `GATEWAY_IP` | Public entry point used by the laptop browser. |
| Backend Pico | `BACKEND_IP` | Protected backend service. |
| Laptop | `LAPTOP_CLIENT_IP` | Client/test machine. |

The gateway Pico exposes browser endpoints such as:

```text
http://GATEWAY_IP/status
http://GATEWAY_IP/api
http://GATEWAY_IP/metrics
```

The main gateway dashboard also shows the gateway identity string, including device name, IP, port, and mode.

The backend Pico runs its own HTTP server on port `8080`, but it only accepts requests from the gateway Pico.

Direct laptop access to the backend is intentionally blocked:

```text
http://BACKEND_IP:8080/status
```

The expected direct backend response from the laptop is:

```text
blocked
```

## How It Works

1. Both Pico boards connect to the LAN using W5500 Ethernet modules.
2. The router gives each Pico an IPv4 address using DHCP.
3. The gateway Pico listens for HTTP requests on port `80`.
4. The laptop sends a browser request to the gateway Pico.
5. The gateway checks the source IP and requested path against its rules.
6. If the request is allowed, the gateway opens a TCP connection to the backend Pico.
7. The gateway forwards the request to the backend Pico on port `8080`.
8. The backend Pico checks that the request came from the gateway IP.
9. If allowed, the backend responds.
10. The gateway relays the backend response back to the laptop browser.

This proves that clients can use the backend service only through the gateway policy layer.

## Network Setup

The network uses DHCP reservations in the router portal so the devices keep stable IP addresses.

| Device | Reserved IP |
| --- | --- |
| Gateway Pico | `GATEWAY_IP` |
| Backend Pico | `BACKEND_IP` |
| Laptop client | `LAPTOP_CLIENT_IP` |

This avoids hardcoding static IP settings on the Pico devices while still keeping the system predictable.

The gateway is configured to forward to:

```python
BACKEND_HOST = "BACKEND_IP"
BACKEND_PORT = 8080
```

The backend is configured to only trust the gateway:

```python
ALLOWED_GATEWAY_IP = "GATEWAY_IP"
```

## Protocols Used

The project uses:

- Ethernet for wired LAN connectivity
- SPI between each Pico and its W5500 module
- DHCP for address assignment
- IPv4 for LAN addressing
- TCP for reliable socket communication
- HTTP for browser and backend requests
- UDP broadcast for gateway discovery

It does not use HTTPS, DNS, mDNS, Wi-Fi, or full firewall packet filtering.

## Hardware Setup

Both Picos are flashed with the W5500 EVB MicroPython UF2 firmware before the project files are copied onto them.

Firmware target:

```text
W5500_EVB_PICO
```

UF2 file used in this project:

```text
W5500_EVB_PICO-20260406-v1.28.0.uf2
```

Each Pico is wired to a W5500 Ethernet module using the same GPIO layout:

| W5500 | Pico |
| --- | --- |
| VCC / 3.3V | 3V3(OUT) |
| GND | GND |
| SCK / SCLK | GP18 |
| MISO / SO / DOUT | GP16 |
| MOSI / SI / DIN | GP19 |
| CS / SS | GP17 |
| RST / RESET | GP20 |

This firmware is required because the normal Pico MicroPython firmware may not include `socket` and `network.WIZNET5K` support.

## Status LEDs

The onboard LEDs provide quick status feedback:

| LED pattern | Meaning |
| --- | --- |
| Slow blink | Waiting for Ethernet. |
| Solid on | Connected and running. |
| Double blink | Request handled. |
| Fast flashing | Error or bad request. |

## What This Demonstrates

This project demonstrates that I can:

- design a small networked embedded system
- work with constrained MicroPython hardware
- use LAN protocols directly rather than relying on high-level frameworks
- structure a project across multiple devices
- build and test a simple gateway/proxy architecture
- apply access-control logic at the application layer
- debug real hardware, firmware, IP addressing, and socket behavior
- document a project clearly enough for setup and presentation

## Future Improvements

Possible next steps:

- add a real sensor or actuator to the backend Pico
- add a small web dashboard to the gateway
- add configurable rules through a protected admin endpoint
- add request logs to `/metrics`
- add stronger authentication, such as a shared token
- move from DHCP-only discovery to mDNS or a small desktop discovery tool
- use router firewall rules or VLANs for stronger backend isolation

## Short Interview Explanation

I built a two-Pico LAN gateway system. One Pico acts as a gateway and the second Pico acts as a protected backend server. The laptop can only reach the backend through the gateway. The gateway checks source IP and path rules, forwards allowed requests over TCP/HTTP, blocks disallowed requests, and exposes metrics. The backend also rejects direct laptop access and only accepts traffic from the gateway IP. This demonstrates embedded Ethernet, socket programming, simple reverse proxy behavior, and application-level access control on constrained hardware.
