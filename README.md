# Pico weather-station

- **code.py**: main code file
- **deploy.bat**: script to push code to Pico

[https://circuitpython.org/libraries](https://circuitpython.org/libraries)
[https://datasheets.raspberrypi.com/picow/pico-2-w-pinout.pdf](https://datasheets.raspberrypi.com/picow/pico-2-w-pinout.pdf)

```bash
pip install circuitpython-stubs
```

```bash
pip install -r requirements.txt
```

## STEMMA QT protocol

- **red**: Vcc (Voltage Common Collector)
- **black**: GND (Ground)
- **yellow**: SLC (Serial Clock Line)
- **blue**: SDA (Serial Data Line)

## I2C addresses

- **HTU31D**: `0x40` or `0x41` (if address selection jumper is shorted?)
- **TSL2591**: `0x29` AND `0x28`
- **BMP388**: `0x77` or `0x76` if address selection jumper is shorted
- **SGP30**: `0x58`

## Documentations

- [Adafruit HTU31D](https://www.adafruit.com/product/4832) => [Adafruit HTU21D-F](https://learn.adafruit.com/adafruit-htu21d-f-temperature-humidity-sensor)
- [Adafruit TSL2591](https://learn.adafruit.com/adafruit-tsl2591)
- [Adafruit BMP3xx](https://learn.adafruit.com/adafruit-bmp388-bmp390-bmp3xx)
- [Adafruit SGP30](https://learn.adafruit.com/adafruit-sgp30-gas-tvoc-eco2-mox-sensor/)

- [Adafruit 1.3" 128x64 OLED](https://learn.adafruit.com/monochrome-oled-breakouts)
- [Adafruit Monochrome OLED Breakouts](https://learn.adafruit.com/monochrome-oled-breakouts/circuitpython-wiring)

## RP2350 issue with internal pull-down resistors:

> The RP2350 microcontroller has a documented bug affecting its internal pull-down resistors. When a GPIO pin is configured as an input with an internal
> pull-down resistor enabled, the pin can exhibit latching behavior. Specifically, after the pin is driven high (e.g., by pressing a button that connects the
> pin to 3.3V) and then released, it may remain at an intermediate voltage (around 2.1–2.2V) instead of returning to a low state. This can cause the input to
> read as high even when the button is not pressed.
>
> Due to this issue, it's safer to configure digital inputs with pull-up resistors.
