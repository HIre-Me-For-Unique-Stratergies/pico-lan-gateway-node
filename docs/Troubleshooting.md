# Troubleshooting

<!--
Purpose: captures common hardware, firmware, setup, and network failures for
the single-Pico LAN Gateway Node.
-->

## `ImportError: no module named 'socket'`

The Pico is running normal MicroPython firmware instead of the W5500 EVB firmware.

Flash the Pico with:

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

## Browser Cannot Reach The Pico

Check:

- the Pico printed an IP address in Thonny
- the client device is on the same LAN or allowed VLAN
- router firewall rules are not blocking the Pico HTTP port
- the W5500 link light is active
- root `/main.py` and the `/gateway_pico/` folder were copied to the Pico

## Redirects To `/setup`

This is expected on first boot or after deleting `settings.py`.

Create the admin account at:

```text
http://PICO_IP/setup
```

## Login Fails

Check:

- the username is `admin` unless you changed it during setup
- the password is the one created on first launch
- the browser accepts cookies
- `settings.py` exists on the Pico root

If the password is lost, follow the reset process in `docs/Recovery.md`.

## Gateway Returns `blocked`

The path was denied by `gateway_pico/config.py`.

Check:

```python
RULES = [
    ("ANY", "/status", "allow"),
]
```

## Gateway Returns `rate_limited`

The client exceeded the configured request limit.

Check:

```python
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 30
```

Wait for the window to reset or raise the limit for testing.

## Gateway Returns `proxy_error`

The local in-process backend rejected or failed a request.

Check:

- `settings.py` exists
- setup completed successfully
- `gateway_pico/local_backend.py` was copied to the Pico
- `gateway_pico/auth.py` was copied to the Pico
