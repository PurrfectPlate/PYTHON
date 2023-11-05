import os
import hashlib

def get_mac_address():
    try:
        mac_address = os.popen("cat /sys/class/net/enp2s0/address").read().strip()
        return mac_address
    except:
        return None

def get_username():
    # Getting the node ID of the Orange Pi
    motherboard_id = get_mac_address()

    print(motherboard_id)
    # Generating a random UUID as the salt value
    salt = "kiri"

    # Assuming the model name is "OrangePiPlus"
    model_name = "OPOH3"

    # Creating a hash based on the concatenation of salt and node ID
    hashed_value = hashlib.sha256((motherboard_id).encode()).hexdigest()

    # Concatenating the prefix "op_" with the lowercased model name and the truncated hash
    username = "PurrfectPlate_" + model_name.lower() + "_" + hashed_value[:7]

    return username

def get_password():
    
    # Getting the node ID of the Orange Pi
    motherboard_id = get_mac_address()
    salt = "kiripass"
    
    password = hashlib.sha256(motherboard_id.encode()).hexdigest()
    
    return password

print("Username: " + get_username())
print("Password: " + get_password())