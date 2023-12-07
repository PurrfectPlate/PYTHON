import OPi.GPIO as GPIO
import time
import orangepi.one


# Set GPIO mode
GPIO.setmode(orangepi.one.BOARD)

# Define GPIO pins
sensor_pin = 15  # GPIO pin for the water sensor
relay_pin = 7   # GPIO pin for the relay (adjust to the actual pin you connected)

# Set up the sensor pin as an input
GPIO.setup(sensor_pin, GPIO.IN)

# Set up the relay pin as an output
GPIO.setup(relay_pin, GPIO.OUT)

try:
    while True:
        # Read the digital output from the water sensor
        water_detected = GPIO.input(sensor_pin)

        if water_detected:
            print("Water detected! Turning off the relay.")
            # Turn on the relay
            GPIO.output(relay_pin, GPIO.HIGH)  # Low-level triggers the relay
        else:
            print("No water detected. Turning on the relay.")
            # Turn off the relay
            GPIO.output(relay_pin, GPIO.LOW)

        # Wait for a short delay before reading again
        time.sleep(1)

except KeyboardInterrupt:
    # Clean up GPIO on keyboard interrupt
    GPIO.cleanup()
