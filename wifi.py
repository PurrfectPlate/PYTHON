import subprocess
import time

# ANSI escape codes for colors
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"

def is_connected_to_internet():
    try:
        subprocess.check_call(["ping", "-c", "1", "8.8.8.8"])
        return True
    except subprocess.CalledProcessError:
        return False

def print_colored(message, color):
    print(f"{color}{message}{RESET}")

def enable_wifi():
    try:
        subprocess.check_output(["nmcli", "r", "wifi", "on"])
        print_colored("WiFi enabling.", GREEN)
    except subprocess.CalledProcessError:
        print_colored("Failed to enable WiFi.", RED)
    time.sleep(5)

def connect_to_wifi():
    enable_wifi()

    if is_connected_to_internet():
        print_colored("Already connected to the internet. No need to connect to WiFi.", GREEN)
        return 0

    while True:
        try:
            networks = subprocess.check_output(["nmcli", "-t", "-f", "ssid", "dev", "wifi"]).decode().split("\n")
            print_colored("Available Networks:", YELLOW)

            for i, network in enumerate(networks):
                print_colored(f"{i+1}. {network}", YELLOW)

            selected_network = int(input("Enter the number of the network you want to connect to: "))
            password = input("Enter the password for the selected network: ")

            subprocess.check_output(["nmcli", "dev", "wifi", "connect", networks[selected_network-1], "password", password])

            print_colored("Connected to the network!", GREEN)
            return 0
            break

        except (ValueError, IndexError):
            print_colored("Invalid input. Please try again.", RED)
            time.sleep(2)

        except subprocess.CalledProcessError:
            print_colored("Failed to connect to the network. Please check your credentials and try again.", RED)
            time.sleep(2)
