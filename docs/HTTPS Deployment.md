# HTTPS Deployment

The Pico firmware serves plain HTTP. That is intentional for this hardware target: a Raspberry Pi Pico with W5500 is not a good place to terminate production TLS.

Use one of these patterns when encrypted access is required:

```text
Browser -> HTTPS reverse proxy / VPN / router TLS endpoint -> Pico HTTP
```

## Option 1: Caddy Reverse Proxy

Run Caddy on a trusted LAN machine, small server, or router that supports it.

Example Caddyfile:

```text
gateway.example.local {
    reverse_proxy http://PICO_IP
}
```

Then restrict direct Pico access in the router so normal clients can only reach the proxy.

## Option 2: Nginx Reverse Proxy

Example server block:

```nginx
server {
    listen 443 ssl;
    server_name gateway.example.local;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://PICO_IP;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

## Option 3: VPN

Put the Pico on a private LAN segment and require clients to connect through a VPN before opening the dashboard.

## Router Rules

For the strongest LAN demo:

- reserve a stable DHCP IP for the Pico
- allow the reverse proxy to reach `PICO_IP:80`
- block other clients from reaching `PICO_IP:80` directly
- keep UDP discovery disabled unless actively testing discovery

This gives encrypted browser access without overstating what the Pico firmware itself can provide.
