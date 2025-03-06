import socket
import time
import getpass
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from messaging.csmessage import CSmessage, REQS
from messaging.cspdu import SmartHomePDU as CSpdu

HOST = "127.0.0.1"
PORT = 5000

def display_device_info(devices):
    """Helper function to display device information in a formatted way"""
    if not devices:
        print("No devices found or unauthorized access")
        return
        
    # Check if devices is a string and try to parse it
    if isinstance(devices, str):
        try:
            devices = json.loads(devices.replace("'", '"'))
        except json.JSONDecodeError:
            print("[ERROR] Failed to parse device information")
            return
            
    print("\nDevice Status:")
    
    # Format the output for better readability
    for room, room_info in devices.items():
        print(f"\n=== {room} ===")
        
        if "devices" in room_info:
            # Check if this is the special "Home" room with house_alarm
            is_home_with_alarm = (room == "Home" and 
                                 "house_alarm" in room_info["devices"])
            
            # If it's the Home room with house alarm, display it specially
            if is_home_with_alarm:
                alarm = room_info["devices"]["house_alarm"]
                print(f"  • House Alarm ({alarm.get('type', 'Alarm')})")
                
                # Display all relevant properties except PIN
                for key, value in alarm.items():
                    if key == "type":
                        continue  # Already displayed in the device header
                    # elif key == "pin":
                    #     print(f"    {key.capitalize()}: [PROTECTED]")
                    else:
                        # Format the property name for better readability
                        pretty_key = key.replace("_", " ").capitalize()
                        print(f"    {pretty_key}: {value}")
                
                print()  # Empty line
                continue  # Skip the regular device display for this room
            
            # Regular display for normal rooms
            for device_name, device_info in room_info["devices"].items():
                # Skip the second display of house_alarm
                if room == "Home" and device_name == "house_alarm":
                    continue
                    
                print(f"  • {device_name} ({device_info.get('type', 'Unknown')})")
                
                # Display all relevant properties
                for key, value in device_info.items():
                    if key == "type":
                        continue  # Already displayed in the device header
                    # elif key == "pin_codes" and device_info.get('type') == "Lock":
                    #     print(f"    {key.capitalize()}: [PROTECTED]")
                    # elif key == "pin" and device_info.get('type') == "Alarm":
                    #     print(f"    {key.capitalize()}: [PROTECTED]")
                    else:
                        # Format the property name for better readability
                        pretty_key = key.replace("_", " ").capitalize()
                        print(f"    {pretty_key}: {value}")
                
                print()  # Empty line between devices
        else:
            print("  No devices found in this room\n")

def handle_window_blind(pdu, room, device):
    """Special handler for window blind operations"""
    print("\nWindow Blind Controls:")
    print("1. Raise blind up")
    print("2. Lower blind down")
    print("3. Open blind")
    print("4. Close blind")
    blind_option = input("Choose an option: ")
    
    status = None
    if blind_option == "1":
        status = "up"
    elif blind_option == "2":
        status = "down"
    elif blind_option == "3":
        status = "open"
    elif blind_option == "4":
        status = "closed"
    else:
        print("Invalid option")
        return
    
    # Send the status change request
    msg = CSmessage()
    msg.setType(REQS.CHG_STATUS)
    msg.addValue("room", room)
    msg.addValue("device", device)
    msg.addValue("status", status)
    
    print(f"\n[DEBUG] Sending CHG_STATUS request: {msg.marshal()}")
    pdu.send_message(msg)
    
    print("[DEBUG] Waiting for server response...")
    response = pdu.receive_message()
    print(f"[DEBUG] Received response: {response.marshal()}")
    
    if response:
        status = response.getValue("status")
        message = response.getValue("message")
        print(f"\nResult: {status}")
        if message:
            print(f"Message: {message}")

