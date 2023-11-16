import os
import json

class Pet:
    def __init__(self, name, weight, goalWeight, callingFile):
        self.name = name
        self.weight = weight
        self.goalWeight = goalWeight
        self.callingFile = callingFile
    
    
def update():
    try:
        home_path = os.path.expanduser("~")
        pet_path = os.path.join(home_path, ".schedules")
        print(pet_path)
        
        if(os.path.isfile(pet_path)):
            with open(pet_path, "r") as file:
                for line in file:
                    print(line)
        
    except Exception as e:
        return e
    return 0


print(update())