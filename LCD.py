import time
import keyboard
from lcd_i2c import LCD_I2C
import subprocess
import re

RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"

# Your existing LCD_I2C and related code
def print_colored(message, color):
    print(f"{color}{message}{RESET}")

def enable_wifi():
    try:
        subprocess.check_output(["nmcli", "r", "wifi", "on"])
        print_colored("WiFi enabling.", GREEN)
    except subprocess.CalledProcessError:
        print_colored("Failed to enable WiFi.", RED)
    time.sleep(5)

def is_connected_to_internet(lcd):
    lcd.clear()
    lcd.write_text("Checking Internet...")
    try:
        subprocess.check_call(["ping", "-c", "1", "8.8.8.8"])
        return True
    except subprocess.CalledProcessError:
        return False

def show_menu(lcd):
    lcd.clear()
    lcd.write_text("Select an option:")
    lcd.cursor.setPos(1, 0)
    lcd.write_text("1. Configure WiFi")
    lcd.cursor.setPos(2, 0)
    lcd.write_text("2. Check IP Address")
    lcd.cursor.setPos(3, 0)
    lcd.write_text("3. Check Status")

def configure_wifi(lcd):
    lcd.clear()
    lcd.write_text("Loading...")

    enable_wifi()

    if is_connected_to_internet(lcd):
        lcd.clear()
        lcd.write_text("Already connected to the internet.")
        time.sleep(1)
        lcd.clear()
        lcd.write_text("Configure wifi?")
        lcd.cursor.setPos(1,0)
        lcd.cursor.off()
        lcd.write_text('(Y)       (N)')
        while True:
            if keyboard.is_pressed('y'):
                break
            elif keyboard.is_pressed('n'):
                lcd.clear()
                lcd.write_text("Going to menu...")
                return True

    lcd.clear()
    lcd.write_text("Scanning for WiFi networks...")

    lcd.blink.on()
    
    while True:
        try:
            networks_list = subprocess.check_output(["nmcli", "-t", "-f", "ssid", "dev", "wifi"]).decode().split("\n")
            # Remove empty elements

            filtered_list = list(set(filter(None, networks_list)))    
            # Remove duplicates
            networks = list(set(filtered_list))
            networks_list.clear()
            for network in networks:
                if len(network) < 15:
                    network = network + ' ' * (15 - len(network))
                networks_list.append(network)
            lcd.clear()
            
            lcd.write_text("Available Networks:")
            
            selected_network = 0
            for i in range(min(3, len(networks))):
                lcd.cursor.setPos(i + 1, 0)
                lcd.write_text(f"{i + 1}. {networks_list[i][:15]}")
            
            
            lcd.cursor.setPos(selected_network + 1, 0)
            while True:
                
                if keyboard.is_pressed('enter'):
                    break
                elif keyboard.is_pressed('up'):
                    selected_network = max(0, selected_network - 1)
                    lcd.cursor.setPos(selected_network + 1, 0)
                    lcd.write_text(f"{selected_network + 1}. {networks_list[selected_network][:15]}")
                    lcd.cursor.setPos(selected_network + 1, 0)
                    time.sleep(0.25)
                elif keyboard.is_pressed('down'):
                    selected_network = min(len(networks) - 1, selected_network + 1)
                    lcd.cursor.setPos(selected_network + 1, 0)
                    lcd.write_text(f"{selected_network + 1}. {networks_list[selected_network][:15]}")
                    lcd.cursor.setPos(selected_network + 1, 0)
                    time.sleep(0.25)

            lcd.clear()
            lcd.write_text(f"Password of {networks[selected_network][:7]}:")
            
            password = ""
            shift_pressed = False
            while True:
                key_event = keyboard.read_event(suppress=True)
                
                key_name = ''
                if key_event.event_type == keyboard.KEY_DOWN:
                    if(key_event.name == 'shift'):
                        shift_pressed = True
                        continue
                    key_name = key_event.name
                    
                elif key_event.event_type == keyboard.KEY_UP:
                    if(key_event.name == 'shift'):
                        shift_pressed = False
                        continue

                if key_name == 'enter':
                    break
                elif key_name == 'backspace':
                    password = password[:-1]
                    lcd.clear()
                    lcd.write_text(f"Password of {networks[selected_network][:6]}")
                    lcd.cursor.setPos(1, 0)
                    lcd.write_text(password)
                elif len(key_name) == 1:
                    # Check if the key is alphanumeric
                    if key_name.isalnum():
                        
                        if shift_pressed:
                            if(key_name in ['0','1','2','3','4','5','6','7','8','9']):
                                symbol_mapping = {'0': ')', '1': '!', '2': '@', '3': '#', '4': '$', '5': '%', '6': '^', '7': '&', '8': '*', '9': '('}
                                password += '\\'
                                password += symbol_mapping[key_name]
                                
                            else:
                                password += key_name.upper()
                        else:
                            password += key_name
                            
                    else:
                        # Handle symbols or special characters
                        symbols_mapping = {'space': ' ', 'minus': '-', 'equal': '=', 'bracketleft': '[', 'bracketright': ']',
                                        'backslash': '\\', 'semicolon': ';', 'apostrophe': "'", 'grave': '`', 'comma': ',',
                                        'dot': '.', 'slash': '/'}
                        password += symbols_mapping.get(key_name, '')

                    lcd.clear()
                    lcd.write_text(f"Password of {networks[selected_network][:6]}:")
                    lcd.cursor.setPos(1, 0)
                    lcd.write_text(password)

            lcd.clear()
            lcd.write_text("Connecting to")
            lcd.cursor.setPos(1,0)
            lcd.write_text(f"{networks[selected_network][:7]}...")

            for attempt in range(5):
                try:
                    
                    command = ["nmcli", "dev", "wifi", "connect", networks[selected_network], "password", password]

                    # Print the command before executing
                    print("Executing command:", " ".join(command))
                    output = subprocess.check_output(command)
                    
                    # Decode the bytes to a string
                    output_str = output.decode("utf-8")

                    # Extract relevant information using regular expressions
                    success_match = re.search(r"Device '(.*?)' successfully activated with '(.*?)'", output_str)
                    if success_match:
                        print("Success!")
                        lcd.clear()
                        lcd.write_text("Connected To The")
                        lcd.cursor.setPos(1,0)
                        lcd.write_text("Network Successfully")
                        time.sleep(2)
                        return True
                    else:
                        
                        lcd.clear()
                        lcd.write_text('Error connecting, trying again...')

                except subprocess.CalledProcessError as e:
                    # Handle error if the command fails
                    print(f"Error: {e.output.decode('utf-8').strip()}")

            return False

        except Exception as e:
            lcd.clear()
            lcd.write_text(f"Error: {str(e)}")
            print_colored(f"Error: {str(e)}", "red")
            return False

