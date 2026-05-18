DEVICE_NAME = "gateway-node"
MODE = "single-pico"

# The Pico listens on every network interface exposed by the W5500.
HTTP_HOST = "0.0.0.0"
HTTP_PORT = 80

# W5500 SPI wiring for the single Pico.
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
DISCOVERY_ENABLED = False

DEFAULT_ADMIN_USERNAME = "admin"
MIN_ADMIN_PASSWORD_LENGTH = 8
PASSWORD_HASH_ROUNDS = 1000
SESSION_TIMEOUT_SECONDS = 900
CLIENT_TIMEOUT_SECONDS = 5
MAX_REQUEST_BYTES = 2048
MAX_BODY_BYTES = 512
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 30
LOGIN_FAILURE_LIMIT = 5
LOGIN_FAILURE_WINDOW_SECONDS = 600
LOGIN_LOCKOUT_SECONDS = 600
AUDIT_LOG_FILE = "audit.log"
AUDIT_LOG_MAX_LINES = 100

DEFAULT_ACTION = "deny"

# Any LAN client can reach setup/login. Authenticated sessions can use the
# protected routes, so the gateway is not tied to one client IP address.
RULES = [
    ("ANY", "/", "allow"),
    ("ANY", "/favicon.ico", "allow"),
    ("ANY", "/setup", "allow"),
    ("ANY", "/login", "allow"),
    ("ANY", "/logout", "allow"),
    ("ANY", "/backend", "allow"),
    ("ANY", "/status", "allow"),
    ("ANY", "/api", "allow"),
    ("ANY", "/metrics", "allow"),
    ("ANY", "/health", "allow"),
    ("ANY", "/export", "allow"),
    ("ANY", "/test/start", "allow"),
    ("ANY", "/admin", "block"),
]
