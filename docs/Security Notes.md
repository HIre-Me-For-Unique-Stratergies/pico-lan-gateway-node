# Security Notes

<!--
Purpose: explains the security model honestly so the project is presented as
a LAN access-control demonstration, not as a production firewall.
-->

This version runs the gateway UI and protected backend data service on one Raspberry Pi Pico with a W5500 Ethernet module. Any device on the LAN can reach the login page; protected routes require the admin session cookie and a generated client token cookie.

What the firmware now protects:

- First launch requires setup of the admin password. The default username is `admin`.
- `settings.py` stores the admin username, password salt, repeated password hash, and hash round count.
- Session, client, and internal backend tokens are generated at runtime and are validated by hash.
- Reusable plaintext passwords and bearer tokens are not stored in `settings.py`.
- Passwords are submitted with `POST`, not URL query strings.
- Protected routes require login plus the generated client token.
- Sessions expire automatically after the configured timeout.
- Login and setup forms use a CSRF token.
- Repeated failed logins trigger a temporary per-client lockout.
- Requests are written to a rotating `audit.log` file.
- Boot-time config validation refuses unsafe settings.
- `/health` and `/export` provide diagnostics without exposing secrets.
- The current Pico IP address is shown in the dashboard and `/status` output.
- UDP discovery is disabled by default.
- Recent request logging and simple per-client rate limiting are enabled.
- `/admin` remains blocked.

Security limits that firmware cannot fully solve:

- HTTPS is not implemented directly on the Pico. Use a LAN TLS reverse proxy, VPN, or router that terminates HTTPS and forwards to the Pico over a trusted private segment.
- A standard Raspberry Pi Pico does not provide secure boot or flash encryption. Anyone with physical access can potentially replace firmware or read files from flash.
- Because the gateway and backend now run in one process, the shared backend token is an internal boundary marker, not a network isolation control.
- Router firewall rules and VLANs cannot be configured by Pico firmware. They must be configured on the router or managed switch.
- This is still an application-layer LAN service, not an inline firewall.

Recommended network hardening:

- Put the Pico on a trusted management VLAN or private LAN segment.
- If HTTPS is required, place a TLS reverse proxy in front of the Pico and restrict direct Pico access to that proxy. See `docs/HTTPS Deployment.md`.
- Use router firewall rules so only the proxy or trusted LAN segment can reach the Pico HTTP port.
- Disable or keep disabled UDP discovery except during setup.
- Keep the generated `settings.py` off source control and rotate it if copied from the device.

Physical access hardening:

- Use a locked enclosure and tamper-evident seals.
- Do not expose BOOTSEL, reset, SWD, USB data, or removable storage access in the final installation.
- Power the Pico from a controlled internal supply, not an exposed USB data cable.
- Treat physical compromise as credential compromise and recreate `settings.py` after any suspected tamper event. See `docs/Recovery.md`.

Good interview wording:

```text
This project implements a single-Pico LAN service with first-run admin setup, token-backed login, disabled discovery by default, request logging, and rate limiting. It can be placed behind a TLS reverse proxy for encrypted access. It is not production-secure against physical attackers because a standard Pico does not provide secure boot or flash encryption.
```
