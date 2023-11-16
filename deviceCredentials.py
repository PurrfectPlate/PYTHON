import os
import hashlib
import firestoreDB

def get_mac_address():
    try:
        mac_address = os.popen("cat /sys/class/net/enp2s0/address").read().strip()
        return mac_address
    except:
        return None

def get_username():
    # Get MAC Address
    motherboard_id = get_mac_address()

    # Creating a hash based on the concatenation of salt and node ID
    hashed_value = hashlib.sha256((motherboard_id).encode()).hexdigest()

    username = "PurrfectPlate_" + hashed_value[3:7]

    return username

def get_password():
    
    # Getting the node ID of the Orange Pi
    motherboard_id = get_mac_address()
    salt = "kiripass"
    
    password = motherboard_id.replace(':','')[:6] + hashlib.sha256((motherboard_id+salt).encode()).hexdigest()[:7]
    
    return password

def upload_credentials(username, password):
    credentials_document = firestoreDB.db.collection("Device_Authorization").document(username)
    data = {"DeviceName": username, "Password": hashlib.sha256(password.encode()).hexdigest()}
    credentials_document.set(data)
    print("USERNAME AND PASSWORD UPLOADED")
    