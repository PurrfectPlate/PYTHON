import firestoreDB
import threading
from feeding_schedule import feedingSchedule
import schedule
from livestream import YouTubeLivestreamManager
import os
import json
from pywifi import PyWiFi, const



scheds_collection = firestoreDB.db.collection("feeding_schedule")
livestream_collection = firestoreDB.db.collection("Livestream")
tasks_collection = firestoreDB.db.collection("Task")
# Create an Event for notifying main thread.

feedingSched = feedingSchedule()

tasks_done = threading.Event()


#####################################################################################
#
#   FOR TASKS
#   TAKES DATA FROM FIRESTORE DATABASE
#
#####################################################################################
def tasks_RealtimeUpdate(col_snapshot, changes, read_time):
    
    for doc in col_snapshot:
        type = doc.get("type")
        
        if type.lower() == "schedule":  
            if feedingSched.update(scheds_collection.get()) == 0:
                doc.reference.delete()
                break
            else:
                print("There's an error")
        
        elif type.lower() == "speak_to_pet":
            break
            
        elif type.lower() == "livestream":
            #jsonKeyFile = livestream_collection.document(doc_id).get().to_dict()["jsonKeyFile"]
            #doc_id = doc.get("document_id")
            #youtubeManager = YouTubeLivestreamManager(doc_id)
            
            #title = 'Your Livestream Title'
            #description = 'Your Livestream Description'

            #livestream_id = youtubeManager.start_livestream(title, description)
            print(f"Livestream started with ID")
            pass
        
        elif type.lower() == "refresh_pet":
            pass
            
        
    tasks_done.set()



# Function to connect to WiFi
def connect_to_wifi(wifi_name, wifi_password):
    wifi = PyWiFi()
    iface = wifi.interfaces()[0]
    profile = iface.add_network_profile()
    profile.ssid = wifi_name
    profile.auth = const.AUTH_ALG_OPEN
    profile.akm.append(const.AKM_TYPE_WPA2PSK)
    profile.cipher = const.CIPHER_TYPE_CCMP
    profile.key = wifi_password

    iface.remove_all_network_profiles()
    iface.connect(profile)

    # Give some time for the connection to establish
    import time
    time.sleep(5)

    # Check if the connection was successful
    if iface.status() == const.IFACE_CONNECTED:
        print("Connected to WiFi successfully.")
    else:
        print("Connection failed.")

# Function to check and create settings.json if it doesn't exist
def check_settings_file():
    settings_file_path = '/home/settings.json'
    if not os.path.exists(settings_file_path):
        wifi_name = input("Enter WiFi name: ")
        wifi_password = input("Enter WiFi password: ")
        data = {"wifi_name": wifi_name, "wifi_password": wifi_password}
        with open(settings_file_path, 'w') as f:
            json.dump(data, f)

# Function to read settings.json and connect to WiFi
def read_settings_and_connect():
    settings_file_path = '/home/settings.json'
    if os.path.exists(settings_file_path):
        with open(settings_file_path, 'r') as f:
            data = json.load(f)
            wifi_name = data.get("wifi_name")
            wifi_password = data.get("wifi_password")
            connect_to_wifi(wifi_name, wifi_password)

query_watch = None

if __name__ == "__main__":
    #check_settings_file()
    #read_settings_and_connect()
    query_watch = tasks_collection.on_snapshot(tasks_RealtimeUpdate)
    try:
        while True:
            feedingSched.schedule.run_pending()
            feedingSched.time.sleep(1)
    except KeyboardInterrupt:
            
        query_watch.unsubscribe() 
        tasks_done.set()
        print("Program terminated.")
