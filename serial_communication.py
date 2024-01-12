import time
import serial

class SerialCommunication:
    def __init__(self, port="/dev/ttyS1", baudrate="9600"):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = serial.Serial(port=self.port, baudrate=self.baudrate)

    def get_next_message(self):
        try:
            if self.serial_connection.is_open:
                message = self.serial_connection.readline().decode('utf-8').strip()
                if not message:
                    return None
                return message
            else:
                print("Serial connection is not open.")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def send_message(self, message):
        if self.serial_connection.is_open:
            message_bytes = (str(message) + '\n').encode('utf-8')
            self.serial_connection.write(message_bytes)
            print(f"Message sent: {message}")
        else:
            print("Serial connection is not open.")
    
    def startRFID(self):
        self.send_message("StartRFID")
        time.sleep(1.5)

    def stopRFID(self):
        self.send_message("StopRFID")
        self.serial_connection.reset_input_buffer()
        time.sleep(1.5)
    
    def startWeightSensor(self):
        self.send_message("StartWeightSensor")
        time.sleep(1.5)

    def stopWeightSensor(self):
        self.send_message("StopWeightSensor")
        self.serial_connection.reset_input_buffer()
        time.sleep(1.5)

if __name__ == "__main__":
    try:
        ser = SerialCommunication()
        ser2 = SerialCommunication(port="/dev/ttyS2")
        ser.startRFID()
        ser2.startRFID()
        ser.startWeightSensor()
        ser2.startWeightSensor()
        
        count = 0
        while True:
            #last_message = ser.get_next_message()

            last_message2 = ser2.get_next_message()

            #print("1: "+ last_message)
            print("2: "+ last_message2)

    except Exception as e:
        print(e)
        
    except KeyboardInterrupt:
        ser.stopRFID()
        ser2.stopRFID()
        ser.stopWeightSensor()
        ser2.stopWeightSensor()
