# Test Plan

<!--
Purpose: gives a repeatable browser-based test sequence for confirming that
single-Pico setup, login, local backend data, blocking rules, metrics, logging,
and rate limiting work.
-->

## Startup

1. Flash the Pico with W5500-compatible MicroPython firmware.
2. Copy root `main.py` and the `gateway_pico/` folder to the Pico root.
3. Power the Pico and wait for the onboard LED to become solid.
4. Read the current Pico IP address from Thonny serial output or from the router DHCP client list.

## First-Run Setup

Open:

```text
http://PICO_IP/
```

Expected result:

```text
Redirects to /setup
```

Create the admin account:

```text
Username: admin
Password: choose on first launch
```

Expected result:

```text
settings.py is created on the Pico
```

The browser should receive the session and client-token cookies, then redirect to `/`.

`settings.py` should contain only username and password hash settings. It should not contain the admin password, session token, client token, or backend token.

## Login

Open:

```text
http://PICO_IP/login
```

Sign in with the admin password.

Expected result:

```text
Redirects to /
```

The browser receives:

```text
gateway_session cookie
gateway_client_token cookie
```

Both cookies should include a `Max-Age` matching `SESSION_TIMEOUT_SECONDS`.

## Protected Routes

Open:

```text
http://PICO_IP/
http://PICO_IP/metrics
http://PICO_IP/backend
http://PICO_IP/status
http://PICO_IP/api
http://PICO_IP/health
http://PICO_IP/export
```

Expected result:

```text
Each page loads after login.
```

Expected `/status` shape:

```json
{"service":"lan-gateway-node","device":"gateway-node","mode":"single-pico","ip_address":"PICO_IP","status":"ready","uptime_seconds":123}
```

## Request Log

Open:

```text
http://PICO_IP/metrics
```

Expected result:

```text
Recent client IP, method, path, and status entries are visible.
```

The Pico should also keep a rotating persistent audit log:

```text
audit.log
```

This file should contain recent method, path, client, and status entries.

## Failed Login Lockout

Submit the wrong password at `/login` repeatedly.

Expected result after `LOGIN_FAILURE_LIMIT` failures:

```text
Too many failed attempts.
```

The client should remain locked out until `LOGIN_LOCKOUT_SECONDS` expires.

## CSRF Protection

Open `/login`, then inspect the form source.

Expected result:

```text
csrf_token hidden field
gateway_csrf cookie
```

Submitting a login form without the matching CSRF token should fail.

## Health And Export

Open:

```text
http://PICO_IP/health
http://PICO_IP/export
```

Expected result:

```text
/health returns JSON diagnostics.
/export returns safe text diagnostics and recent audit log lines without secrets.
```

## Load Test

Open:

```text
http://PICO_IP/test/start
```

Expected shape:

```text
requests=10
successes=10
failures=0
elapsed_ms=...
```

Check metrics again:

```text
http://PICO_IP/metrics
```

Expected counters to increase:

```text
allowed_requests
proxied_requests
load_test_requests
load_test_successes
```

## Blocked Route

Open:

```text
http://PICO_IP/admin
```

Expected result:

```text
blocked
```

## Discovery

UDP discovery is disabled by default in `gateway_pico/config.py`:

```python
DISCOVERY_ENABLED = False
```

No discovery broadcasts should appear unless this value is changed to `True`.
