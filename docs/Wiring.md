# Wiring Notes

<!--
Purpose: documents the physical wiring for both Pico devices so the hardware
can be rebuilt consistently without relying on memory or chat history.
-->

Both the gateway Pico and backend Pico use the same W5500 wiring.

| W5500 pin | Pico pin |
| --- | --- |
| VCC / 3.3V | 3V3(OUT) |
| GND | GND |
| SCK / SCLK | GP18 |
| MISO / SO / DOUT | GP16 |
| MOSI / SI / DIN | GP19 |
| CS / SS | GP17 |
| RST / RESET | GP20 |
| INT | Leave disconnected |
| NC | Leave disconnected |

Power notes:

- Use `3V3(OUT)` for the W5500 VCC pin.
- Use a Pico `GND` pin for W5500 ground.
- Do not power the W5500 from `VBUS`, `VSYS`, or `3V3_EN`.
- Do not power both W5500 modules from one Pico's `3V3(OUT)`.

Each Pico should power its own W5500 module.

Switch/router port:

```text
Speed: Auto
Duplex: Auto
```

If auto negotiation fails, use:

```text
100MF
```

The W5500 is a 10/100 Mbps Ethernet controller, not gigabit.
