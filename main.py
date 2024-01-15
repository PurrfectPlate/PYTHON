#PET FEEDER SERVICE: petfeeder.service

import firestoreDB
import threading
import LCD
import keyboard
import time
from livestream import Livestream
from livestream import stop_livestream
from lcd_i2c import LCD_I2C
from serial_communication import SerialCommunication
from feeding_schedule import feedingSchedule
from deviceCredentials import get_password
from deviceCredentials import get_username
from deviceCredentials import upload_credentials
from google.cloud.firestore import FieldFilter
from audio import AudioPlayer
from smbus2 import SMBus
import OPi.GPIO as GPIO
import orangepi.pc
import subprocess

settings_file_path = './settings.json'

GPIO.setmode(orangepi.pc.BOARD)
GPIO.cleanup()
lcd = LCD_I2C(39, 20, 4, False, SMBus(1))
lcd2 = LCD_I2C(38, 16, 2, False, SMBus(0))

lcd.backlight.on()
lcd.clear()
lcd.write_text('STARTING...')
lcd2.backlight.on()
lcd2.clear()
lcd2.write_text('Initializing...')

scheds_collection = firestoreDB.db.collection("feeding_schedule")
livestream_collection = firestoreDB.db.collection("Livestream")
tasks_collection = firestoreDB.db.collection("Task")

# Create an Event for notifying main thread.



feedingSched = feedingSchedule(lcd2)

tasks_done = threading.Event()


#####################################################################################
#
#   FOR TASKS
#   TAKES DATA FROM FIRESTORE DATABASE
#
#####################################################################################

def schedule_feeding():
    if feedingSched.update(scheds_collection.where(filter=FieldFilter("DeviceName", "==", get_username())).get()) == 0:
        print("SCHEDULE REFRESHED")
    else:
        print("There's an error")

def tasks_RealtimeUpdate(col_snapshot, changes, read_time):
    
    
    for doc in col_snapshot:
        
        #IF NOT FOR THIS DEVICE
        if(doc.get("deviceName") != get_username()):
            continue
        
        type = doc.get("type")
        
        if type.lower() == "schedule":  
            print("TASK: REFRESHING SCHEDULE")
            schedule_feeding()
            doc.reference.delete()
            break
        
        elif type.lower() == "dispense_water":
            
            subprocess.run(
                "systemctl start petfeeder_water.service",
                shell=True,
                stdout=subprocess.DEVNULL,
                #stderr=subprocess.DEVNULL
            )
            doc.reference.delete()
            break
        
        elif type.lower() == "speak_to_pet":
            print("TASK: SPEAKING TO DEVICE")
            audio = AudioPlayer(doc.get("document_id"))
            audio.play_sound()
            doc.reference.delete()
            break
        
        elif type.lower() == "livestream":
            doc_id = doc.get("document_id")
            doc_request = doc.get('request')
            
            livestream_document = firestoreDB.get_document_by_id("Livestream", doc_id)
            
            doc_data = livestream_document.to_dict()
            
            livestream_instance = Livestream(key = doc_data['Streamkey'])
            
            try:
                if doc_request == 'Start':
                    print("TASK: STARTING LIVESTREAM")
                    stop_livestream()
                    time.sleep(1)
                    try:
                        livestream_thread = threading.Thread(target=livestream_instance.run_livestream)
                        livestream_thread.start()
                    except Exception as e:
                        print("Error: {e}")
                    doc_data['isliveNow'] = True
                    livestream_document.reference.update(doc_data)
                    print("TASK: LIVESTREAM STARTED!")
                elif doc_request == 'Stop':
                    print("TASK: STOPPING LIVESTREAM")
                    stop_livestream()
                    doc_data['isliveNow'] = False
                    doc_data['ended'] = True
                    doc_data['Youtube_Url'] = ""
                    livestream_document.reference.update(doc_data)
                    print("TASK: STOPPED LIVESTREAM!")
            except:
                print("There's an error trying to livestream")
            doc.reference.delete()
            
        
        elif type.lower() == "request_rfid":
            
            ser = SerialCommunication(f"/dev/ttyS{int(doc.get('request'))}")
            
            ser.startRFID()
            

            print(f"REQUEST RFID: Ready to Take RFID on {ser.port}")
            while True:

                rfid_message = ser.get_next_message()
                if rfid_message == None:
                    continue
                
                try:
                    if rfid_message.split(":")[1].lower().strip() == "none".lower():
                        continue
                except:
                    continue
                
                try:
                    received_rfid = rfid_message.split(":")
                    if received_rfid[0].strip() == "RFID":
                        print("REQUEST RFID: RFID DETECTED")
                        ser.stopRFID()
                        doc_ref = firestoreDB.db.collection("List_of_Pets").document(doc.get('document_id'))
                        pet_data = doc_ref.get().to_dict()
                        
                        if pet_data:
                            doc_ref.update({"Rfid": received_rfid[1].strip()})
                            print(f"REQUEST RFID: Updated Rfid field to {received_rfid[1].strip()} for document {doc.get('document_id')}")

                            doc.reference.delete()
                            break
                        else:
                            print(f"Document {doc_data['document_id']} not found")
                            break

                except IndexError:
                    print("IndexError: Unable to extract RFID information from the message.")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    break

        elif type.lower() == "request_weight":
            ser = SerialCommunication(f"/dev/ttyS{int(doc.get('request'))}")
            ser.startWeightSensor()
            

            print(f"REQUEST WEIGHT: Ready to Take Weight on {ser.port}")
            while True:

                weight_message = ser.get_next_message()
                if weight_message == None:
                    continue
                
                try:
                    if weight_message.split(":")[1].lower().strip() == "none".lower():
                        continue
                except:
                    continue
                
                
                try:
                    received_weight = weight_message.split(":")
                    if received_weight[0].strip() == "Weight Stable":
                        if received_weight[1].strip() == "NONE":
                            continue
                        print("REQUEST WEIGHT: Weight DETECTED")
                        ser.stopWeightSensor()
                        doc_ref = firestoreDB.db.collection("List_of_Pets").document(doc.get('document_id'))
                        pet_data = doc_ref.get().to_dict()
                        
                        if pet_data:
                            doc_ref.update({"Weight": received_weight[1].strip()})
                            print(f"REQUEST WEIGHT: Updated Weight field to {received_weight[1].strip()} for document {doc.get('document_id')}")

                            doc.reference.delete()
                            break
                        else:
                            print(f"Document {doc_data['document_id']} not found")

                            break

                except IndexError:
                    print("IndexError: Unable to extract WEIGHT information from the message.")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    break
            
        
    tasks_done.set()

