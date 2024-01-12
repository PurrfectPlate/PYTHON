import OPi.GPIO as GPIO
import time
import orangepi.pc
import math
import firestoreDB
from deviceCredentials import get_username

class HCSR04:
    def __init__(self, trigger_pin, echo_pin):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.temperature = 20
        self.failed_pulse_counter = 0

        # Set GPIO mode and setup pins
        GPIO.setmode(orangepi.pc.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)

    def raw_distance(self, sample_size=11, sample_wait=0.1):
        """Return an error corrected unrounded distance, in cm, of an object
        adjusted for temperature in Celcius.  The distance calculated
        is the median value of a sample of `sample_size` readings.


        Speed of readings is a result of two variables.  The sample_size
        per reading and the sample_wait (interval between individual samples).

        Example: To use a sample size of 5 instead of 11 will increase the
        speed of your reading but could increase variance in readings;

        value = sensor.Measurement(trig_pin, echo_pin)
        r = value.raw_distance(sample_size=5)

        Adjusting the interval between individual samples can also
        increase the speed of the reading.  Increasing the speed will also
        increase CPU usage.  Setting it too low will cause errors.  A default
        of sample_wait=0.1 is a good balance between speed and minimizing
        CPU usage.  It is also a safe setting that should not cause errors.

        e.g.

        r = value.raw_distance(sample_wait=0.03)
        """

        speed_of_sound = 331.3 * math.sqrt(1 + (self.temperature / 273.15))
        sample = []
        # setup input/output pins

        while len(sample) < sample_size:
            GPIO.output(self.trigger_pin, GPIO.LOW)
            time.sleep(sample_wait)
            GPIO.output(self.trigger_pin, True)
            time.sleep(0.00001)
            GPIO.output(self.trigger_pin, False)
            echo_status_counter = 1
            sonar_signal_on = None
            while GPIO.input(self.echo_pin) == 0:
                if echo_status_counter < 1000:
                    sonar_signal_off = time.time()
                    echo_status_counter += 1
                else:
                    # Increase the failed pulse counter
                    self.failed_pulse_counter += 1
                    if self.failed_pulse_counter >= 20:
                        return 0  # Output distance as 0 if 20 consecutive failed pulses
                    raise SystemError("Echo pulse was not received")
            while GPIO.input(self.echo_pin) == 1:
                sonar_signal_on = time.time()
            if sonar_signal_on == None:
                continue
            time_passed = sonar_signal_on - sonar_signal_off
            distance_cm = time_passed * ((speed_of_sound * 100) / 2)
            sample.append(distance_cm)
        sorted_sample = sorted(sample)
        
        time.sleep(5)
        return sorted_sample[sample_size // 2]

    # def get_distance(self):
    #     # Send a short pulse to trigger the sensor
    #     GPIO.output(self.trigger_pin, GPIO.HIGH)
    #     time.sleep(0.00001)
    #     GPIO.output(self.trigger_pin, GPIO.LOW)

    #     # Measure the time for the echo pulse
    #     pulse_start_time = time.time()
    #     pulse_end_time = time.time()

    #     while GPIO.input(self.echo_pin) == 0:
    #         pulse_start_time = time.time()

    #     while GPIO.input(self.echo_pin) == 1:
    #         pulse_end_time = time.time()

    #     # Calculate distance in centimeters
    #     pulse_duration = pulse_end_time - pulse_start_time
    #     distance = pulse_duration * 17150  # Speed of sound is 343 meters per second (17150 cm/s)
    #     distance = round(distance, 2)

    #     return distance

    def cleanup(self):
        # Cleanup GPIO settings
        GPIO.cleanup()

    def update_food_level(self, document_id, new_food_level):
        collection_name = "Device_Authorization"
        field_name = "Food_Level"

        doc_ref = firestoreDB.db.collection(collection_name).document(document_id)

        # Check if the document exists
        if doc_ref.get().exists:
            doc_ref.update({field_name: new_food_level})
            print(f"Food_Level updated to {new_food_level} for document {document_id}")
        else:
            print(f"Document {document_id} does not exist in {collection_name} collection.")


# Example usage:
if __name__ == "__main__":
    try:
        # Define trigger and echo pins
        trigger_pin = 22
        echo_pin = 18

        # Create an instance of the HCSR04 class
        sensor = HCSR04(trigger_pin, echo_pin)
        last_distance = None
        percent = None
        last_percent = None
        while True:
            try:
                distance = sensor.raw_distance()
                
                
                print(f"Distance: {distance} cm")
                if last_distance is not None and abs(distance - last_distance) / last_distance * 100 <= 10:
                    continue  # Skip printing if within tolerance
                
                last_distance = distance
                percent = ( (13 - (distance)) / 13 ) * 100
                
                if percent < 0:
                    percent = 0
                elif percent > 100:
                    percent = 100
                
                if last_percent == None:
                    last_percent = percent
                    sensor.update_food_level(get_username(),int(percent))
                elif abs(percent - last_percent) > 5:
                    sensor.update_food_level(get_username(),int(percent))
                    last_percent = percent
                
                
                print(f"Percent: {int(percent)}")
                
                
            except Exception as e:
                print(e)

    except KeyboardInterrupt:
        # Cleanup GPIO settings on keyboard interrupt
        print("\nMeasurement aborted. GPIO cleanup performed.")
    finally:
        sensor.cleanup()
