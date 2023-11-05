import os
import json
import schedule
import time
from datetime import datetime

class feedingSchedule:
    
    def __init__(self):
        self.local_schedules = []
        self.schedule = schedule
        self.time = time

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
        except:
            return 1
        return 0
        


    ####################################################################################################
    # END OF: THIS IS FOR READING DATA FROM FIRESTORE AND STORING THE DATA IN A .Schedules FILE ON HOME FOLDER
    ####################################################################################################



    ####################################################################################################
    # FOR FEEDING TIME FOR PET
    ####################################################################################################

    # Function to feed the pet
    def feed_pet(self, petname, cups):
        print(f"Feeding {petname} with {cups} cups")

    # Function to schedule pet feeding
    def schedule_feeding(self, pet_data):
        print(f"Pet data: {pet_data}")
        for entry in pet_data:
            petname = entry["Petname"]
            days = entry["Days"]
            for schedule_time in entry["ScheduleTime"]:
                time_str = schedule_time["time"]
                cups = schedule_time["cups"]
                
                # Parse the time string into a datetime object
                scheduled_time = datetime.strptime(time_str, "%H:%M").time()
                
                # Get the current time
                current_time = datetime.now().time()
                
                # Schedule future events
                if days == "Everyday" or time_str == "Everyday":
                    self.schedule.every().day.at(time_str).do(self.feed_pet, petname, cups)


    ####################################################################################################
    # END OF: FOR FEEDING TIME FOR PET
    ####################################################################################################
