# Security Notes

<!--
Purpose: explains the security model honestly so the project is presented as
a LAN access-control demonstration, not as a production firewall.
-->

This project is secure enough for a controlled LAN demo, but it is not a hardened production security system.

What the project protects:

- The backend Pico blocks direct laptop access.
- The backend Pico only accepts requests from `GATEWAY_IP`.
- The gateway Pico only allows configured client IPs.
- The gateway blocks `/admin`.
- Normal backend use must go through the gateway path.

Main limitations:

- HTTP is not encrypted.
- There is no password, token, login, or certificate.
- IP-based trust can be bypassed on some networks.
- Anyone with physical access to the Picos can replace or read files.
- UDP discovery broadcasts gateway details on the LAN.
- The system is not an inline firewall and cannot control unrelated LAN traffic.

Good interview wording:

```text
This project implements lightweight application-layer access control on a trusted LAN. It demonstrates gateway policy enforcement and backend isolation, but it is not production-secure because it does not include encryption, authentication, or tamper resistance.
```

Recommended future upgrades:

- Add a shared token between gateway and backend.
- Add a client token required by the gateway.
- Restrict or disable UDP discovery.
- Add router firewall rules so only the gateway can reach the backend port.
- Put the backend on a separate VLAN or private subnet.
- Add request logging and rate limiting.
