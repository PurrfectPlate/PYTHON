import OPi.GPIO as GPIO
import time
import orangepi.one
import sys
from serial_communication import SerialCommunication

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

            
    def turn_stepper_forward(self, rotate_times = 0, delay=0.0016):
        
        for _ in range(int(rotate_times)):
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
    
    
    def turn_stepper_backward(self, rotate_times, delay=0.002):
        
        for _ in range(int(rotate_times)):
            GPIO.output(self.IN1, GPIO.LOW)
            GPIO.output(self.IN2, GPIO.LOW)
            GPIO.output(self.IN3, GPIO.LOW)
            GPIO.output(self.IN4, GPIO.HIGH)
            time.sleep(delay)

            GPIO.output(self.IN3, GPIO.HIGH)
            GPIO.output(self.IN4, GPIO.LOW)
            time.sleep(delay)

            GPIO.output(self.IN2, GPIO.HIGH)
            GPIO.output(self.IN3, GPIO.LOW)
            time.sleep(delay)

            GPIO.output(self.IN2, GPIO.LOW)
            GPIO.output(self.IN1, GPIO.HIGH)
            time.sleep(delay)
    
    def turn_stepper(self, steps, delay=0.002):
        rotate_times = 512 * steps
        while rotate_times > 0:
            self.turn_stepper_forward(min(512,max(rotate_times, 0)))
            rotate_times -= 512
            print(rotate_times)
            #self.turn_stepper_backward(min(128,max(rotate_times, 0)))
            #rotate_times -= 64
            #print(rotate_times)
GPIO.cleanup()

if __name__ == "__main__":
    stepper = ULN2003(in1=8, in2=10,in3=12,in4=16)
    
    #stepper = ULN2003()
    stepper.turn_stepper(20)
    #stepper.turn_stepper_forward(512)
    
    