def handle_light(pdu, room, device, current_status=None, current_brightness=None, current_color=None):
    """Special handler for light operations"""
    print("\nLight Controls:")
    print(f"Current status: {current_status}")
    if current_brightness is not None:
        print(f"Current brightness: {current_brightness}")
    if current_color:
        print(f"Current color: {current_color}")
        
    print("\nOptions:")
    print("1. Turn On")
    print("2. Turn Off")
    print("3. Set Brightness")
    print("4. Change Color")
    light_option = input("\nChoose an option: ")
    
    msg = CSmessage()
    msg.setType(REQS.CHG_STATUS)
    msg.addValue("room", room)
    msg.addValue("device", device)
    
    if light_option == "1":
        msg.addValue("status", "on")
    elif light_option == "2":
        msg.addValue("status", "off")
    elif light_option == "3":
        while True:
            try:
                brightness = int(input("\nEnter brightness level (0-100): "))
                if 0 <= brightness <= 100:
                    msg.addValue("status", "dimmed")
                    msg.addValue("brightness", brightness)
                    break
                else:
                    print("Brightness must be between 0 and 100")
            except ValueError:
                print("Please enter a valid number")
                continue
    elif light_option == "4":
        color = input("\nEnter color (e.g., red, blue, white or RGB format 255,0,0): ")
        # Keep the current status unless it was "off"
        if current_status == "off":
            msg.addValue("status", "on")  # Turn on when changing color from off
        else:
            msg.addValue("status", current_status)  # Keep current status
        msg.addValue("color", color)
    else:
        print("Invalid option")
        return
    
    print(f"\n[DEBUG] Sending CHG_STATUS request: {msg.marshal()}")
    pdu.send_message(msg)
    
    print("[DEBUG] Waiting for server response...")
    response = pdu.receive_message()
    print(f"[DEBUG] Received response: {response.marshal()}")
    
    if response:
        status = response.getValue("status")
        message = response.getValue("message")
        print(f"\nResult: {status}")
        if message:
            print(f"Message: {message}")

def handle_house_alarm(pdu):
    """Special handler for house alarm operations"""
    print("\nHouse Alarm Controls:")
    print("1. Arm")
    print("2. Disarm")
    alarm_option = input("Choose an option: ")
    
    status = None
    if alarm_option == "1":
        status = "armed"
    elif alarm_option == "2":
        status = "disarmed"
    else:
        print("Invalid option")
        return
    
    pin = input("Enter PIN: ")
    
    # Send the status change request
    msg = CSmessage()
    msg.setType(REQS.CHG_STATUS)
    msg.addValue("device", "house_alarm")
    msg.addValue("status", status)
    msg.addValue("pin", pin)
    
    print(f"\n[DEBUG] Sending CHG_STATUS request: {msg.marshal()}")
    pdu.send_message(msg)
    
    print("[DEBUG] Waiting for server response...")
    response = pdu.receive_message()
    print(f"[DEBUG] Received response: {response.marshal()}")
    
    if response:
        status = response.getValue("status")
        message = response.getValue("message")
        print(f"\nResult: {status}")
        if message:
            print(f"Message: {message}")

def masked_input(prompt="Password: "):
    """Get password input with asterisk masking for multiple platforms"""
    import platform
    import sys
    
    if platform.system() == 'Windows':
        import msvcrt
        print(prompt, end='', flush=True)
        password = ""
        while True:
            char = msvcrt.getch()
            char = char.decode('utf-8') if isinstance(char, bytes) else char
            
            if char == '\r' or char == '\n':
                print()
                break
            elif char == '\b' or ord(char) == 8:
                if password:
                    password = password[:-1]
                    print('\b \b', end='', flush=True)
            elif ord(char) == 3:  # Ctrl+C
                raise KeyboardInterrupt
            elif ord(char) >= 32:
                password += char
                print('*', end='', flush=True)
        return password
    
    else:  # Unix/Linux/MacOS
        import termios
        import tty
        
        print(prompt, end='', flush=True)
        password = ""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            tty.setraw(fd)
            while True:
                char = sys.stdin.read(1)
                
                if char == '\r' or char == '\n':
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    break
                elif char == '\x7f' or ord(char) == 127:  # backspace or delete
                    if password:
                        password = password[:-1]
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                elif ord(char) == 3:  # ctrl-c
                    raise KeyboardInterrupt
                elif ord(char) >= 32:
                    password += char
                    sys.stdout.write('*')
                    sys.stdout.flush()
                    
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
        return password

