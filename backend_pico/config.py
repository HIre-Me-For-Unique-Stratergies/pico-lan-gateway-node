DEVICE_NAME = "backend-node"

# The backend Pico listens on every network interface exposed by the W5500.
HTTP_HOST = "0.0.0.0"
HTTP_PORT = 8080
CLIENT_TIMEOUT_SECONDS = 5

# Replace with the gateway Pico IP printed by Thonny or reserved in your router.
ALLOWED_GATEWAY_IP = "GATEWAY_IP"

# W5500 SPI wiring. Keep this the same on the gateway and backend Picos.
SPI_ID = 0
SPI_BAUDRATE = 2_000_000
SPI_SCK_PIN = 18
SPI_MOSI_PIN = 19
SPI_MISO_PIN = 16
W5500_CS_PIN = 17
W5500_RST_PIN = 20
