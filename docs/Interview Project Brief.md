# LAN Gateway Node - Interview Project Brief

## Project Summary

LAN Gateway Node is a single-device embedded networking project built with a Raspberry Pi Pico and a W5500 Ethernet module.

The project demonstrates a protected LAN service architecture:

```text
LAN browser client -> Pico Gateway Node -> local protected backend module
```

Any device on the LAN can reach the login page. Protected routes require an admin session cookie and a generated client token. The Pico serves the UI, local backend data, metrics, request logs, and a small load test endpoint.

## Purpose

The purpose of the project is to show how a constrained embedded device can run a small authenticated LAN application with clear operational limits.

It demonstrates:

- wired Ethernet with a W5500 module
- DHCP addressing and displaying the current assigned IP
- HTTP request parsing on MicroPython
- first-run admin setup
- password hashing and generated access tokens
- CSRF protection for setup and login forms
- failed-login lockout
- persistent rotating audit logging
- route allow/block rules
- request logging and rate limiting
- optional UDP discovery, disabled by default
- runtime status indicators using the onboard LED
- honest security documentation for TLS and physical-access limits

## What Was Built

The system uses one Raspberry Pi Pico.

| Component | Role |
| --- | --- |
| Root `main.py` | MicroPython boot script that starts the app automatically. |
| `gateway_pico/main.py` | HTTP server, routing, login flow, lockout, CSRF checks, logging, and rate limiting. |
| `gateway_pico/audit_log.py` | Small rotating persistent request log. |
| `gateway_pico/local_backend.py` | Protected local backend data provider. |
| `settings.py` | Generated password salt/hash settings on the Pico. Not committed to git. |

Browser endpoints include:

```text
http://PICO_IP/
http://PICO_IP/setup
http://PICO_IP/login
http://PICO_IP/status
http://PICO_IP/api
http://PICO_IP/metrics
```

## How It Works

1. The Pico connects to the LAN through the W5500 Ethernet module.
2. The router gives the Pico an IPv4 address using DHCP.
3. Root `/main.py` starts the application from `/gateway_pico/main.py`.
4. On first launch, unauthenticated users are redirected to `/setup`.
5. Setup creates a password salt and repeated password hash in `settings.py`.
6. Login generates runtime session and client tokens, stores only their hashes in memory, and sets short-lived cookies.
7. Protected routes require both cookies.
8. The gateway serves local backend data through `gateway_pico/local_backend.py`.
9. Metrics and recent request logs are shown in the browser.
10. Rate limiting rejects clients that exceed the configured request window.
11. Expired sessions are cleared and must log in again.
12. Repeated failed logins trigger a temporary lockout.
13. `/health` and `/export` expose safe operational diagnostics.

## Security Positioning

The firmware includes password setup, salted password hashing, runtime token-backed login, CSRF-protected forms, failed-login lockout, automatic session expiry, persistent audit logging, rate limiting, health/export diagnostics, and disabled discovery by default.

It does not claim to provide production HTTPS or physical tamper resistance on the Pico itself. For encrypted access, place the Pico behind a TLS reverse proxy, VPN, or router that terminates HTTPS. For physical security, use an enclosure and restrict access to USB data, BOOTSEL, reset, and SWD pins.

## Short Interview Explanation

```text
I built a single-Pico LAN gateway application using MicroPython and a W5500 Ethernet module. On first launch it creates an admin account with a salted repeated password hash, then protects operational routes behind runtime session and client tokens that expire automatically. The app protects setup/login forms with CSRF tokens, locks out repeated failed logins, shows its current DHCP address, serves local backend diagnostics, records a rotating audit log, rate-limits clients, and keeps UDP discovery disabled by default. I also documented the boundaries clearly: HTTPS should be handled by a TLS reverse proxy or VPN, and a standard Pico cannot guarantee secure boot or flash encryption against physical attackers.
```
