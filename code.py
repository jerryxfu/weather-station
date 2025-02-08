import time
import board
import digitalio

print("Hello, World!")

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

ledGP28 = digitalio.DigitalInOut(board.GP28)
ledGP28.direction = digitalio.Direction.OUTPUT

while True:
    led.value = True
    ledGP28.value = True
    time.sleep(0.50)
    led.value = False
    ledGP28.value = False
    time.sleep(0.50)