def main():
    print("\n[SMART HOME APP]")
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(10)
        client.connect((HOST, PORT))
        pdu = CSpdu(client)
        print(r"""
        ╔════════════════════════════════════════════╗
        ║             SMART HOME SYSTEM              ║
        ║          Remote Access Interface           ║
        ╚════════════════════════════════════════════╝
        """)
        print(" Welcome to your Smart Home Control Center")
        print(" • Control your devices from anywhere")
        print(" • Monitor home status remotely")
        print(" • Manage security systems\n")
        
        print(" Establishing connection to server...")
        print(" ✓ Connection established successfully")
            
        print("\n Please log in to continue:\n")
        session_active = True
        while session_active:
            # Login sequence
            username = input("Enter username: ")
            password = masked_input("Enter password: ")
            
            login_msg = CSmessage()
            login_msg.setType(REQS.LGIN)
            login_msg.addValue("username", username)
            login_msg.addValue("password", password)
            
            print(f"\n[DEBUG] Sending login request: {login_msg.marshal()}")
            pdu.send_message(login_msg)
            
            response = pdu.receive_message()
            print(f"[DEBUG] Received response: {response.marshal()}")
            
            if response and response.getValue("status") == "Login successful":
                print("Login successful!")
                
                # User session loop
                user_active = True
                while user_active:
                    print("\n╔════════════════════════╗")
                    print("║     MAIN MENU          ║")
                    print("╚════════════════════════╝")
                    print("1. Show Device Status")
                    print("2. Change Device Status")
                    print("3. Add New Device")  # New option
                    print("4. Logout")
                    print("5. Exit")
                    choice = input("Choose an option: ")
                    
                    if choice == "1":
                        # Show Device Status submenu
                        print("\n╔════════════════════════╗")
                        print("║   DEVICE STATUS MENU   ║")
                        print("╚════════════════════════╝")
                        print("1. By Room")
                        print("2. By Group")  # New option
                        print("3. By Device") # New option
                        print("4. All Devices")
                        list_choice = input("Choose an option: ")
                        
                        msg = CSmessage()
                        msg.setType(REQS.LIST)
                        
                        if list_choice == "1":  # By Room
                            room = input("Enter room name: ").strip()
                            msg.addValue("room", room)
                            msg.addValue("filter_type", "room")
                        elif list_choice == "2":  # By Group
                            group = input("Enter group name (e.g., lights, security): ").strip()
                            msg.addValue("group", group)
                            msg.addValue("filter_type", "group")
                        elif list_choice == "3":  # By Device
                            device = input("Enter device name: ").strip()
                            msg.addValue("device", device)
                            msg.addValue("filter_type", "device")
                        elif list_choice == "4":  # All Devices
                            msg.addValue("room", "all")
                            msg.addValue("filter_type", "all")
                        else:
                            print("Invalid option")
                            continue
                        
                        print(f"\n[DEBUG] Sending LIST request: {msg.marshal()}")
                        pdu.send_message(msg)
                        
                        print("[DEBUG] Waiting for server response...")
                        response = pdu.receive_message()
                        print(f"[DEBUG] Received response: {response.marshal()}")
                        
                        if response:
                            devices = response.getValue("devices")
                            display_device_info(devices)
                    
                    elif choice == "2":
                        # First, get the room list
                        room_msg = CSmessage()
                        room_msg.setType(REQS.LIST)
                        room_msg.addValue("room", "all")
                        room_msg.addValue("filter_type", "all")
                        
                        print(f"\n[DEBUG] Fetching available rooms and devices...")
                        pdu.send_message(room_msg)
                        
                        room_response = pdu.receive_message()
                        
                        # Display available rooms
                        if room_response:
                            devices_data = room_response.getValue("devices")
                            if isinstance(devices_data, str):
                                try:
                                    devices_data = json.loads(devices_data.replace("'", '"'))
                                except:
                                    print("[ERROR] Failed to parse device information")
                                    continue
                                    
                            print("\nAvailable Rooms:")
                            for i, room in enumerate([r for r in devices_data.keys() if r != "Home"], 1):
                                print(f"{i}. {room}")   
                            
                            # Add after the room display code in choice == "2" section
                            # First detect if Home with house_alarm exists
                            if "Home" in devices_data and "devices" in devices_data["Home"] and "house_alarm" in devices_data["Home"]["devices"]:
                                print("H. House Alarm (special)")  # Add as a special option
                            
                            room_idx = input("\nSelect room number: ")
                            
                            # Then add this after room selection in choice == "2" section
                            # Check if user selected the house alarm
                            if room_idx.lower() == "h":
                                print(f"Selected: House Alarm")
                                handle_house_alarm(pdu)
                                continue
                            
                            try:
                                # Get the list of rooms excluding "Home"
                                available_rooms = [r for r in devices_data.keys() if r != "Home"]
                                room_name = available_rooms[int(room_idx) - 1]
                                print(f"Selected room: {room_name}")
                                
                                # Display available devices in the room
                                print("\nAvailable Devices:")
                                room_devices = devices_data[room_name]["devices"]
                                for i, device in enumerate(room_devices.keys(), 1):
                                    device_type = room_devices[device].get("type", "Unknown")
                                    print(f"{i}. {device} ({device_type})")
                                
                                device_idx = input("\nSelect device number: ")
                                try:
                                    device_name = list(room_devices.keys())[int(device_idx) - 1]
                                    device_info = room_devices[device_name]
                                    device_type = device_info.get("type", "Unknown")
                                    current_status = device_info.get("status", "Unknown")
                                    current_brightness = device_info.get("brightness", None)
                                    current_color = device_info.get("color", None)
                                    
                                    print(f"\nSelected device: {device_name}")
                                    print(f"Type: {device_type}")
                                    print(f"Current status: {current_status}")
                                    
                                    # Special handling based on device type
                                    if device_type == "WindowBlind":
                                        handle_window_blind(pdu, room_name, device_name)
                                    elif device_type == "Light":
                                        handle_light(pdu, room_name, device_name, current_status, current_brightness, current_color)
                                    elif device_type == "Lock":
                                        # Special handling for locks with PIN verification
                                        lock_option = input("\nLock Controls:\n1. Lock\n2. Unlock\nChoose an option: ")
                                        
                                        new_status = ""
                                        if lock_option == "1":
                                            new_status = "locked"
                                        elif lock_option == "2":
                                            new_status = "unlocked"
                                        else:
                                            print("Invalid option")
                                            continue
                                        
                                        pin = input("Enter PIN: ")
                                        
                                        msg = CSmessage()
                                        msg.setType(REQS.CHG_STATUS)
                                        msg.addValue("room", room_name)
                                        msg.addValue("device", device_name)
                                        msg.addValue("status", new_status)
                                        msg.addValue("pin", pin)
                                        
                                        print(f"\n[DEBUG] Sending CHG_STATUS request: {msg.marshal()}")
                                        pdu.send_message(msg)
                                        
                                        print("[DEBUG] Waiting for server response...")
                                        response = pdu.receive_message()
                                        print(f"[DEBUG] Received response: {response.marshal()}")
                                        
                                        if response:
                                            status = response.getValue("status")
                                            message = response.getValue("message")
                                            print(f"\nResult: {status}")
                                            if message:
                                                print(f"Message: {message}")
                                    else:
                                        # Generic device handling
                                        new_status = input("\nEnter new status: ")
                                        
                                        msg = CSmessage()
                                        msg.setType(REQS.CHG_STATUS)
                                        msg.addValue("room", room_name)
                                        msg.addValue("device", device_name)
                                        msg.addValue("status", new_status)
                                        
                                        if "lock" in device_name.lower() or device_type == "Lock":
                                            pin = input("Enter PIN: ")
                                            msg.addValue("pin", pin)
                                        
                                        print(f"\n[DEBUG] Sending CHG_STATUS request: {msg.marshal()}")
                                        pdu.send_message(msg)
                                        
                                        print("[DEBUG] Waiting for server response...")
                                        response = pdu.receive_message()
                                        print(f"[DEBUG] Received response: {response.marshal()}")
                                        
                                        if response:
                                            status = response.getValue("status")
                                            message = response.getValue("message")
                                            print(f"\nResult: {status}")
                                            if message:
                                                print(f"Message: {message}")
                                                
                                except (ValueError, IndexError):
                                    print("Invalid device selection")
                            except (ValueError, IndexError):
                                print("Invalid room selection")
                    
                    elif choice == "3":  # Add new device
                        # First, get rooms
                        room_msg = CSmessage()
                        room_msg.setType(REQS.LIST)
                        room_msg.addValue("room", "all")
                        room_msg.addValue("filter_type", "all")
                        
                        print(f"\n[DEBUG] Fetching available rooms...")
                        pdu.send_message(room_msg)
                        
                        room_response = pdu.receive_message()
                        
                        # Display available rooms
                        if room_response:
                            devices_data = room_response.getValue("devices")
                            if isinstance(devices_data, str):
                                try:
                                    devices_data = json.loads(devices_data.replace("'", '"'))
                                except:
                                    print("[ERROR] Failed to parse device information")
                                    continue
                                    
                            print("\nAvailable Rooms:")
                            for i, room in enumerate(devices_data.keys(), 1):
                                print(f"{i}. {room}")
                            
                            room_idx = input("\nSelect room number: ")
                            try:
                                room_name = list(devices_data.keys())[int(room_idx) - 1]
                                
                                print("\nDevice Types:")
                                print("1. Light")
                                print("2. Window Blind")
                                print("3. Lock")
                                
                                device_type_idx = input("Select device type: ")
                                device_types = ["Light", "WindowBlind", "Lock"]
                                try:
                                    device_type = device_types[int(device_type_idx) - 1]
                                    
                                    device_name = input("\nEnter device name: ")
                                    
                                    # Create the new device message
                                    msg = CSmessage()
                                    msg.setType(REQS.ADD_DEVICE)
                                    msg.addValue("room", room_name)
                                    msg.addValue("device_name", device_name)
                                    msg.addValue("device_type", device_type)
                                    
                                    # Add specific properties based on device type
                                    if device_type == "Light":
                                        msg.addValue("brightness", 50)  # Default brightness
                                        msg.addValue("color", "white")  # Default color
                                    elif device_type == "Lock":
                                        pin = input("Enter PIN code for the lock: ")
                                        msg.addValue("pin_codes", [pin])  # Initial PIN code
                                    
                                    # Send the request
                                    print(f"\n[DEBUG] Sending ADD_DEVICE request...")
                                    pdu.send_message(msg)
                                    
                                    response = pdu.receive_message()
                                    
                                    if response:
                                        status = response.getValue("status") 
                                        print(f"\nResult: {status}")
                                        
                                except (ValueError, IndexError):
                                    print("Invalid device type selection")
                                    
                            except (ValueError, IndexError):
                                print("Invalid room selection")
                                
                    elif choice == "4":  # Logout
                        msg = CSmessage()
                        msg.setType(REQS.LOUT)
                        
                        print(f"\n[DEBUG] Sending LOUT request: {msg.marshal()}")
                        pdu.send_message(msg)
                        
                        response = pdu.receive_message()
                        print(f"[DEBUG] Received response: {response.marshal()}")
                        
                        print("Logged out successfully")
                        user_active = False  # Exit user session but not main session
                    
                    elif choice == "5":  # Exit application
                        msg = CSmessage()
                        msg.setType(REQS.EXIT)
                        
                        print(f"\n[DEBUG] Sending EXIT request: {msg.marshal()}")
                        pdu.send_message(msg)
                        
                        response = pdu.receive_message()
                        print(f"[DEBUG] Received response: {response.marshal()}")
                        
                        print("Exiting...")
                        session_active = False  # Exit both loops
                        break
            else:
                print(f"Login failed: {response.getValue('status') if response else 'No response from server'}")
                retry = input("Try again? (y/n): ")
                if retry.lower() != 'y':
                    session_active = False
        
    except socket.timeout:
        print("[ERROR] Connection timed out. Server might be unresponsive.")
    except ConnectionRefusedError:
        print("[ERROR] Connection refused. Is the server running?")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
    finally:
        if 'client' in locals():
            try:
                client.close()
                print("[DEBUG] Connection closed")
            except:
                pass

if __name__ == "__main__":
    main()