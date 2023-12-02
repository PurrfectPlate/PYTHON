import firestoreDB
import threading
import LCD
import keyboard
import time
from livestream import Livestream
from lcd_i2c import LCD_I2C
from serial_communication import SerialCommunication
from feeding_schedule import feedingSchedule
from deviceCredentials import get_password
from deviceCredentials import get_username
from deviceCredentials import upload_credentials
from google.cloud.firestore import FieldFilter
from audio import AudioPlayer

settings_file_path = './settings.json'
 
lcd = LCD_I2C(39, 20, 4)

lcd.backlight.on()
lcd.clear()
lcd.write_text('STARTING...')

scheds_collection = firestoreDB.db.collection("feeding_schedule")
livestream_collection = firestoreDB.db.collection("Livestream")
tasks_collection = firestoreDB.db.collection("Task")

livestream_instance = Livestream()
# Create an Event for notifying main thread.

feedingSched = feedingSchedule()

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
        
        if(doc.get("deviceName") != get_username()):
            print("Not for this device")
            continue
        
        print(doc)
        
        
        type = doc.get("type")
        
        if type.lower() == "schedule":  
            schedule_feeding()
            doc.reference.delete()
            break
        
        elif type.lower() == "speak_to_pet":
            audio = AudioPlayer(doc.get("document_id"))
            break
        
        elif type.lower() == "livestream":
            doc_id = doc.get("document_id")
            doc_request = doc.get('request')
            
            livestream_document = firestoreDB.get_document_by_id("Livestream", doc_id)
            
            doc_data = livestream_document.to_dict()
            
            livestream_instance = Livestream(key = doc_data['Streamkey'])
            
            try:
                if doc_request == 'Start':
                    livestream_instance.stop_livestream()
                    livestream_instance.run_livestream()
                    doc_data['isliveNow'] = True
                    livestream_document.reference.update(doc_data)
                elif doc_request == 'Stop':
                    livestream_instance.stop_livestream()
                    doc_data['isliveNow'] = False
                    doc_data['youtube_url'] = False
                    livestream_document.reference.update(doc_data)
            except:
                print("There's an error trying to livestream")
            
            print(f"Livestream started with ID")
            pass
        
        elif type.lower() == "refresh_pet":
            print("Refreshing Pet...")
            pass
            
        
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
    
    
    query_watch = tasks_collection.on_snapshot(tasks_RealtimeUpdate)
    try:
        print(f"Username: {get_username()}")
        print(f"Password: {get_password()}")
        upload_credentials(get_username(), get_password())
        schedule_feeding()
        
        options_list = ['Configure WiFi', 'Check IP Address', 'Check User/Pass', 'Feed a Pet']
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
        
        while True:
            feedingSched.schedule.run_pending()
            
            lcd.cursor.setPos(selected_option + 1, 0)
            while True:
                
                if keyboard.is_pressed('enter'):
                    match selected_option:
                        case 0:
                            LCD.configure_wifi(lcd)
                            reset()
                            break
                        case 1:
                            LCD.check_ip_address(lcd)
                            reset()
                            break
                        case 2:
                            show_credentials(lcd)
                            reset()
                            break
                
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
        print("Program terminated.")
