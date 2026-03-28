from gpiozero import OutputDevice
from time import sleep

# Define the relay on GPIO 18
# Note: If your relay triggers when the pin is LOW, set active_high=False
relay = OutputDevice(18, active_high=True, initial_value=False)

print("Starting Humidifier Loop. Press Ctrl+C to stop.")

try:
    while True:
        print("Humidifier ON")
        relay.on()   # Closes the COM and NO contacts
        sleep(10)    # Run for 10 seconds
        
        print("Humidifier OFF")
        relay.off()  # Opens the circuit
        sleep(5)     # Wait for 5 seconds
        
except KeyboardInterrupt:
    print("\nLoop stopped by user.")
    relay.off()
