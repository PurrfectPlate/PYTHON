import os
import json
import schedule
import time
from datetime import datetime
from uln2003 import ULN2003
from multiprocessing import Process
from serial_communication import SerialCommunication
from audio import AudioPlayer
from smbus2 import SMBus
from lcd_i2c import LCD_I2C
import firestoreDB
from notification import NotificationSender
from deviceCredentials import get_username


class feedingSchedule:
    
    def __init__(self, lcd):
        self.local_schedules = []
        self.schedule = schedule
        self.time = time
        self.lcd = lcd

    def get_local_schedules(self):
        return self.local_schedules

    ####################################################################################################
    # THIS IS FOR READING DATA FROM FIRESTORE AND STORING THE DATA IN A .Schedules FILE ON HOME FOLDER
    ####################################################################################################

    def update(self, col_snapshot):
        try:
            # Load existing local schedules into a list
            home_folder = os.path.expanduser("~")
            file_path = os.path.join(home_folder, ".schedules")

            print("File path: {}".format(file_path))

            if os.path.isfile(file_path):
                with open(file_path, "r") as file:
                    for line in file:
                        schedule = json.loads(line.strip())
                        self.local_schedules.append(schedule)

            # Create a set of Firestore document IDs for fast lookup
            firestore_schedule_ids = {doc.id for doc in col_snapshot}

            # Synchronize local file with Firestore
            with open(file_path, "w") as file:
                for doc in col_snapshot:
                    doc_data = doc.to_dict()
                    doc_id = doc.id

                    # Update the "synced" field to true in the local schedule
                    for local_schedule in self.local_schedules:
                        if local_schedule.get('id') == doc_id:
                            local_schedule['synced'] = True
                            break
                    
                    # Update Firestore with the new data
                    doc_data['synced'] = True  # Update the "synced" field to True
                    doc.reference.update(doc_data)  # Update Firestore document

                    # Write the document to the file, one per line
                    file.write(json.dumps(doc_data) + "\n")

                    # Remove the document ID from the set (if it exists) to track existing documents
                    if doc_id in firestore_schedule_ids:
                        firestore_schedule_ids.remove(doc_id)

            # Remove local schedules that no longer exist in Firestore
            self.local_schedules = [schedule for schedule in self.local_schedules if schedule.get('id') in firestore_schedule_ids]

            if os.path.isfile(file_path):
                with open(file_path, "r") as file:
                    for line in file:
                        schedule = json.loads(line.strip())
                        self.local_schedules.append(schedule)


            self.schedule_feeding(self.get_local_schedules())
        except Exception as e:
            print(e)
            return 1
        return 0
        


    ####################################################################################################
    # END OF: THIS IS FOR READING DATA FROM FIRESTORE AND STORING THE DATA IN A .Schedules FILE ON HOME FOLDER
    ####################################################################################################



    ####################################################################################################
    # FOR FEEDING TIME FOR PET
    ####################################################################################################

    def lcd_write(self, message, slot):
        
        if slot == 1:
            self.lcd.cursor.setPos(0,0)
            self.lcd.write_text(f"1: {message}")
        elif slot == 2:
            self.lcd.cursor.setPos(1,0)
            self.lcd.write_text(f"2: {message}")

    def turn_stepper(self, petname, stepper, cups, rfid, weight, slot = 1):

        p1 = Process(target = stepper.turn_stepper,args=(int(cups)/4,))
        p1.start()
        print(f"TURNING STEPPER MOTOR WITH {int(cups)/4}")
        self.lcd_write("Releasing Food...", slot)
        if(slot == 1):
            ser = SerialCommunication(port="/dev/ttyS1")
        else:
            ser = SerialCommunication(port="/dev/ttyS2")
        ser.startRFID()
        print(f"Ready to Take RFID on {ser.port}")
        self.lcd_write("Taking RFID", slot)
        notif = NotificationSender(firestoreDB.db)
        start_time = time.time()
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time >= 540:  # 540 seconds = 9 minutes
                p1.terminate()  # Stop the turn_stepper process
                notif.fed_a_pet(petname, cups, "", get_username(), successful= False)
                return

            rfid_message = ser.get_next_message()
            

            if rfid_message == None:
                continue
            try:
                received_rfid = rfid_message.split(":")[1].strip()
            except:
                continue

            if received_rfid == rfid:
                ser.stopRFID()
                print(f"RFID MATCHED: {received_rfid}")
                stepper.turn_stepper((int(cups)/4)*3)
                print("TURNING MOTOR AGAIN TO FULL")
                break
            else:
                print("RFID does not match. Stepper will not turn.")
        
        ser.startWeightSensor()
        print("Weight Sensor Starting...")
        weightData = []
        weight = float(weight)
        while True:
            weight_message = ser.get_next_message()

            try:
                weight_value = float(weight_message.split(":")[1].strip())
            except:
                continue

            if 0.9 * weight <= weight_value <= 1.1 * weight:
                weightData.append(weight_value)
                print(f"Appended {weight_value}")

            if len(weightData) == 20:
                print("Already got 20")
                break

        average_weight = sum(weightData) / len(weightData)
        notif.fed_a_pet(petname, cups, get_username(), successful= True)
        return average_weight


    # Function to feed the pet
    def feed_pet(self, document_id, cups, feed_slot = 2):
        print("FEEDING A PET")

        feeder_motor = None
        audio = AudioPlayer(document_id, collection_name = "List_of_Pets")
        pet_document = firestoreDB.get_document_by_id("List_of_Pets", document_id)
        pet_ref = firestoreDB.db.collection("List_of_Pets").document(document_id)
        doc_data = pet_document.to_dict()
            
        
        if feed_slot == 1:
            feeder_motor = ULN2003()
        else:
            feeder_motor = ULN2003(in1=8, in2=10,in3=12,in4=16)
        

        weight = self.turn_stepper(doc_data['Petname'], feeder_motor, cups, doc_data["Rfid"], doc_data["Weight"], feed_slot)
        
        if doc_data['GoalWeight'] < weight:
            #TO IMPLEMENT NOTIFICATION OF GOALWEIGHT
            pass

        pet_ref.update({"Weight" : weight})
        print("Weight successfully changed.")
        

    # Function to schedule pet feeding
    def schedule_feeding(self, pet_data):
        print(f"Pet data: {pet_data}")
        for entry in pet_data:
            documentID = entry['petId']
            petname = entry["Petname"]
            days = entry["Days"]
            feeder_slot = entry['Slot']
            for schedule_time in entry["ScheduleTime"]:
                time_str = schedule_time["time"]
                cups = schedule_time["cups"]
                
                # Schedule future events
                if(days.lower() == "everyday"):
                    self.schedule.every().day.at(time_str).do(self.feed_pet, documentID, cups, feeder_slot)
                else:
                    getattr(self.schedule.every(), days.lower()).at(time_str).do(self.feed_pet, documentID, cups, feeder_slot)
        print(f"SCHEDULES: {schedule.get_jobs()}")


    ####################################################################################################
    # END OF: FOR FEEDING TIME FOR PET
    ####################################################################################################
