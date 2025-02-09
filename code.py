import time

import adafruit_bmp3xx
import adafruit_displayio_ssd1306
import adafruit_htu31d
import adafruit_sgp30
import adafruit_tsl2591
import board
import busio
import digitalio
import displayio
import terminalio
from adafruit_display_text import label

# Initialize devices
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

button = digitalio.DigitalInOut(board.GP22)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

I2C = busio.I2C(board.SCL, board.SDA)

HTU31d = adafruit_htu31d.HTU31D(I2C, address=0x40)
TSL2591 = adafruit_tsl2591.TSL2591(I2C, address=0x29)
BMP388 = adafruit_bmp3xx.BMP3XX_I2C(I2C, address=0x77)
SGP30 = adafruit_sgp30.Adafruit_SGP30(I2C, address=0x58)

# Display setup
displayio.release_displays()
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
display_bus = displayio.I2CDisplay(I2C, device_address=0x3D)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT)

# Create a display group
splash = displayio.Group()
display.show(splash)

# Create a text label
hello_text = label.Label(terminalio.FONT, text="Hello", color=0xFFFFFF, x=10, y=DISPLAY_HEIGHT // 2)
splash.append(hello_text)

while True:
    if not button.value:
        led.value = True
    else:
        led.value = False

    time.sleep(0.10)
