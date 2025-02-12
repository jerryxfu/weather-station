import math
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
import microcontroller
import neopixel
import supervisor
import terminalio
from adafruit_display_text import label

displayio.release_displays()

I2C0 = busio.I2C(scl=board.GP5, sda=board.GP4)
I2C1 = busio.I2C(scl=board.GP27, sda=board.GP26)

# Devices
onboardLed = digitalio.DigitalInOut(board.LED)
onboardLed.direction = digitalio.Direction.OUTPUT

button = digitalio.DigitalInOut(board.GP17)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# Neopixels are extremely bright, so we'll dim them (over 50% is hard to look at)
pixels = neopixel.NeoPixel(board.GP28, 24, brightness=0.03, auto_write=False, pixel_order=neopixel.GRBW)
pixels.fill((0, 0, 0, 0))
pixels.show()
pixels.fill((255, 0, 0, 127))
pixels.show()

# Sensors
TSL2591 = adafruit_tsl2591.TSL2591(I2C0, address=0x29)
SGP30 = adafruit_sgp30.Adafruit_SGP30(I2C0, address=0x58)
HTU31D = adafruit_htu31d.HTU31D(I2C0, address=0x40)
BMP388 = adafruit_bmp3xx.BMP3XX_I2C(I2C0, address=0x77)

# Display setup
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
display_bus = displayio.I2CDisplay(I2C1, device_address=0x3D)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, rotation=0, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT)

# Pages
page1 = displayio.Group()
page2 = displayio.Group()
page3 = displayio.Group()
statsPage = displayio.Group()
current_page = 0
pages = [page1, page2, page3, statsPage]
display.root_group = pages[current_page]  # default page

eCO2_ranks = {
    30000: "EVAC",
    1600: "CRIT",
    1400: "BAD",
    1200: "VENT",
    1000: "HIGH",
    800: "fair",
    400: "norm"
}


def get_eCO2_rank(eCO2_val):
    for threshold, text in sorted(eCO2_ranks.items(), reverse=True):
        if eCO2_val <= 400:
            return "low"
        if eCO2_val >= threshold:
            return text
    return "n/a"


tvoc_ppb_ranks = {
    5500: "EVAC",
    2200: "CRIT",
    1430: "BAD",
    660: "VENT",
    430: "HIGH",
    220: "fair"
}


def get_tvoc_rank(tvoc_val):
    for threshold, text in sorted(tvoc_ppb_ranks.items(), reverse=True):
        if tvoc_val <= 220:
            return "low"
        elif tvoc_val >= threshold:
            return text
    return "n/a"


temperature_ranks = {
    30: "hot",
    25: "warm",
    22: "norm",
    20: "cool",
    19: "cold",
    0: "HEAT"
}


def get_temperature_rank(temperature):
    for threshold, text in sorted(temperature_ranks.items(), reverse=True):
        if temperature <= 0:
            return "freezing"
        if temperature >= threshold:
            return text
    return "n/a"


humidity_ranks = {
    90: "wet",
    80: "moist",
    60: "humid",
    40: "norm",
    20: "dry",
    0: "DESERT"
}


def get_humidity_rank(humidity):
    for threshold, text in sorted(humidity_ranks.items(), reverse=True):
        if humidity <= 0:
            return "dry"
        if humidity >= threshold:
            return text
    return "n/a"


# Page 1
p1_title = label.Label(font=terminalio.FONT, text="Hello!", color=0xFFFFFF, x=0, y=4)
p1_temperature = label.Label(font=terminalio.FONT, text="{temp}", color=0xFFFFFF, x=0, y=14)
p1_humidity = label.Label(font=terminalio.FONT, text="{humidity}", color=0xFFFFFF, x=0, y=24 + 1)
p1_pressure_label = label.Label(font=terminalio.FONT, text="{pressure}", color=0xFFFFFF, x=0, y=34 + 2)
p1_TVOC_ppm = label.Label(font=terminalio.FONT, text="{TVOC}", color=0xFFFFFF, x=0, y=44 + 3)
p1_eCO2 = label.Label(font=terminalio.FONT, text="{eCO2}", color=0xFFFFFF, x=0, y=54 + 5)

p1_left_labels = [p1_title, p1_temperature, p1_humidity, p1_pressure_label, p1_TVOC_ppm, p1_eCO2]