query_watch = None

def show_credentials(lcd):
    lcd.clear()
    lcd.blink.off()
    lcd.write_text("Username:")
    lcd.cursor.setPos(1,0)
    lcd.write_text(get_username())
    lcd.cursor.setPos(2,0)
    lcd.write_text("Password: ")
    lcd.cursor.setPos(3,0)
    lcd.write_text(get_password())
    time.sleep(3)

if __name__ == "__main__":
    lcd.clear()
    lcd.write_text("Checking Internet...")
    while LCD.configure_wifi(lcd) == False:
        pass
    
    try:
        query_watch = tasks_collection.on_snapshot(tasks_RealtimeUpdate)
    except Exception as e:
        print("e")
        
    
    
    try:
        print(f"Username: {get_username()}")
        print(f"Password: {get_password()}")
        upload_credentials(get_username(), get_password())
        schedule_feeding()
        
        options_list = ['Configure WiFi', 'Check IP Address', 'Check User/Pass']
        max_length = 15
        options_list = [f'{option:<{max_length}}' for option in options_list]
        
        selected_option= 0
        
        def reset():
            lcd.clear()
            lcd.blink.on()
            lcd.write_text("Select an option:")
            for i in range(min(3, len(options_list))):
                lcd.cursor.setPos(i + 1, 0)
                lcd.write_text(f"{i + 1}. {options_list[i][:15]}")
        
        reset()
        
        lcd.cursor.setPos(selected_option + 1, 0)
        while True:
            feedingSched.schedule.run_pending()
            if keyboard.is_pressed('enter'):
                match selected_option:
                    case 0:
                        LCD.configure_wifi(lcd)
                        reset()
                        continue
                    case 1:
                        LCD.check_ip_address(lcd)
                        reset()
                        continue
                    case 2:
                        show_credentials(lcd)
                        reset()
                        continue
            
            elif keyboard.is_pressed('up'):
                selected_option = max(0, selected_option - 1)
                lcd.cursor.setPos(selected_option + 1, 0)
                lcd.write_text(f"{selected_option + 1}. {options_list[selected_option][:15]}")
                lcd.cursor.setPos(selected_option + 1, 0)
                time.sleep(0.25)
            elif keyboard.is_pressed('down'):
                selected_option = min(len(options_list) - 1, selected_option + 1)
                lcd.cursor.setPos(selected_option + 1, 0)
                lcd.write_text(f"{selected_option + 1}. {options_list[selected_option][:15]}")
                lcd.cursor.setPos(selected_option + 1, 0)
                time.sleep(0.25)
            
            
    except KeyboardInterrupt:
        lcd.clear()
        lcd.backlight.off()
        query_watch.unsubscribe() 
        tasks_done.set()
        GPIO.cleanup()
        print("Program terminated.")
    
    finally:
        ser2 = SerialCommunication(port="/dev/ttyS2")
        ser1 = SerialCommunication(port="/dev/ttyS1")
        ser1.stopWeightSensor()
        ser1.stopRFID()
        ser2.stopWeightSensor()
        ser2.stopRFID()
        lcd.clear()
        lcd.backlight.off()
        lcd2.backlight.off()
        lcd2.clear()
        query_watch.unsubscribe() 
        tasks_done.set()
        GPIO.cleanup()
        print("Program Terminated.")
        