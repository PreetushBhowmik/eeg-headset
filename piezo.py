import RPi.GPIO as GPIO
import time

PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN, GPIO.OUT)

print("Testing piezo...")

# Turn ON
print("ON")
GPIO.output(PIN, GPIO.LOW)   # Try LOW first
time.sleep(3)

# Turn OFF
print("OFF")
GPIO.output(PIN, GPIO.HIGH)
time.sleep(2)

GPIO.cleanup()
