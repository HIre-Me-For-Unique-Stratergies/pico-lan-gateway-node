# Test Plan

<!--
Purpose: gives a repeatable browser-based test sequence for confirming that
the backend, gateway, blocking rules, proxying, and metrics all work.
-->

Before testing, replace placeholders in both config files:

| Placeholder | Replace with |
| --- | --- |
| `GATEWAY_IP` | Gateway Pico IP from Thonny or router DHCP reservation. |
| `BACKEND_IP` | Backend Pico IP from Thonny or router DHCP reservation. |
| `LAPTOP_CLIENT_IP` | Laptop/client IPv4 address. |

Recommended startup order:

1. Power backend Pico.
2. Wait for solid onboard LED.
3. Power gateway Pico.
4. Wait for solid onboard LED.
5. Test from the laptop browser.

Backend direct access test:

```text
http://BACKEND_IP:8080/
http://BACKEND_IP:8080/status
http://BACKEND_IP:8080/api
http://BACKEND_IP:8080/discover
```

Expected result from the laptop:

```text
blocked
```

Gateway local tests:

```text
http://GATEWAY_IP/
http://GATEWAY_IP/metrics
```

Expected dashboard identity section:

```text
DEVICE=gateway-node;IP=GATEWAY_IP;PORT=80;MODE=proxy
```

Gateway proxy tests:

```text
http://GATEWAY_IP/backend
http://GATEWAY_IP/status
http://GATEWAY_IP/api
```

Expected `/status` shape:

```json
{"service":"lan-gateway-backend-pico","device":"backend-node","status":"ready","uptime_seconds":123}
```

Load test:

```text
http://GATEWAY_IP/test/start
```

Expected shape:

```text
requests=10
successes=10
failures=0
elapsed_ms=...
```

Check metrics after the load test:

```text
http://GATEWAY_IP/metrics
```

Expected counters to increase:

```text
allowed_requests
proxied_requests
load_test_requests
load_test_successes
```
