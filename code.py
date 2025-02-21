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
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.sparklepulse import SparklePulse

displayio.release_displays()

I2C0 = busio.I2C(scl=board.GP21, sda=board.GP20)
I2C1 = busio.I2C(scl=board.GP19, sda=board.GP18)

# Devices
onboardLed = digitalio.DigitalInOut(board.LED)
onboardLed.direction = digitalio.Direction.OUTPUT

button = digitalio.DigitalInOut(board.GP11)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP


def animate_once(animation):
    start = animation.cycle_count
    while not animation.cycle_count > start:
        animation.animate()


night_mode = False
# Neopixels are extremely bright, so we'll dim them (over 50% is hard to look at)
neopixel_max_brightness = 0.08
neopixel_night_brightness = 0.02
pixels = neopixel.NeoPixel(board.GP6, 24, brightness=neopixel_max_brightness, auto_write=False, pixel_order=neopixel.GRBW)
pixels.fill((0, 0, 0, 0))
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

display.root_group = displayio.Group()
display.root_group.append(label.Label(font=terminalio.FONT, text="Hello!", scale=2, color=0xFFFFFF, x=4, y=display.height // 2))
display.root_group.append(label.Label(font=terminalio.FONT, text="Starting...", scale=1, color=0xFFFFFF, x=4, y=8))

# led animations
pulse = Pulse(pixels, speed=1 / 255, color=(255, 255, 255, 255), period=1, max_intensity=1)
comet = Comet(pixels, speed=0.02, color=(64, 64, 64, 255), tail_length=18, ring=False, bounce=False)
sparkle_pulse = SparklePulse(pixels, speed=1 / 512, color=(255, 0, 255, 64), period=3, max_intensity=1)

animate_once(sparkle_pulse)
pixels.fill((0, 0, 0, 0))
pixels.show()


def convert_range(old_value, old_min, old_max, new_min, new_max):
    old_range = old_max - old_min
    new_range = new_max - new_min
    new_value = (((old_value - old_min) * new_range) / old_range) + new_min
    return max(min(new_value, new_max), new_min)


# Pages
page1 = displayio.Group()
page2 = displayio.Group()
page3 = displayio.Group()
# statsPage = displayio.Group()
current_page = 0
pages = [page1, page2, page3]
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
    28: "hot",
    26: "warm",
    23: "norm",
    22: "cool",
    20: "cold",
    1: "^HEAT^",
    -60: "FREEZE"
}


def get_temperature_rank(temperature):
    for threshold, text in sorted(temperature_ranks.items(), reverse=True):
        if temperature <= 0:
            return "FREEZE"
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

"""
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
"""


def value_to_color(value, min_range=0, max_range=100, color_stops=None):
    """
    Convert a value in [min_range, max_range] to a color on a gradient defined by color_stops.

    Parameters:
        value (float): The value to convert.
        min_range (float): The minimum value of the range.
        max_range (float): The maximum value of the range.
        color_stops (dict): A dictionary where keys are floats between 0 and 1
                            and values are (R, G, B, A/W) tuples (each 0-255).

    Returns:
        tuple: (R, G, B, 0) where R, G, B are integers in [0,255].
               The alpha/white channel is averaged between the two stops.
               If interpolation fails, returns (255, 255, 255, 0) (full white).
    """
    # Default color stops if none are provided:
    if color_stops is None:
        color_stops = {
            0.00: (255, 230, 204, 0),  # Pale tan
            0.33: (204, 229, 255, 0),  # Light blue
            0.66: (102, 178, 255, 0),  # Medium blue
            1.00: (0, 102, 204, 0)  # Deeper blue
        }

    # Clamp value to [min_range, max_range]
    value = max(min_range, min(max_range, value))

    # Normalize value to fraction f in [0, 1]
    f = (value - min_range) / float(max_range - min_range)

    # Sort the color stops by their normalized keys
    stops = sorted(color_stops.items())

    # Interpolate between the two stops that f falls between
    for i in range(len(stops) - 1):
        f_lower, c_lower = stops[i]
        f_upper, c_upper = stops[i + 1]

        if f_lower <= f <= f_upper:
            # Determine how far f is between f_lower and f_upper
            local_f = (f - f_lower) / (f_upper - f_lower)
            R = int(c_lower[0] + (c_upper[0] - c_lower[0]) * local_f)
            G = int(c_lower[1] + (c_upper[1] - c_lower[1]) * local_f)
            B = int(c_lower[2] + (c_upper[2] - c_lower[2]) * local_f)
            return (R, G, B, (c_lower[3] + c_upper[3]) / 2)

    # Fallback to full white if interpolation fails
    return (255, 255, 255, 0)


def update_temperature_bar(_temperature):
    color = value_to_color(_temperature, 0, 32, color_stops={
        0.00: (0, 0, 255, 0),  # Blue
        0.56: (75, 97, 209, 0),  # Savoy blue
        0.68: (0, 255, 0, 0),  # Green
        0.75: (0, 128, 128, 0),  # Teal
        0.84: (255, 165, 0, 0),  # Orange
        1.00: (255, 0, 0, 0)  # Red
    })

    # dimmed_color = tuple(int(convert_range(c, 0, 255, 48, 64)) for c in color)

    for i in range(12, 24):
        pixels[i] = (0, 0, 0, 16)

    for i in range(12, 12 + round(convert_range(_temperature, 18, 32, 0, 11))):
        pixels[i] = color


def update_humidity_bar(_humidity):
    color = value_to_color(_humidity, 15, 85, color_stops={
        0.00: (107, 81, 21, 0),  # Field drab
        0.38: (148, 108, 7, 0),  # Sand dune
        0.50: (0, 128, 128, 0),  # Teal
        0.62: (0, 128, 255, 0),  # Blue
        1.00: (128, 0, 128, 0)  # Purple
    })
    # dimmed_color = tuple(int(convert_range(c, 0, 255, 48, 64)) for c in color)

    for i in range(0, 11):
        pixels[i] = (0, 0, 0, 16)

    for i in range(11, 11 - round(convert_range(_humidity, 0, 100, 0, 12)), -1):
        pixels[i] = color


def update_tvoc_bar(_tvoc):
    color = value_to_color(_tvoc, 0, 1430, color_stops={
        0.00: (0, 255, 0, 0),  # Green
        0.50: (255, 165, 0, 0),  # Orange
        1.00: (255, 0, 0, 0)  # Red
    })

    # dimmed_color = tuple(int(convert_range(c, 0, 255, 48, 64)) for c in color)

    for i in range(12, 24):
        pixels[i] = (0, 0, 0, 16)

    for i in range(12, 12 + round(convert_range(_tvoc, -400, 2000, 0, 11))):
        pixels[i] = color


def update_eco2_bar(_eco2):
    color = value_to_color(_eco2, 400, 1400, color_stops={
        0.00: (0, 255, 0, 0),  # Green
        0.50: (255, 165, 0, 0),  # Orange
        1.00: (255, 0, 0, 0)  # Red
    })

    # dimmed_color = tuple(int(convert_range(c, 0, 255, 48, 64)) for c in color)

    for i in range(0, 11):
        pixels[i] = (0, 0, 0, 16)

    for i in range(11, 11 - round(convert_range(_eco2, -400, 4000, 0, 12)), -1):
        pixels[i] = color


def update_sensor_display(_page):
    # Update page 1
    if _page == 0:
        HTU31D_temperature = HTU31D.temperature
        HTU31D_humidity = HTU31D.relative_humidity
        SGP30_TVOC = SGP30.TVOC
        SGP30_eCO2 = SGP30.eCO2

        p1_temperature.text = f"T: {HTU31D_temperature:.1f}C"
        p1_humidity.text = f"H: {HTU31D_humidity:.1f}%"
        p1_pressure_label.text = f"P: {BMP388.pressure / 10:.1f}kPa"
        p1_TVOC_ppm.text = f"TVOC: {SGP30_TVOC / 1000}ppm"
        p1_eCO2.text = f"eCO2: {'low' if SGP30_eCO2 == 400 else str(SGP30_eCO2) + 'ppm'}"

        p1_temperature_rank.text = f"{get_temperature_rank(HTU31D_temperature)}"
        p1_humidity_rank.text = f"{get_humidity_rank(HTU31D_humidity)}"
        p1_lux.text = f"{TSL2591.lux:.0f}lux"
        p1_tvoc_rank.text = f"{get_tvoc_rank(SGP30_TVOC)}"
        p1_eCO2_rank.text = f"{get_eCO2_rank(SGP30_eCO2)}"

        for _lbl in p1_left_labels + p1_right_labels:
            if _lbl.text == "norm" or _lbl.text == "low":
                _lbl.text = ""

        for _lbl in p1_right_labels:
            _lbl.x = DISPLAY_WIDTH - _lbl.bounding_box[2]

        if night_mode:
            pixels.brightness = neopixel_night_brightness
        else:
            pixels.brightness = neopixel_max_brightness

        pixels.fill((0, 0, 0, 0))
        update_temperature_bar(HTU31D_temperature)
        update_humidity_bar(HTU31D_humidity)
        pixels.show()

    # Update page 2
    elif _page == 1:
        HTU31D_temperature = HTU31D.temperature
        HTU31D_humidity = HTU31D.relative_humidity

        p2_temperature.text = f"{HTU31D_temperature:.1f} C"
        p2_humidity.text = f"{HTU31D_humidity:.1f} %"
        p2_temp_title.text = f"Temp (C) [{get_temperature_rank(HTU31D_temperature)}]"
        p2_humidity_title.text = f"Humidity (RH) [{get_humidity_rank(HTU31D_humidity)}]"

        for _lbl in p2_right_labels:
            _lbl.x = DISPLAY_WIDTH - _lbl.bounding_box[2]

        if night_mode:
            pixels.brightness = neopixel_night_brightness
        else:
            pixels.brightness = neopixel_max_brightness

        pixels.fill((0, 0, 0, 0))
        update_temperature_bar(HTU31D_temperature)
        update_humidity_bar(HTU31D_humidity)
        pixels.show()

    # Update page 3
    elif _page == 2:
        SGP30_TVOC = SGP30.TVOC
        SGP30_eCO2 = SGP30.eCO2

        p3_tvoc_ppm.text = str(SGP30_TVOC)
        p3_eCO2.text = "low" if SGP30_eCO2 == 400 else str(SGP30_eCO2)
        p3_tvoc_title.text = f"TVOC (ppb) [{get_tvoc_rank(SGP30_TVOC)}]"
        p3_eCO2_title.text = f"eCO2 (ppm) [{get_eCO2_rank(SGP30_eCO2)}]"

        for _lbl in p3_right_labels:
            _lbl.x = DISPLAY_WIDTH - _lbl.bounding_box[2]

        if night_mode:
            pixels.brightness = neopixel_night_brightness
        else:
            pixels.brightness = neopixel_max_brightness

        pixels.fill((0, 0, 0, 0))
        update_tvoc_bar(SGP30_TVOC)
        update_eco2_bar(SGP30_eCO2)
        pixels.show()


"""
    # Update stats page
    elif _page == 3:
        stats_cpu_temp.text = f"CPU Temp: {microcontroller.cpu.temperature:.2f}C"
        stats_cpu_freq.text = f"CPU Freq: {microcontroller.cpu.frequency / 1_000_000:.2f}MHz"
        # stats_cpu_voltage.text = f"CPU Volt: {microcontroller.cpu.voltage:.2f}V" # not available on Pico 2 W
        stats_usb.text = f"usb?: {supervisor.runtime.usb_connected}"
        stats_serial.text = f"serial?: {supervisor.runtime.serial_connected}"

        for _lbl in stats_right_labels:
            _lbl.x = DISPLAY_WIDTH - _lbl.bounding_box[2]
"""

update_sensor_display(0)

time_now = time.monotonic()
prev_button_state = button.value
button_press_time = None

update_interval = sensor_update_interval = 1  # seconds
sensor_update_interval_night = 10  # seconds
sparkle_pulse.period = sensor_update_interval
prev_sensor_update = time_now

# Main loop
while True:
    current_time = time.monotonic()
    current_button_state = button.value

    if prev_button_state and not current_button_state:
        # Button was pressed
        button_press_time = current_time
        onboardLed.value = True
        comet.ring = False
        animate_once(comet)
        comet.ring = True
        current_page = current_page + 1 if current_page < 2 else 0
        display.root_group = pages[current_page]
    elif not prev_button_state and current_button_state:
        # Button was released
        onboardLed.value = False
        button_press_time = None

    prev_button_state = current_button_state

    # Check to update sensors
    if current_time - prev_sensor_update >= update_interval:
        if TSL2591.lux <= 1 and not night_mode:
            night_mode = True
            update_interval = sensor_update_interval_night
            p1_subtitle.text = "Night | <3"
            p1_subtitle.x = DISPLAY_WIDTH - p1_subtitle.bounding_box[2]
        else:
            night_mode = False
            update_interval = sensor_update_interval
            p1_subtitle.text = "<3"
            p1_subtitle.x = DISPLAY_WIDTH - p1_subtitle.bounding_box[2]

        if night_mode:
            update_sensor_display(current_page)
        else:
            update_sensor_display(current_page)
        prev_sensor_update = current_time
