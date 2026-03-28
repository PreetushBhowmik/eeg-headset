import RPi.GPIO as GPIO
import time

PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN, GPIO.OUT)

# VERY IMPORTANT: Start OFF
GPIO.output(PIN, GPIO.HIGH)

print("Starting test...")

try:
    while True:
        print("FORCE ON")
        GPIO.output(PIN, GPIO.LOW)   # 🔊 FORCE ON
        time.sleep(7)

        print("FORCE OFF")
        GPIO.output(PIN, GPIO.HIGH)  # ❌ OFF
        time.sleep(7)

except KeyboardInterrupt:
    print("Stopping...")
    GPIO.output(PIN, GPIO.HIGH)  # ensure OFF
    GPIO.cleanup()
