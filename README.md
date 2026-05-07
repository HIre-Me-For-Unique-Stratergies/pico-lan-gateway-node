# LAN Gateway Node

Version 1 of this project uses two Raspberry Pi Pico devices on the LAN:

- Pico 1 is the gateway.
- Pico 2 is the backend server.
- The laptop is only the client/test machine.

The gateway Pico announces itself, accepts HTTP requests, checks simple allow/block rules, renders the browser UI, fetches data from the backend Pico, and exposes gateway metrics.

This is a policy gateway for traffic sent to the Pico. It is not a full network firewall.

## Network Layout

```text
Laptop client
    |
    | HTTP request
    v
Pico 1 + W5500
Gateway Pico
    |
    | forwarded HTTP request
    v
Pico 2 + W5500
Backend Pico
```

Recommended DHCP reservations:

| Device | Example reserved IP | Purpose |
| --- | --- | --- |
| Pico 1 gateway | `GATEWAY_IP` | The laptop calls this IP. |
| Pico 2 backend | `BACKEND_IP` | The gateway forwards to this IP. |
| Laptop client | `LAPTOP_CLIENT_IP` | The gateway rules allow this client IP. |

Use DHCP on both Picos, then create DHCP reservations in the router portal. Bind each device MAC address to a fixed IP. This is better than hardcoding static IPs in firmware because the router avoids conflicts and the code stays simpler.

After creating the reservations:

- set `gateway_pico/config.py` `BACKEND_HOST` to the backend Pico IP currently printed by Thonny
- set `gateway_pico/config.py` rules to allow the laptop client IP
- set `backend_pico/config.py` `ALLOWED_GATEWAY_IP` to the gateway Pico IP
- test the gateway using the gateway Pico IP

Before copying files to the Picos, replace these placeholders:

| Placeholder | Replace with |
| --- | --- |
| `GATEWAY_IP` | The gateway Pico IP from Thonny or the router DHCP reservation. |
| `BACKEND_IP` | The backend Pico IP from Thonny or the router DHCP reservation. |
| `LAPTOP_CLIENT_IP` | The laptop/client IPv4 address allowed to use the gateway. |

## Project Structure

