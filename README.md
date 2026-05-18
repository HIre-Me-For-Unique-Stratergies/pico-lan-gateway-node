# LAN Gateway Node

LAN Gateway Node now runs as a single Raspberry Pi Pico + W5500 LAN service.

The Pico hosts the browser UI, authentication, protected local backend data, metrics, request logging, and a small load-test endpoint. It is not tied to one laptop IP address.

## Network Layout

```text
Laptop / phone / LAN client
    |
    | HTTP request
    v
Raspberry Pi Pico + W5500
Single-device LAN Gateway Node
```

The dashboard and `/status` output display the current DHCP address assigned to the Pico. Use a router DHCP reservation if you want the address to stay stable.

## First Run

On first boot, browse to the Pico IP address. The firmware redirects to:

```text
http://PICO_IP/setup
```

Create the admin password. The username defaults to:

```text
admin
```

Setup creates `settings.py` on the Pico with:

- admin username
- admin password salt
- repeated SHA-256 password hash
- password hash round count

The browser is signed in after setup. Later, sign in at:

```text
http://PICO_IP/login
```

Do not commit `settings.py`.

## Endpoints

| Endpoint | Purpose |
| --- | --- |
| `/setup` | First-run admin password setup. |
| `/login` | Admin login. |
| `/logout` | Clears session cookies. |
| `/` | Dashboard with current IP, metrics, and request log. |
| `/metrics` | Metrics and recent request log. |
| `/backend` | Gateway-rendered local backend summary. |
| `/status` | Local backend status data. |
| `/api` | Local backend API data. |
| `/health` | JSON health and diagnostics. |
| `/export` | Plain-text status export without secrets. |
| `/test/start` | Runs a small in-process backend load test. |
| `/admin` | Intentionally blocked. |

Protected routes require a valid login session and generated client token cookie.
Sessions remain valid while the Pico is running and the browser keeps making authenticated requests.
After the configured inactivity timeout, the session expires and the browser must log in again.

## Security Model

Implemented in firmware:

- first-run admin password setup
- password submitted with `POST`
- salted password hashing
- generated runtime session token
- generated runtime client token
- generated runtime internal backend token
- automatic inactivity-based session expiry
- CSRF token on setup and login forms
- failed-login lockout
- persistent rotating audit log
- boot-time config validation
- health and safe status export endpoints
- UDP discovery disabled by default
- request logging
- simple per-client rate limiting
- no fixed client IP requirement

`settings.py` does not store reusable plaintext passwords or bearer tokens. Runtime tokens are held in memory and validated by hash.

Not provided directly by Pico firmware:

- production HTTPS/TLS serving
- secure boot
- flash encryption
- protection against someone with physical access replacing or reading firmware
- router firewall or VLAN configuration

For encrypted access, place the Pico behind a LAN TLS reverse proxy, VPN, or router that terminates HTTPS and restricts direct Pico access. For physical security, use a locked enclosure and prevent access to USB data, BOOTSEL, reset, and SWD pins.

See [docs/Security Notes.md](docs/Security%20Notes.md), [docs/HTTPS Deployment.md](docs/HTTPS%20Deployment.md), and [docs/Recovery.md](docs/Recovery.md) for details.

## Boot Script And Files

The root [main.py](main.py) is the parent boot script. MicroPython runs root `/main.py` automatically, and this script starts the application from `gateway_pico/`.

Copy this layout to the Pico:

```text
/main.py
/gateway_pico/
  audit_log.py
  auth.py
  config.py
  discovery.py
  local_backend.py
  main.py
  metrics.py
  rules.py
  status_led.py
  ui.py
```

The local backend runs inside `gateway_pico/local_backend.py`.

## Firmware

Both networking and sockets require the W5500 EVB MicroPython firmware target:

```text
W5500_EVB_PICO
```

Check in Thonny:

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

Do not power the W5500 from `VBUS`, `VSYS`, or `3V3_EN`.
