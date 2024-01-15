import OPi.GPIO as GPIO
import time
import orangepi.pc
from notification import NotificationSender
import firestoreDB
from deviceCredentials import get_username

class WaterSensorController:
    def __init__(self, sensor_pin = 15, relay_pin = 7):
        self.sensor_pin = sensor_pin
        self.relay_pin = relay_pin
        self.notification_sender = NotificationSender(firestoreDB.db)
        self.max_no_water_time = 300  # Maximum time without water (in seconds)
        self.no_water_timer = 0
        self.on = True
        
        GPIO.setmode(orangepi.pc.BOARD)
        # Set up the sensor pin as an input
        GPIO.setup(15, GPIO.IN)

        # Set up the relay pin as an output
        GPIO.setup(7, GPIO.OUT)

        
    def start_sensor(self):
        try:
            while True:
                
                if self.on:
                    # Read the digital output from the water sensor
                    water_detected = GPIO.input(self.sensor_pin)
                    print(water_detected)

                    if water_detected:
                        print("WATER: Water detected! Turning off the relay.")
                        # Reset the no water timer
                        self.no_water_timer = 0
                        # Turn off the relay
                        GPIO.output(self.relay_pin, GPIO.HIGH)
                    else:
                        print("WATER: No water detected. Turning on the relay.")
                        # Increment the no water timer
                        GPIO.output(self.relay_pin, GPIO.LOW)
                        self.no_water_timer += 1

                        # Check if the maximum no water time is reached
                        if self.no_water_timer >= self.max_no_water_time:
                            print(f"WATER: No water detected for {self.max_no_water_time} seconds. Stopping water sensor.")
                            # Send notification about no water detection
                            self.notification_sender.send_notification("No water detected. Water may be empty.",
                                                                        device_name=get_username())
                            break

                    # Wait for a short delay before reading again
                    time.sleep(1)
                elif not self.on:
                    self.no_water_timer = 0
        
        finally:
            GPIO.output(self.relay_pin, GPIO.HIGH)
            print("TURNED OFF")
            GPIO.cleanup()


if __name__ == "__main__":
    water_sensor = WaterSensorController()
    try:
        water_sensor.start_sensor()
    except KeyboardInterrupt:
        print("Script terminated by user.")
    finally:
        GPIO.cleanup()