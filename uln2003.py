import OPi.GPIO as GPIO
import time
import orangepi.one
import sys

IN1 = 0
IN2 = 0
IN3 = 0
IN4 = 0

def __init__(self):
    self.IN1 = 31
    self.IN2 = 33
    self.IN3 = 35
    self.IN4 = 37

def __init__(self, in1, in2, in3, in4):
    self.IN1 = in1
    self.IN2 = in2
    self.IN3 = in3
    self.IN4 = in4
    
def turn_stepper(steps, delay):
    for _ in range(steps):
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.LOW)
        time.sleep(delay)
        
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        time.sleep(delay)
        
        GPIO.output(IN2, GPIO.LOW)
        GPIO.output(IN3, GPIO.HIGH)
        time.sleep(delay)
        
        GPIO.output(IN3, GPIO.LOW)
        GPIO.output(IN4, GPIO.HIGH)
        time.sleep(delay)