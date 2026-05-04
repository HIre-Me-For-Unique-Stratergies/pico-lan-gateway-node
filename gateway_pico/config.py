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
# Replace BACKEND_IP with the backend Pico IP from Thonny or the router reservation.
BACKEND_HOST = "BACKEND_IP"
BACKEND_PORT = 8080
BACKEND_TIMEOUT_SECONDS = 5

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_SHA256 = "REPLACE_WITH_PASSWORD_SHA256"
ADMIN_SESSION_TOKEN = "REPLACE_WITH_RANDOM_SESSION_TOKEN"

DEFAULT_ACTION = "deny"

# For version 1, only this laptop can use the gateway endpoints.
# Replace LAPTOP_CLIENT_IP with the laptop/client IPv4 address.
RULES = [
    ("LAPTOP_CLIENT_IP", "/", "allow"),
    ("LAPTOP_CLIENT_IP", "/login", "allow"),
    ("LAPTOP_CLIENT_IP", "/logout", "allow"),
    ("LAPTOP_CLIENT_IP", "/backend", "allow"),
    ("LAPTOP_CLIENT_IP", "/status", "allow"),
    ("LAPTOP_CLIENT_IP", "/api", "allow"),
    ("LAPTOP_CLIENT_IP", "/metrics", "allow"),
    ("LAPTOP_CLIENT_IP", "/test/start", "allow"),
    ("ANY", "/admin", "block"),
]