p1_subtitle = label.Label(font=terminalio.FONT, text="<3", color=0xFFFFFF, x=0, y=4)
p1_temperature_rank = label.Label(font=terminalio.FONT, text="{temp_rank}", color=0xFFFFFF, x=0, y=14)
p1_humidity_rank = label.Label(font=terminalio.FONT, text="{humidity_rank}", color=0xFFFFFF, x=0, y=24)
p1_lux = label.Label(font=terminalio.FONT, text="{lux}", color=0xFFFFFF, x=0, y=34)
p1_tvoc_rank = label.Label(font=terminalio.FONT, text="{tvoc_rank}", color=0xFFFFFF, x=0, y=44)
p1_eCO2_rank = label.Label(font=terminalio.FONT, text="{eco2_rank}", color=0xFFFFFF, x=0, y=54)

p1_right_labels = [p1_subtitle, p1_lux, p1_temperature_rank, p1_humidity_rank, p1_tvoc_rank, p1_eCO2_rank]

for lbl in p1_right_labels:
    lbl.x = DISPLAY_WIDTH - lbl.bounding_box[2]

for lbl in p1_left_labels + p1_right_labels:
    page1.append(lbl)

# Page 2
p2_temp_title = label.Label(font=terminalio.FONT, scale=1, text="Temp (C)", color=0xFFFFFF, x=0, y=4)
p2_temperature = label.Label(font=terminalio.FONT, scale=2, text="{temp}", color=0xFFFFFF, x=0, y=4 + 16)
p2_humidity_title = label.Label(font=terminalio.FONT, scale=1, text="Humidity (RH)", color=0xFFFFFF, x=0, y=56 - 16)
p2_humidity = label.Label(font=terminalio.FONT, scale=2, text="{humidity}", color=0xFFFFFF, x=0, y=56)

p2_left_labels = [p2_temp_title, p2_temperature, p2_humidity_title, p2_humidity]

p2_right_labels = []

for lbl in p2_right_labels:
    lbl.x = DISPLAY_WIDTH - lbl.bounding_box[2]

for lbl in p2_left_labels + p2_right_labels:
    page2.append(lbl)

# Page 3
p3_tvoc_title = label.Label(font=terminalio.FONT, scale=1, text="TVOC (ppb) []", color=0xFFFFFF, x=0, y=4)
p3_tvoc_ppm = label.Label(font=terminalio.FONT, scale=2, text="{TVOC}", color=0xFFFFFF, x=0, y=4 + 16)
p3_eCO2_title = label.Label(font=terminalio.FONT, scale=1, text="eCO2 (ppm) []", color=0xFFFFFF, x=0, y=56 - 16)
p3_eCO2 = label.Label(font=terminalio.FONT, scale=2, text="{eCO2}", color=0xFFFFFF, x=0, y=56)

p3_left_labels = [p3_tvoc_title, p3_tvoc_ppm, p3_eCO2_title, p3_eCO2]

p3_right_labels = []

for lbl in p3_right_labels:
    lbl.x = DISPLAY_WIDTH - lbl.bounding_box[2]

for lbl in p3_left_labels + p3_right_labels:
    page3.append(lbl)

# Stats Page
stats_title = label.Label(font=terminalio.FONT, text="Raspberry Pi Pico 2 W", color=0xFFFFFF, x=0, y=4)
stats_cpu_temp = label.Label(font=terminalio.FONT, text="{cpu_temp}", color=0xFFFFFF, x=0, y=14)
stats_cpu_freq = label.Label(font=terminalio.FONT, text="{cpu_freq}", color=0xFFFFFF, x=0, y=24)
# stats_cpu_voltage = label.Label(font=terminalio.FONT, text="{cpu_voltage}", color=0xFFFFFF, x=0, y=34) # not available on Pico 2 W
stats_usb = label.Label(font=terminalio.FONT, text="{usb_connected}", color=0xFFFFFF, x=0, y=34)
stats_serial = label.Label(font=terminalio.FONT, text="{serial_connected}", color=0xFFFFFF, x=0, y=44)

stats_left_labels = [stats_title, stats_cpu_temp, stats_cpu_freq, stats_usb, stats_serial]

stats_right_labels = []

for lbl in stats_right_labels:
    lbl.x = DISPLAY_WIDTH - lbl.bounding_box[2]

for lbl in stats_left_labels + stats_right_labels:
    statsPage.append(lbl)

time.sleep(1.5)

# Breathing parameters
angle = 0
angle_increment = 5  # degrees per iteration
breathing_update_interval = 0.05  # seconds

sensor_update_interval = 2.0  # seconds
last_sensor_update = time.monotonic()

