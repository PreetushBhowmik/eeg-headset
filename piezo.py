import RPi.GPIO as GPIO
import time

PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN, GPIO.OUT)

print("Starting test...")

try:
    while True:
        print("ON")
        GPIO.output(PIN, GPIO.LOW)   # 🔊 ON
        time.sleep(7)

        print("OFF")
        GPIO.output(PIN, GPIO.HIGH)  # ❌ OFF
        time.sleep(7)

except KeyboardInterrupt:
    print("Stopped")
    GPIO.output(PIN, GPIO.HIGH)  # ensure OFF
    GPIO.cleanup()
