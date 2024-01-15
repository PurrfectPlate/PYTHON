import multiprocessing
import os
import json
import threading
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
import traceback


class feedingSchedule:
    
    def __init__(self, lcd):
        self.local_schedules = []
        self.schedule = schedule
        self.time = time
        self.lcd = lcd
        self.audio = [None, None]
        self.stepper = [ULN2003(in1=8, in2=10,in3=12,in4=16), ULN2003()]
        self.lastPlayed = 0
        self.notif = NotificationSender(firestoreDB.db)
        self.lcd_write("WAITING SCHED", 1)
        self.lcd_write("WAITING SCHED", 2)
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
        # Define the maximum length for each line on the LCD
        max_length = 13

        if len(message) > max_length:
            # If the message is longer than the LCD width, truncate it
            message = message[:max_length]
        else:
            # If the message is shorter, pad it with spaces
            message = message.ljust(max_length)

        if slot == 1:
            self.lcd.cursor.setPos(0, 0)
            self.lcd.write_text(f"1: {message}")
        elif slot == 2:
            self.lcd.cursor.setPos(1, 0)
            self.lcd.write_text(f"2: {message}")


    def turn_stepper(self, petname, cups, rfid, weight, slot = 1):

        #p1 = Process(target = stepper.turn_stepper,args=(int(cups)/4,))
        #p1.start()
        #print(f"TURNING STEPPER MOTOR WITH {int(cups)/4}")
        #self.lcd_write("Releasing Food...", slot)
        timer_seconds = 180
        
        if(slot == 1):
            ser = SerialCommunication(port="/dev/ttyS1")
        else:
            ser = SerialCommunication(port="/dev/ttyS2")
        ser.startRFID()
        print(f"Ready to Take RFID on {ser.port}")
        self.lcd_write("Taking RFID", slot)
        possible_pets = []
        
        start_time = time.time()
        seconds = timer_seconds
        while True:
            print(f"Remaining time for slot {slot}: {seconds - int(time.time() - start_time)} seconds.")
            
            if int(time.time() - start_time) > seconds:
                self.lcd_write("NO RFID DETECTED!", slot)
                ser.stopRFID()
                ser.stopWeightSensor()
                self.notif.fed_a_pet(petname, cups, get_username(), successful= False,special_message="RFID not read.")
                
                if len(possible_pets) > 0:
                    self.notif.potential_food_consumption(possible_pets,petname,get_username())
                    possible_pets.clear()
                return -1
            
            if self.audio[0] is not None and self.audio[1] is not None:
                if not (self.audio[0].isPlaying or self.audio[1].isPlaying):
                    if int(slot) != self.lastPlayed:
                        try:
                            sound_thread = threading.Thread(target=self.audio[int(slot) - 1].play_sound)
                            sound_thread.start()
                            self.lastPlayed = int(slot)
                        except Exception as e:
                            print("Error:", e)
            elif self.audio[int(slot) - 1] is not None:
                if not self.audio[int(slot) - 1].isPlaying:
                    try:
                        sound_thread = threading.Thread(target=self.audio[int(slot) - 1].play_sound)
                        sound_thread.start()
                        self.lastPlayed = int(slot)
                    except Exception as e:
                        print("Error:", e)
            else:
                # Handle the case when one or both elements are None
                pass  # Or raise an error, log a message, etc.

            rfid_message = ser.get_next_message()
            

            if rfid_message == None:
                continue
            try:
                received_rfid = rfid_message.split(":")[1].strip()
                if received_rfid.upper() == "NONE":
                    continue
            except:
                continue

            if received_rfid.upper() == rfid.upper():
                self.lcd_write("RFID MATCHED!", slot)
                ser.stopRFID()
                print(f"RFID MATCHED: {received_rfid}")
                self.audio[int(slot - 1)] = None
                
                cups = int(cups)
                process = multiprocessing.Process(target=self.stepper[int(slot) - 1].turn_stepper, args=(cups,))
                process.start()
                
                self.lcd_write("DISPENSING FOOD", slot)
                print("TURNING MOTOR TO FULL")
                break
            else:
                print(f"RFID does not match. Stepper will not turn. {received_rfid}")
        
        ser.startWeightSensor()
        print("Weight Sensor Starting...")
        self.lcd_write("Waiting Weight", slot)
        weightData = []
        weight = float(weight)
        seconds = timer_seconds - int(time.time() - start_time)
        start_time = time.time()
        while True:
            
            print(f"Remaining time for slot {slot}: {seconds - int(time.time() - start_time)} seconds.")
            
            if int(time.time() - start_time) > seconds:
                ser.stopRFID()
                ser.stopWeightSensor()
                self.notif.fed_a_pet(petname, cups, get_username(), successful= False,special_message="Weight wasn't received.")
                
                if len(possible_pets) > 0:
                    self.notif.potential_food_consumption(possible_pets,petname,get_username())
                    possible_pets.clear()
                return -1
            
            weight_message = ser.get_next_message()
            

            try:
                weight_value = float(weight_message.split(":")[1].strip())
                if(weight_value == "None"):
                    print("NONE WEIGHT")
                    continue
            except:
                continue

            if 0.9 * weight <= weight_value <= 1.1 * weight:
                weightData.append(weight_value)
                print(f"Appended {weight_value}")
                self.lcd_write("Getting Weigh", slot)
                #self.lcd_write(f"Weight:{weight_value}kg", slot)

            if len(weightData) == 20:
                print("Already got 20")
                self.lcd_write('Got Weight!', slot)
                ser.stopWeightSensor()
                break

        average_weight = sum(weightData) / len(weightData)
        ser.stopWeightSensor()
        ser.startRFID()
        seconds = timer_seconds - int(time.time() - start_time)
        start_time = time.time()
        while time.time() - start_time < seconds:
            
            self.lcd_write("DETECT RFID", slot)
            #self.lcd_write(f"Time left: {seconds - int(time.time() - start_time)}", slot)
            print(f"Remaining time for slot {slot}: {seconds - int(time.time() - start_time)} seconds.")
        
            rfid_message = ser.get_next_message()
        
            if rfid_message == None:
                continue
            try:
                received_rfid = rfid_message.split(":")[1].strip()
                if received_rfid.upper() == "NONE":
                    continue
            except:
                continue

            if received_rfid.upper() != rfid.upper():
                if received_rfid not in possible_pets:
                    possible_pets.append(received_rfid)
                    print("PET with RFID {received_rfid} was detected.")
        
        
        self.lcd_write(f"Feeding Done!", slot)
        ser.stopRFID()
        ser.stopWeightSensor()
        
        if len(possible_pets) > 0:
            self.notif.potential_food_consumption(possible_pets,petname,get_username())
            possible_pets.clear()
        self.notif.fed_a_pet(petname, cups, get_username(), successful= True)
        return average_weight
        



    # Function to feed the pet
    def feed_pet(self, document_id, cups, feed_slot = 2):
        try:
            print("FEEDING A PET")
            self.audio[feed_slot - 1] = AudioPlayer(document_id, collection_name = "List_of_Pets", slot = int(feed_slot - 1))
            pet_document = firestoreDB.get_document_by_id("List_of_Pets", document_id)
            pet_ref = firestoreDB.db.collection("List_of_Pets").document(document_id)
            doc_data = pet_document.to_dict()
            
            
            self.lcd_write("FEEDING " + doc_data['Petname'], feed_slot)
            weight = self.turn_stepper(doc_data['Petname'], cups, doc_data["Rfid"], doc_data["Weight"], feed_slot)
            
            if(weight <= 0):
                print("There was an error on feeding")
                return 0
            
            
            current_date = datetime.now()
            
            end_goal_month_str = doc_data['EndGoalMonth']
            
            if end_goal_month_str is None or end_goal_month_str.lower() == 'Invalid Date'.lower():
                print("No goal month specified.")
            else:
                try:
                    # Convert the EndGoalMonth string to a datetime object
                    end_goal_month = datetime.strptime(end_goal_month_str, '%m/%d/%Y')

                    # Compare current date with EndGoalMonth
                    if current_date > end_goal_month:
                        print("Failed: Current date is after EndGoalMonth.")
                        self.notif.goal_weight_achieved(doc_data['Petname'],doc_data['GoalWeight'], get_username(), False)
                    elif round(float(doc_data['GoalWeight'])) < round(float(weight)):
                        self.notif.goal_weight_achieved(doc_data['Petname'],doc_data['GoalWeight'], get_username(), True)
                except Exception as e:
                    print("There's an error trying to get Goal Weight.")
                    
        
            pet_ref.update({"Weight" : weight})
            print("Weight successfully changed.")
            return 0
        
        except Exception as e:
            print(f"Error on feed_pet: {e}")
            traceback.print_exc()
            exception_traceback = traceback.format_exc()
            print(f"Exception occurred on line {line_number}")
        finally:
            print(f"DONE FEEDING SLOT {feed_slot}")
            self.lcd_write("WAITING SCHED", feed_slot)

    # Function to schedule pet feeding
    def schedule_feeding(self, pet_data):
        self.schedule.clear()
        for entry in pet_data:
            documentID = entry['petId']
            days = entry["Days"]
            feeder_slot = entry['Slot']
            for schedule_time in entry["ScheduleTime"]:
                time_str = schedule_time["time"]
                cups = schedule_time["cups"]
                
                thread = threading.Thread(target=self.feed_pet, args=(documentID, cups, feeder_slot))
                # Schedule future events
                if(days.lower() == "everyday"):
                    self.schedule.every().day.at(time_str).do(thread.start)
                else:
                    getattr(self.schedule.every(), days.lower()).at(time_str).do(thread.start)
        print(f"SCHEDULES: {schedule.get_jobs()}")


    ####################################################################################################
    # END OF: FOR FEEDING TIME FOR PET
    ####################################################################################################