def check_ip_address(lcd):
    lcd.clear()
    lcd.blink.off()
    lcd.write_text("Checking IP Address...")

    try:
        # Get and display IP address for eth0
        eth0_output = subprocess.check_output(["ifconfig", "eth0"]).decode("utf-8")
        eth0_ip_match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", eth0_output)
        eth0_ip = eth0_ip_match.group(1) if eth0_ip_match else "Not available"
        
        lcd.clear()
        lcd.write_text("Eth:")
        lcd.write_text(eth0_ip)

        # Get a list of WiFi interfaces starting with "wl"
        iwconfig_output = subprocess.check_output(["iwconfig"]).decode("utf-8")
        wifi_interfaces = re.findall(r"(wl\S+)", iwconfig_output)
        wifi_interfaces = [interface for interface in wifi_interfaces if interface.startswith("wl")]

        # Get and display IP addresses for WiFi interfaces
        for wifi_interface in wifi_interfaces:
            wifi_output = subprocess.check_output(["ifconfig", wifi_interface]).decode("utf-8")
            wifi_ip_match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", wifi_output)
            wifi_ip = wifi_ip_match.group(1) if wifi_ip_match else "Not available"

            lcd.cursor.setPos(1,0)
            lcd.write_text(f"Wifi:")
            lcd.write_text(wifi_ip)

        if not wifi_interfaces:
            lcd.write_text("No interfaces found.")

    except subprocess.CalledProcessError as e:
        # Handle error if the command fails
        lcd.clear()
        lcd.write_text(f"Error: {e.output.decode('utf-8').strip()}")
    
    time.sleep(3)

def check_status(lcd):
    lcd.clear()
    lcd.write_text("Checking Status...")
    # Add your logic to check and display the device status
    time.sleep(2)  # Simulating a delay
    lcd.clear()
    lcd.write_text("Status: OK")

if __name__ == "__main__":
    lcd = LCD_I2C(39, 20, 4)  # Assuming your LCD is 20x4
    
    show_menu(lcd)
    lcd.backlight.on()
    
    while True:
        # Listen for specific key events
        if keyboard.is_pressed('1'):
            configure_wifi(lcd)
            time.sleep(3)
            show_menu(lcd)
        elif keyboard.is_pressed('2'):
            check_ip_address(lcd)
            time.sleep(3)
            show_menu(lcd)
        elif keyboard.is_pressed('3'):
            check_status(lcd)
            time.sleep(3)
            show_menu(lcd)
    
        
