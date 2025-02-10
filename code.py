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

displayio.release_displays()

I2C0 = busio.I2C(scl=board.GP5, sda=board.GP4)
I2C1 = busio.I2C(scl=board.GP27, sda=board.GP26)

# Initialize devices
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

button = digitalio.DigitalInOut(board.GP17)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

TSL2591 = adafruit_tsl2591.TSL2591(I2C0, address=0x29)
SGP30 = adafruit_sgp30.Adafruit_SGP30(I2C0, address=0x58)
HTU31D = adafruit_htu31d.HTU31D(I2C0, address=0x40)
BMP388 = adafruit_bmp3xx.BMP3XX_I2C(I2C0, address=0x77)

# Display setup
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
display_bus = displayio.I2CDisplay(I2C1, device_address=0x3D)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, rotation=0, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT)
# display = adafruit_displayio_ssd1306.SSD1306(display_bus, rotation=90, width=DISPLAY_HEIGHT, height=DISPLAY_WIDTH)

# Create a display group
page1 = displayio.Group()
page2 = displayio.Group()
page3 = displayio.Group()
current_page = 1
pages = [page1, page2, page3]
display.root_group = pages[current_page]  # default page

eCO2_levels = {
    30000: "EVAC",
    1600: "CRIT",
    1400: "BAD",
    1200: "VENT",
    1000: "HIGH",
    800: "fair"
}
tvoc_ppm_levels = {
    5.5: "EVAC",
    2.2: "CRIT",
    1.43: "BAD",
    0.66: "VENT",
    0.43: "HIGH",
    0.22: "fair"
}
tvoc_ppb_levels = {
    5500: "EVAC",
    2200: "CRIT",
    1430: "BAD",
    660: "VENT",
    430: "HIGH",
    220: "fair"
}


def get_eCO2_text(eCO2_val):
    for threshold, text in sorted(eCO2_levels.items(), reverse=True):
        if eCO2_val == 400:
            return "low"
        if eCO2_val >= threshold:
            return f"{eCO2_val}ppm ({text})"
    return f"{eCO2_val}ppm"


def get_tvoc_text(tvoc_val):
    for threshold, text in sorted(tvoc_ppm_levels.items(), reverse=True):
        if tvoc_val >= threshold:
            return f"{tvoc_val}ppm ({text})"
    return f"{tvoc_val}ppm"


"""
    Page 1
"""
# Create LEFT aligned labels
p1_title_label = label.Label(font=terminalio.FONT, text="Hello!", color=0xFFFFFF, x=0, y=5)
p1_temperature_label = label.Label(font=terminalio.FONT, text="[Temp]", color=0xFFFFFF, x=0, y=15 + 3)
p1_humidity_label = label.Label(font=terminalio.FONT, text="[Humidity]", color=0xFFFFFF, x=0, y=25 + 3)
p1_lux_label = label.Label(font=terminalio.FONT, text="[Light]", color=0xFFFFFF, x=0, y=35 + 3)
p1_tvoc_ppm_label = label.Label(font=terminalio.FONT, text="[TVOC]", color=0xFFFFFF, x=0, y=45 + 3)
p1_eCO2_label = label.Label(font=terminalio.FONT, text="[eCO2]", color=0xFFFFFF, x=0, y=55 + 3)

p1_left_labels = [
    p1_title_label,
    p1_humidity_label,
    p1_temperature_label,
    p1_lux_label,
    p1_tvoc_ppm_label,
    p1_eCO2_label
]

# Create RIGHT aligned labels
p1_subtitle_label = label.Label(font=terminalio.FONT, text="<3", color=0xFFFFFF, x=0, y=5)
p1_pressure_label = label.Label(font=terminalio.FONT, text="[Pressure]", color=0xFFFFFF, x=0, y=15 + 3)

p1_right_labels = [
    p1_subtitle_label,
    p1_pressure_label
]

for l in p1_right_labels:
    l.x = DISPLAY_WIDTH - l.bounding_box[2]

# Append labels to the display group
for label in p1_left_labels + p1_right_labels:
    page1.append(label)

"""
    Page 2
"""
p2_title_label = label.Label(font=terminalio.FONT, text="Hello!", color=0xFFFFFF, x=0, y=5)
p2_temperature1_label = label.Label(font=terminalio.FONT, text="[Temp1]", color=0xFFFFFF, x=0, y=15 + 3)
p2_temperature2_label = label.Label(font=terminalio.FONT, text="[Temp2]", color=0xFFFFFF, x=0, y=25 + 3)
p2_humidity_label = label.Label(font=terminalio.FONT, text="[Humidity]", color=0xFFFFFF, x=0, y=35 + 3)

p2_left_labels = [
    p2_title_label,
    p2_temperature1_label,
    p2_temperature2_label,
    p2_humidity_label
]

for label in p2_left_labels:
    page2.append(label)

time.sleep(3)

# Main loop
while True:
    # Update sensor readings
    HTU31D_temperature, HTU31D_humidity = HTU31D.measurements
    BMP388_pressure = BMP388.pressure
    BMP388_temperature = BMP388.temperature
    BMP388_altitude = BMP388.altitude
    TSL2591_lux = TSL2591.lux
    TSL2591_full = TSL2591.full_spectrum
    TSL2591_visible = TSL2591.visible
    TSL2591_ir = TSL2591.infrared
    SGP30_TVOC = SGP30.TVOC
    SGP30_eCO2 = SGP30.eCO2
    SGP30_H2 = SGP30.H2
    SGP30_ethanol = SGP30.Ethanol

    print("temp", HTU31D.temperature)
    print("humidity", HTU31D.relative_humidity)
    print("pressure", BMP388.pressure)
    print("---")
    print("lux", TSL2591.lux)
    print("infra", TSL2591.infrared)
    print("visible", TSL2591.visible)
    print("full", TSL2591.full_spectrum)
    print("---")
    print("tvoc", SGP30.TVOC)
    print("eco2", SGP30.eCO2)
    print("h2", SGP30.H2)
    print("eth", SGP30.Ethanol)
    print("----------------")

    """
        Page 1
    """
    # Update page 1
    p1_temperature_label.text = f"T: {HTU31D_temperature:.1f}C"
    p1_humidity_label.text = f"H: {HTU31D_humidity:.1f}%"
    p1_lux_label.text = f"Lt: {TSL2591_lux:.0f}lux"
    p1_tvoc_ppm_label.text = f"TVOC: {get_tvoc_text(SGP30_TVOC / 1000)}"
    p1_eCO2_label.text = f"eCO2: {get_eCO2_text(SGP30_eCO2)}"

    p1_pressure_label.text = f"P: {BMP388_pressure / 10:.1f}kPa"

    for l in p1_right_labels:
        l.x = DISPLAY_WIDTH - l.bounding_box[2]

    """
        Page 2
    """
    p2_temperature1_label.text = f"T1: {HTU31D_temperature:.1f}C"
    p2_temperature2_label.text = f"T2: {BMP388_temperature:.1f}C"
    p2_humidity_label.text = f"H: {HTU31D_humidity:.1f}%"

    if not button.value:
        led.value = True
        current_page = current_page + 1 if current_page < 2 else 0
        display.root_group = pages[current_page]
    else:
        led.value = False

    time.sleep(1)
