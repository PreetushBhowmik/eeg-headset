import RPi.GPIO as GPIO
import time

PIN = 18   # change if using different pin

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN, GPIO.OUT)

# IMPORTANT: Start with relay OFF
GPIO.output(PIN, GPIO.LOW)

print("Starting relay + piezo test...")

try:
    while True:
        print("🔊 ON (Relay ON → Piezo ON)")
        GPIO.output(PIN, GPIO.HIGH)   # Relay ON
        time.sleep(5)

        print("❌ OFF (Relay OFF → Piezo OFF)")
        GPIO.output(PIN, GPIO.LOW)    # Relay OFF
        time.sleep(5)

except KeyboardInterrupt:
    print("Stopping test...")
    GPIO.output(PIN, GPIO.LOW)  # Ensure OFF
    GPIO.cleanup()
