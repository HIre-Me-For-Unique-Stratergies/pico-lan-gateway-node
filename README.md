# LAN Gateway Node

Version 1 of this project is a small embedded LAN gateway built with a Raspberry Pi Pico and a W5500 Ethernet module.

The device sits on a local network, announces itself, accepts simple HTTP requests, checks basic allow/block rules, forwards approved requests to one backend server, and exposes simple metrics.

This is a policy gateway for traffic sent to the Pico. It is not a full network firewall.

## Version 1 Goals

- Get the Pico online with W5500 Ethernet.
- Broadcast a UDP discovery message on the LAN.
- Run a simple HTTP listener on the Pico.
- Allow or block requests by source IP and path.
- Forward approved `/status` requests to one backend server.
- Track request counters on a `/metrics` endpoint.
- Add a small backend test server for local development.

## Project Structure

```text
LAN Gateway Node/
├─ README.md
├─ Project Description.txt
├─ firmware/
│  ├─ main.py
│  ├─ config.py
│  ├─ discovery.py
│  ├─ rules.py
│  ├─ proxy.py
│  └─ metrics.py
└─ backend/
   └─ server.py
```

## File Responsibilities

| File | Purpose |
| --- | --- |
| `firmware/main.py` | Pico entry point. Starts Ethernet, discovery, HTTP handling, rules, proxy, and metrics. |
| `firmware/config.py` | Device name, network settings, backend IP/port, and rule settings. |
| `firmware/discovery.py` | Sends UDP broadcast packets so clients can find the gateway. |
| `firmware/rules.py` | Checks whether a client IP and path should be allowed or blocked. |
| `firmware/proxy.py` | Forwards approved requests to the backend server. |
| `firmware/metrics.py` | Stores counters for allowed, blocked, proxied, and failed requests. |
| `backend/server.py` | Simple backend server for testing proxy behavior. |

## Hardware

- Raspberry Pi Pico
- W5500 Ethernet module
- Ethernet cable
- Router or network switch
- PC or laptop for the backend server
- USB cable for Pico power and programming

## Typical Wiring

| W5500 | Pico |
| --- | --- |
| VCC | 3.3V |
| GND | GND |
| SCK | GP18 |
| MISO | GP16 |
| MOSI | GP19 |
| CS | GP17 |
| RST | GP20, optional |

Use 3.3V, keep wires short, and make sure all grounds are connected.

## Example Network

| Device | Example IP |
| --- | --- |
| Pico gateway | `192.168.1.50` |
| Backend server | `192.168.1.10:8080` |
| Laptop client | `192.168.1.100` |

## Version 1 Behavior

1. Pico starts Ethernet.
2. Pico gets or uses an IP address.
3. Pico broadcasts a discovery packet every few seconds.
4. Pico listens for HTTP requests.
5. Pico checks the source IP and request path.
6. Blocked requests receive a deny response.
7. Allowed `/status` requests are proxied to the backend.
8. Metrics are available from the Pico.

## Planned Endpoints

| Endpoint | Purpose |
| --- | --- |
| `/status` | Allowed request path that can be proxied to the backend. |
| `/metrics` | Pico-side counters and simple diagnostics. |
| `/discover` | Local device information. |

## Example Discovery Packet

```text
DEVICE=gateway-node;IP=192.168.1.50;PORT=80;MODE=proxy
```

## Example Rules

| Source IP | Path | Action |
| --- | --- | --- |
| `192.168.1.100` | `/status` | allow |
| `192.168.1.100` | `/metrics` | allow |
| `ANY` | `/admin` | block |
| `ANY` | `*` | deny |

## Build Order

1. Bring up W5500 networking.
2. Add UDP discovery.
3. Add a basic HTTP server.
4. Add the rule checker.
5. Add `/status` proxy forwarding.
6. Add `/metrics` counters.
7. Add the backend test server.

## Limits

- Basic HTTP only.
- No HTTPS termination.
- Few simultaneous sockets.
- Small request and response buffers.
- Simple rules only.
- Not suitable as a real firewall or high-load proxy.

## Short Definition

LAN Gateway Node is a discoverable Pico-based LAN proxy that protects access to a backend service with simple rules and reports basic gateway metrics.
