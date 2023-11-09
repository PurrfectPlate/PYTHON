import OPi.GPIO as GPIO
import time
import orangepi.one
import sys

class ULN2003:
    def __init__(self, in1=31, in2=33, in3=35, in4=37):
        self.IN1 = in1
        self.IN2 = in2
        self.IN3 = in3
        self.IN4 = in4

        GPIO.setmode(orangepi.one.BOARD)
        GPIO.setup(self.IN1, GPIO.OUT)
        GPIO.setup(self.IN2, GPIO.OUT)
        GPIO.setup(self.IN3, GPIO.OUT)
        GPIO.setup(self.IN4, GPIO.OUT)

    def turn_stepper(self, steps, delay=0.002):
        full_rotate = 512
        rotate_times = 512 * steps
        for _ in range(rotate_times):
            GPIO.output(self.IN1, GPIO.HIGH)
            GPIO.output(self.IN2, GPIO.LOW)
            GPIO.output(self.IN3, GPIO.LOW)
            GPIO.output(self.IN4, GPIO.LOW)
            time.sleep(delay)

            GPIO.output(self.IN1, GPIO.LOW)
            GPIO.output(self.IN2, GPIO.HIGH)
            time.sleep(delay)
            
            GPIO.output(self.IN2, GPIO.LOW)
            GPIO.output(self.IN3, GPIO.HIGH)
            time.sleep(delay)
            
            GPIO.output(self.IN3, GPIO.LOW)
            GPIO.output(self.IN4, GPIO.HIGH)
            time.sleep(delay)
            

GPIO.cleanup()



