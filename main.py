import firestoreDB
import threading
from feeding_schedule import feedingSchedule
from wifi import connect_to_wifi
from deviceCredentials import get_password
from deviceCredentials import get_username
from deviceCredentials import upload_credentials
from google.cloud.firestore import FieldFilter

settings_file_path = '/home/kiritian/settings.json'
 

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
            print("Playing audio...")
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
            print("Refreshing Pet...")
            pass
            
        
    tasks_done.set()

query_watch = None

if __name__ == "__main__":
    while connect_to_wifi() != 0:
        pass
    
    query_watch = tasks_collection.on_snapshot(tasks_RealtimeUpdate)
    try:
        print(f"Username: {get_username()}")
        print(f"Password: {get_password()}")
        upload_credentials(get_username(), get_password())
        schedule_feeding()
        while True:
            feedingSched.schedule.run_pending()
            feedingSched.time.sleep(5)
            
    except KeyboardInterrupt:
            
        query_watch.unsubscribe() 
        tasks_done.set()
        print("Program terminated.")
