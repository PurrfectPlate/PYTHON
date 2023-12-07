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

    def stopRFID(self):
        self.send_message("StopRFID")
        self.serial_connection.reset_input_buffer()
    
    def startWeightSensor(self):
        self.send_message("StartWeightSensor")

    def stopWeightSensor(self):
        self.send_message("StopWeightSensor")
        self.serial_connection.reset_input_buffer()

if __name__ == "__main__":
    try:
        ser = SerialCommunication()
        ser.send_message("StartRFID")
        count = 0
        while True:
            last_message = ser.get_next_message()

            print(last_message)

    except Exception as e:
        print(e)