```text
LAN Gateway Node/
|-- README.md
|-- .gitignore
|-- docs/
|   |-- Interview Project Brief.md
|   |-- Project Description.txt
|   |-- Wiring.md
|   |-- Test Plan.md
|   |-- Security Notes.md
|   `-- Troubleshooting.md
|-- gateway_pico/
|   |-- main.py
|   |-- config.py
|   |-- discovery.py
|   |-- rules.py
|   |-- proxy.py
|   |-- metrics.py
|   `-- status_led.py
|-- backend_pico/
|   |-- main.py
|   |-- config.py
|   `-- status_led.py
```

## Device Responsibilities

| Device | Files copied to device | Responsibility |
| --- | --- | --- |
| Gateway Pico | files from `gateway_pico/` | W5500 Ethernet, discovery, rule checks, browser UI, backend data fetches, metrics, load test. |
| Backend Pico | files from `backend_pico/` | W5500 Ethernet and data-only HTTP backend on port `8080`. |
| Laptop client | none | Browser testing only. |

## MicroPython Firmware

Both Picos must be flashed with the W5500 EVB MicroPython UF2 firmware before copying the project files.

Use this UF2 firmware target:

```text
W5500_EVB_PICO
```

Download the UF2 from the MicroPython W5500 EVB Pico firmware page. Do not commit the UF2 binary to git.

Firmware source:

```text
https://micropython.org/download/W5500_EVB_PICO/
```

The UF2 filename used during development was:

```text
W5500_EVB_PICO-20260406-v1.28.0.uf2
```

The normal Pico MicroPython firmware may not include `socket` or `network.WIZNET5K`. If the Pico shows this error:

```text
ImportError: no module named 'socket'
```

flash the W5500 EVB MicroPython `.uf2` firmware build. The target name to look for is:

```text
W5500_EVB_PICO
```

After flashing, check in the Thonny shell on each Pico:

```python
import socket
import network
print(hasattr(network, "WIZNET5K"))
```

The final line should print:

```text
True
```

## Wiring

Use this exact same wiring for both Picos. The gateway Pico and backend Pico use the same GPIO placement in their `config.py` files.

| W5500 | Pico |
| --- | --- |
| VCC / 3.3V | 3V3(OUT) |
| GND | GND |
| SCK / SCLK | GP18 |
| MISO / SO / DOUT | GP16 |
| MOSI / SI / DIN | GP19 |
| CS / SS | GP17 |
| RST / RESET | GP20 |
| INT | Leave disconnected |
| NC | Leave disconnected |

Do not power the W5500 from `VBUS`, `VSYS`, or `3V3_EN`. Use `3V3(OUT)` and `GND`.

`GP0` is not used by this project and can be left disconnected.

Both `gateway_pico/config.py` and `backend_pico/config.py` use:

```python
SPI_ID = 0
SPI_SCK_PIN = 18
SPI_MOSI_PIN = 19
SPI_MISO_PIN = 16
W5500_CS_PIN = 17
W5500_RST_PIN = 20
```

## Switch Port Setting

Set the switch/router port for each W5500 to:

```text
Speed: Auto
Duplex: Auto
```

If auto negotiation does not work, manually set:

```text
100MF
```

This means 100 Mbps full duplex. Do not force `1000MF`, because the W5500 is a 10/100 Mbps Ethernet controller, not gigabit.

## Onboard LED Status

Both Pico firmwares use the onboard LED as a quick status indicator. On a standard Raspberry Pi Pico this is GP25. On boards that expose `Pin("LED")`, the firmware will use that automatically.

| LED pattern | Meaning |
| --- | --- |
| Slow blink | Starting up or waiting for Ethernet. |
| Solid on | Ethernet is connected and the service is running. |
| Quick blink | Gateway discovery packet was sent. |
| Double blink | Request was handled. |
| Fast flashing | Error, proxy failure, or bad request. |
| Off | Not running or fatal startup failure. |

## Gateway Pico Configuration

`gateway_pico/config.py` should point at the backend Pico:

```python
BACKEND_HOST = "BACKEND_IP"
BACKEND_PORT = 8080
BACKEND_TIMEOUT_SECONDS = 5
```

The rules should allow the laptop client IP:

```python
RULES = [
    ("LAPTOP_CLIENT_IP", "/", "allow"),
    ("LAPTOP_CLIENT_IP", "/backend", "allow"),
    ("LAPTOP_CLIENT_IP", "/status", "allow"),
    ("LAPTOP_CLIENT_IP", "/api", "allow"),
    ("LAPTOP_CLIENT_IP", "/metrics", "allow"),
    ("LAPTOP_CLIENT_IP", "/test/start", "allow"),
    ("ANY", "/admin", "block"),
]
```

## Backend Pico Configuration

`backend_pico/config.py` runs the backend HTTP server on:

```python
HTTP_HOST = "0.0.0.0"
HTTP_PORT = 8080
CLIENT_TIMEOUT_SECONDS = 5
ALLOWED_GATEWAY_IP = "GATEWAY_IP"
```

Reserve the backend Pico MAC address in the router portal so this device always receives the IP used by `BACKEND_HOST`.

The backend only accepts requests from `ALLOWED_GATEWAY_IP` and returns data only. This prevents the laptop from bypassing the gateway and keeps all user-facing UI on the gateway.

## Copy Files To Each Pico

Copy the contents of `gateway_pico/` to the root of Pico 1:

```text
/main.py
/config.py
/discovery.py
/rules.py
/proxy.py
/metrics.py
/status_led.py
```

Copy the contents of `backend_pico/` to the root of Pico 2:

```text
/main.py
/config.py
/status_led.py
```

Do not copy the folders themselves to the Pico root unless you change the imports. MicroPython automatically runs root `/main.py` when the Pico powers on.

## Endpoints

Use these browser paths for testing.

Gateway Pico paths:

| Endpoint | Purpose |
| --- | --- |
| `http://GATEWAY_IP/` | Gateway dashboard page with navigation links, gateway metrics, and gateway identity details. |
| `http://GATEWAY_IP/metrics` | Shows gateway counters and diagnostics as a standalone page. |
| `http://GATEWAY_IP/backend` | Gateway-rendered page showing protected backend data. |
| `http://GATEWAY_IP/status` | Gateway-rendered page using backend Pico `/status` data. |
| `http://GATEWAY_IP/api` | Gateway-rendered page using backend Pico `/api` data. |
| `http://GATEWAY_IP/test/start` | Runs a small backend load test from the gateway Pico. |
| `http://GATEWAY_IP/admin` | Intentionally blocked by the gateway rules. |

