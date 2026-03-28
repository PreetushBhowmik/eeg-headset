import RPi.GPIO as GPIO
import time

PIN = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.OUT)

while True:
    GPIO.output(PIN, GPIO.HIGH)
    print("Relay ON")
    time.sleep(5)

    GPIO.output(PIN, GPIO.LOW)
    print("Relay OFF")
    time.sleep(5)
