DEVICE_NAME = "gateway-node"

# The Pico listens on every network interface exposed by the W5500.
HTTP_HOST = "0.0.0.0"
HTTP_PORT = 80

# W5500 SPI wiring. Keep this the same on the gateway and backend Picos.
SPI_ID = 0
SPI_BAUDRATE = 2_000_000
SPI_SCK_PIN = 18
SPI_MOSI_PIN = 19
SPI_MISO_PIN = 16
W5500_CS_PIN = 17
W5500_RST_PIN = 20

DISCOVERY_BROADCAST_IP = "255.255.255.255"
DISCOVERY_PORT = 4210
DISCOVERY_INTERVAL_SECONDS = 5

# Backend server running on the second Pico.
BACKEND_HOST = "192.168.1.107"
BACKEND_PORT = 8080
BACKEND_TIMEOUT_SECONDS = 5

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_SHA256 = "a628029282efd81939d6452acee171fe485dd23762e96aaf7f6b08f59df255e8"
ADMIN_SESSION_TOKEN = "ad98cef19006d62d91fc6888"

DEFAULT_ACTION = "deny"

# For version 1, only this laptop can use the gateway endpoints.
RULES = [
    ("192.168.1.100", "/", "allow"),
    ("192.168.1.100", "/login", "allow"),
    ("192.168.1.100", "/logout", "allow"),
    ("192.168.1.100", "/backend", "allow"),
    ("192.168.1.100", "/status", "allow"),
    ("192.168.1.100", "/api", "allow"),
    ("192.168.1.100", "/metrics", "allow"),
    ("192.168.1.100", "/discover", "allow"),
    ("192.168.1.100", "/test/start", "allow"),
    ("ANY", "/admin", "block"),
]

