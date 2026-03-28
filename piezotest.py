from gpiozero import OutputDevice
from time import sleep

# Use GPIO 18
piezo_relay = OutputDevice(18, active_high=True, initial_value=False)

print("Turning on Humidifier...")
piezo_relay.on()
sleep(5)
print("Turning off...")
piezo_relay.off()