# Main loop
while True:
    if not button.value:
        onboardLed.value = True
        current_page = current_page + 1 if current_page < 3 else 0
        display.root_group = pages[current_page]
    else:
        onboardLed.value = False

    # Check if it's time to update sensor readings (once per second)
    current_time = time.monotonic()
    if current_time - last_sensor_update >= sensor_update_interval:
        # Update page 1
        if current_page == 0:
            HTU31D_temperature = HTU31D.temperature
            HTU31D_humidity = HTU31D.relative_humidity
            SGP30_TVOC = SGP30.TVOC
            SGP30_eCO2 = SGP30.eCO2

            p1_temperature.text = f"T: {HTU31D_temperature:.1f}C"
            p1_humidity.text = f"H: {HTU31D_humidity:.1f}%"
            p1_pressure_label.text = f"P: {BMP388.pressure / 10:.1f}kPa"
            p1_TVOC_ppm.text = f"TVOC: {SGP30_TVOC / 1000}{(' (' + get_tvoc_rank(SGP30_TVOC) + ')') if SGP30_TVOC >= 219 else ''}"
            p1_eCO2.text = f"eCO2: {'low' if SGP30_eCO2 == 400 else str(SGP30_eCO2) + ((' (' + get_eCO2_rank(SGP30_eCO2) + ')') if SGP30_eCO2 >= 799 else '')}"

            p1_temperature_rank.text = f"{get_temperature_rank(HTU31D_temperature)}"
            p1_humidity_rank.text = f"{get_humidity_rank(HTU31D_humidity)}"
            p1_lux.text = f"{TSL2591.lux:.0f}lux"
            p1_tvoc_rank.text = f"{get_tvoc_rank(SGP30_TVOC)}"
            p1_eCO2_rank.text = f"{get_eCO2_rank(SGP30_eCO2)}"

            for lbl in p1_left_labels + p1_right_labels:
                if lbl.text == "norm" or lbl.text == "low":
                    lbl.text = ""

            for lbl in p1_right_labels:
                lbl.x = DISPLAY_WIDTH - lbl.bounding_box[2]

        # Update page 2
        elif current_page == 1:
            HTU31D_temperature = HTU31D.temperature
            HTU31D_humidity = HTU31D.relative_humidity

            p2_temperature.text = f"{HTU31D_temperature:.1f} C"
            p2_humidity.text = f"{HTU31D_humidity:.1f} %"
            p2_temp_title.text = f"Temp (C) [{get_temperature_rank(HTU31D_temperature)}]"
            p2_humidity_title.text = f"Humidity (RH) [{get_humidity_rank(HTU31D_humidity)}]"

            for lbl in p2_right_labels:
                lbl.x = DISPLAY_WIDTH - lbl.bounding_box[2]

        # Update page 3
        elif current_page == 2:
            SGP30_TVOC = SGP30.TVOC
            SGP30_eCO2 = SGP30.eCO2

            p3_tvoc_ppm.text = str(SGP30_TVOC)
            p3_eCO2.text = "low" if SGP30_eCO2 == 400 else str(SGP30_eCO2)
            p3_tvoc_title.text = f"TVOC (ppb) [{get_tvoc_rank(SGP30_TVOC)}]"
            p3_eCO2_title.text = f"eCO2 (ppm) [{get_eCO2_rank(SGP30_eCO2)}]"

            for lbl in p3_right_labels:
                lbl.x = DISPLAY_WIDTH - lbl.bounding_box[2]

        # Update stats page
        elif current_page == 3:
            stats_cpu_temp.text = f"CPU Temp: {microcontroller.cpu.temperature:.2f}C"
            stats_cpu_freq.text = f"CPU Freq: {microcontroller.cpu.frequency / 1_000_000:.2f}MHz"
            # stats_cpu_voltage.text = f"CPU Volt: {microcontroller.cpu.voltage:.2f}V" # not available on Pico 2 W
            stats_usb.text = f"usb?: {supervisor.runtime.usb_connected}"
            stats_serial.text = f"serial?: {supervisor.runtime.serial_connected}"

            for lbl in stats_right_labels:
                lbl.x = DISPLAY_WIDTH - lbl.bounding_box[2]

        last_sensor_update = current_time

    # Compute brightness factor from 0.0 to 1.0 using a sine wave.
    factor = (math.sin(math.radians(angle)) + 1) / 2
    print(factor)
    pixels.brightness = factor
    pixels.fill((0, 0, 0, 127))
    pixels.show()
    angle = (angle + angle_increment) % 360

    time.sleep(0.1)