Backend Pico paths:

| Endpoint | Purpose |
| --- | --- |
| `http://BACKEND_IP:8080/` | Backend status JSON data. Should be blocked from the laptop. |
| `http://BACKEND_IP:8080/status` | Backend status JSON data. Should be blocked from the laptop. |
| `http://BACKEND_IP:8080/api` | Backend API JSON data. Should be blocked from the laptop. |
| `http://BACKEND_IP:8080/discover` | Backend discovery text data. Should be blocked from the laptop. |

Normal use should go through the gateway paths. Direct backend paths are blocked from the laptop so the gateway cannot be bypassed.

## Network Protocols Used

| Protocol | Where used | Purpose |
| --- | --- | --- |
| Ethernet | Both Picos through W5500 modules | Physical/wired LAN connection. |
| SPI | Pico to W5500 module on each device | Lets the Pico control the W5500 Ethernet chip. |
| DHCP | Both Picos, provided by the router | Gives each Pico an IP address. Router DHCP reservations keep those IPs stable. |
| IPv4 | Laptop, gateway Pico, backend Pico | Main addressing system, using the `GATEWAY_IP`, `BACKEND_IP`, and `LAPTOP_CLIENT_IP` values from your LAN. |
| TCP | Browser to gateway, gateway to backend | Reliable connection used by HTTP. |
| HTTP | Browser/gateway/backend paths | Main request/response protocol for `/`, `/status`, `/api`, `/metrics`, and `/test/start`. |
| UDP broadcast | Gateway discovery | Gateway sends discovery packets to `255.255.255.255` on UDP port `4210`. |

Protocols not used:

| Protocol | Reason |
| --- | --- |
| HTTPS / TLS | Not supported in this version; basic HTTP only. |
| DNS | IP addresses are used directly in the browser. |
| mDNS | Discovery is done with a simple UDP broadcast, not `.local` names. |
| ICMP | Not required by the application, though normal network tools like `ping` may use it. |
| Wi-Fi | Both devices are standard wired Picos using W5500 Ethernet modules. |

## Test Checklist

1. Flash W5500-compatible MicroPython firmware on both Picos.
2. Wire one W5500 module to each Pico.
3. Create router DHCP reservations:

```text
Gateway Pico: GATEWAY_IP
Backend Pico: BACKEND_IP
Laptop:       LAPTOP_CLIENT_IP
```

4. Copy `backend_pico/` files to Pico 2 root and power it on.
5. Confirm Pico 2 LED becomes solid on.
6. Test backend Pico directly from the laptop. This should now be blocked because direct laptop access bypasses the gateway:

```text
http://BACKEND_IP:8080/status
http://BACKEND_IP:8080/api
http://BACKEND_IP:8080/discover
http://BACKEND_IP:8080/
```

Expected direct backend response from the laptop:

```text
blocked
```

7. Copy `gateway_pico/` files to Pico 1 root and power it on.
8. Confirm Pico 1 LED becomes solid on.
9. Test gateway local endpoints:

```text
http://GATEWAY_IP/
http://GATEWAY_IP/metrics
```

10. Test gateway-rendered backend data pages:

```text
http://GATEWAY_IP/status
http://GATEWAY_IP/api
http://GATEWAY_IP/backend
```

11. Run the gateway load test from the browser:

```text
http://GATEWAY_IP/test/start
```

12. Check gateway metrics again:

```text
http://GATEWAY_IP/metrics
```

Expected gateway dashboard identity section:

```text
DEVICE=gateway-node;IP=GATEWAY_IP;PORT=80;MODE=proxy
```

Expected backend status data shown inside the gateway `/status` page:

```json
{"service":"lan-gateway-backend-pico","device":"backend-node","status":"ready","uptime_seconds":123}
```

If direct backend access is blocked but gateway access works, the gateway policy is doing its job.

All normal testing is done from the browser. The laptop does not need to run a Python server or helper script.

## Limits

- Basic HTTP only.
- No HTTPS termination.
- Few simultaneous sockets.
- Small request and response buffers.
- Simple rules only.
- Not suitable as a real firewall or high-load proxy.

## Short Definition

LAN Gateway Node is a two-Pico LAN gateway system where one Pico is the front-end gateway and policy gate, while the second Pico is a protected data-only backend service.
