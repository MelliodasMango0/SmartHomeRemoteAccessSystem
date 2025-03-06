import sys
import os
import json
import socket
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from messaging.csmessage import CSmessage, REQS
from messaging.cspdu import SmartHomePDU as CSpdu

# Define JSON file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "..", "smart_home.json")

cached_data = None

def load_data():
    global cached_data
    if cached_data is None:  # Load only once
        try:
            with open(DATA_FILE, "r") as file:
                cached_data = json.load(file)
                print("[DEBUG] JSON loaded successfully")
        except FileNotFoundError:
            print("[ERROR] JSON file missing, creating a new one.")
            cached_data = {"users": {}, "home": {"rooms": {}}}
            save_data()  # Create the file
    return cached_data

def save_data():
    global cached_data
    if cached_data:
        with open(DATA_FILE, "w") as file:
            json.dump(cached_data, file, indent=4)
        print("[DEBUG] JSON saved successfully")

# Server-side authentication
def authenticate_user(username, password):
    data = load_data()
    return username in data["users"] and data["users"][username]["password"] == password

# Fetch device status
def get_device_status(room_name=None, device_name=None, group=None):
    """
    Get device status filtering by room, device, or group.
    """
    data = load_data()
    result = {}
    
    try:
        # Special handling for house_alarm
        house_alarm = data["home"]["special_devices"]["house_alarm"] if "special_devices" in data["home"] and "house_alarm" in data["home"]["special_devices"] else None
        
        if room_name and device_name:
            # Get specific device in specific room
            if room_name in data["home"]["rooms"] and device_name in data["home"]["rooms"][room_name]["devices"]:
                result[room_name] = {"devices": {device_name: data["home"]["rooms"][room_name]["devices"][device_name]}}
            # Special case for house_alarm
            elif room_name == "Home" and device_name == "house_alarm" and house_alarm:
                result["Home"] = {"devices": {"house_alarm": house_alarm}}
            
        elif room_name and room_name != "all":
            # Get all devices in specific room
            if room_name in data["home"]["rooms"]:
                result[room_name] = data["home"]["rooms"][room_name]
            # Special case for house_alarm
            elif room_name == "Home" and house_alarm:
                result["Home"] = {"devices": {"house_alarm": house_alarm}}
                
        elif group:
            # Get all devices of a specific group/type
            for room_name, room in data["home"]["rooms"].items():
                for device_name, device in room["devices"].items():
                    if device.get("type", "").lower() == group.lower() or group.lower() in device.get("groups", []):
                        if room_name not in result:
                            result[room_name] = {"devices": {}}
                        result[room_name]["devices"][device_name] = device
            
            # Include house alarm if group matches
            if house_alarm and (house_alarm.get("type", "").lower() == group.lower() or group.lower() in house_alarm.get("groups", [])):
                if "Home" not in result:
                    result["Home"] = {"devices": {}}
                result["Home"]["devices"]["house_alarm"] = house_alarm
                        
        elif device_name:
            # Get specific device in any room
            for room_name, room in data["home"]["rooms"].items():
                if device_name in room["devices"]:
                    if room_name not in result:
                        result[room_name] = {"devices": {}}
                    result[room_name]["devices"][device_name] = room["devices"][device_name]
            
            # Include house alarm if name matches
            if device_name == "house_alarm" and house_alarm:
                if "Home" not in result:
                    result["Home"] = {"devices": {}}
                result["Home"]["devices"]["house_alarm"] = house_alarm
                    
        else:
            # Get all devices in all rooms
            result = data["home"]["rooms"]
            
            # Add house_alarm to results
            if house_alarm:
                if "Home" not in result:
                    result["Home"] = {"devices": {}}
                result["Home"]["devices"]["house_alarm"] = house_alarm
    
    except KeyError as e:
        print(f"[ERROR] KeyError in get_device_status: {e}")
        return {"error": "Data structure error"}
    except Exception as e:
        print(f"[ERROR] Unexpected error in get_device_status: {e}")
        return {"error": "An unexpected error occurred"}
        
    return result

def change_house_alarm_status(new_status, pin=None):
    """Changes the status of the house alarm"""
    data = load_data()
    changes_made = []
    
    try:
        if "special_devices" not in data["home"] or "house_alarm" not in data["home"]["special_devices"]:
            return {"error": "House alarm not found"}
            
        alarm_info = data["home"]["special_devices"]["house_alarm"]
        
        # Check PIN for the alarm
        if pin != alarm_info.get("pin"):
            return {"error": "Invalid PIN code for house alarm"}
        
        # Update alarm status
        if new_status:
            old_status = alarm_info.get("status", "unknown")
            data["home"]["special_devices"]["house_alarm"]["status"] = new_status
            changes_made.append(f"status from {old_status} to {new_status}")
        
        # Update last_updated timestamp
        data["home"]["special_devices"]["house_alarm"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save changes
        save_data()
        
        print(f"[DEBUG] Successfully changed house_alarm: {', '.join(changes_made)}")
        
        # Create a detailed success message
        if changes_made:
            success_message = f"House alarm updated: {', '.join(changes_made)}"
        else:
            success_message = "No changes made to house alarm"
            
        return {"success": success_message}
        
    except Exception as e:
        print(f"[ERROR] Unexpected error in change_house_alarm_status: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

def change_device_status(room, device, new_status, pin=None, brightness=None, color=None):
    data = load_data()
    print(f"[DEBUG] Attempting to change {device} in {room} to {new_status}")
    print(f"[DEBUG] Additional properties: brightness={brightness}, color={color}, pin={pin}")
    
    changes_made = []
    
    try:
        # Validate room exists
        if room not in data["home"]["rooms"]:
            print(f"[ERROR] Room '{room}' not found")
            return {"error": f"Room '{room}' not found"}
            
        # Validate device exists
        if device not in data["home"]["rooms"][room]["devices"]:
            print(f"[ERROR] Device '{device}' not found in room '{room}'")
            return {"error": f"Device '{device}' not found in room '{room}'"}
            
        # Get device info
        device_info = data["home"]["rooms"][room]["devices"][device]
        
        # Check PIN for locks
        if device_info.get("type") == "Lock":
            if new_status in ["unlock", "unlocked"] and not pin:
                return {"error": "PIN required for this lock"}
            
            # Check if PIN is valid
            pin_codes = device_info.get("pin_codes", [])
            if pin and pin not in pin_codes:
                print(f"[ERROR] Invalid PIN provided: {pin}")
                return {"error": "Invalid PIN code"}
        
        # Update device status
        if new_status:
            old_status = device_info.get("status", "unknown")
            data["home"]["rooms"][room]["devices"][device]["status"] = new_status
            changes_made.append(f"status from {old_status} to {new_status}")
        
        # Update brightness if provided (for lights)
        if brightness is not None and device_info.get("type") == "Light":
            try:
                brightness_val = int(brightness)
                if 0 <= brightness_val <= 100:
                    old_brightness = device_info.get("brightness", 0)
                    data["home"]["rooms"][room]["devices"][device]["brightness"] = brightness_val
                    changes_made.append(f"brightness from {old_brightness} to {brightness_val}")
                    print(f"[DEBUG] Updated brightness to {brightness_val}")
                else:
                    print(f"[ERROR] Brightness out of range: {brightness_val}")
                    return {"error": "Brightness must be between 0-100"}
            except ValueError:
                print(f"[ERROR] Invalid brightness value: {brightness}")
                return {"error": "Invalid brightness value"}
        
        # Update color if provided (for lights)
        if color is not None and device_info.get("type") == "Light":
            old_color = device_info.get("color", "unknown")
            data["home"]["rooms"][room]["devices"][device]["color"] = color
            changes_made.append(f"color from {old_color} to {color}")
            print(f"[DEBUG] Updated color to {color}")
        
        # Update last_updated timestamp
        data["home"]["rooms"][room]["devices"][device]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # IMPORTANT: Save the updated data to JSON file
        save_data()
        
        print(f"[DEBUG] Successfully changed {device}: {', '.join(changes_made)}")
        
        # Create a detailed success message
        if changes_made:
            success_message = f"{device} updated: {', '.join(changes_made)}"
        else:
            success_message = f"No changes made to {device}"
            
        return {"success": success_message}
        
    except KeyError as e:
        print(f"[ERROR] KeyError in change_device_status: {e}")
        return {"error": "Data structure error"}
    except Exception as e:
        print(f"[ERROR] Unexpected error in change_device_status: {e}")
        return {"error": "An unexpected error occurred"}

def handle_client(conn, addr):
    """Handles client communication over TCP"""
    pdu = CSpdu(conn)
    logged_in = False
    username = None

    try:
        print(f"\n[SERVER] Connection from {addr}")

        while True:
            print("[DEBUG] Waiting for message from client...")
            try:
                message = pdu.receive_message()
            except ConnectionError:
                print("[ERROR] Connection lost. Closing client session.")
                break
            except Exception as e:
                print(f"[ERROR] Failed to receive message: {e}")
                break

            print(f"[DEBUG] Received message: {message.marshal()}")

            response = CSmessage()
            response.setType(message.getType())

            if message.getType() == REQS.LGIN:
                username = message.getValue("username")
                password = message.getValue("password")

                if logged_in:
                    response.addValue("status", "Already logged in")
                elif authenticate_user(username, password):
                    logged_in = True
                    response.addValue("status", "Login successful")
                    print(f"[SERVER] User '{username}' logged in successfully")
                else:
                    response.addValue("status", "Invalid credentials")
                    print(f"[SERVER] Login failed for user '{username}'")

            elif message.getType() == REQS.LOUT:
                if logged_in:
                    print(f"[SERVER] User '{username}' logged out")
                    logged_in = False
                    username = None
                    response.addValue("status", "Logged out successfully")
                else:
                    response.addValue("status", "Not logged in")

            elif message.getType() == REQS.LIST:
                if not logged_in:
                    print("[SERVER] Unauthorized LIST attempt")
                    response.addValue("status", "Unauthorized")
                else:
                    filter_type = message.getValue("filter_type") if "filter_type" in message._data else "room"
                    
                    if filter_type == "room":
                        room = message.getValue("room")
                        print(f"[DEBUG] Processing LIST request for room: {room}")
                        
                        # Handle "all" rooms properly
                        if room == "all":
                            device_status = get_device_status(None)
                        else:
                            device_status = get_device_status(room_name=room)
                            
                    elif filter_type == "group":
                        group = message.getValue("group")
                        print(f"[DEBUG] Processing LIST request for group: {group}")
                        device_status = get_device_status(group=group)
                        
                    elif filter_type == "device":
                        device = message.getValue("device")
                        print(f"[DEBUG] Processing LIST request for device: {device}")
                        device_status = get_device_status(device_name=device)
                        
                    else:  # "all" or default
                        print(f"[DEBUG] Processing LIST request for all devices")
                        device_status = get_device_status()
                        
                    response.addValue("devices", device_status)
                    response.addValue("status", "Success")

            elif message.getType() == REQS.CHG_STATUS:
                if not logged_in:
                    print("[SERVER] Unauthorized CHG_STATUS attempt")
                    response.addValue("status", "Unauthorized")
                else:
                    device = message.getValue("device")
                    
                    # Special handling for house alarm
                    if device == "house_alarm":
                        new_status = message.getValue("status")
                        pin = message.getValue("pin") if "pin" in message._data else None
                        
                        print(f"[DEBUG] User '{username}' changing house alarm to {new_status}")
                        result = change_house_alarm_status(new_status, pin)
                        
                        if "success" in result:
                            response.addValue("status", "Success")
                            response.addValue("message", result["success"])
                        else:
                            response.addValue("status", "Error")
                            response.addValue("message", result["error"])
                    else:
                        # Existing logic for other devices
                        room = message.getValue("room")
                        new_status = message.getValue("status")
                        pin = message.getValue("pin") if "pin" in message._data else None
                        brightness = message.getValue("brightness") if "brightness" in message._data else None
                        color = message.getValue("color") if "color" in message._data else None

                        print(f"[DEBUG] User '{username}' changing {device} in {room} to {new_status}")
                        print(f"[DEBUG] Additional properties: brightness={brightness}, color={color}, pin={pin}")
                        
                        result = change_device_status(room, device, new_status, pin, brightness, color)

                        if "success" in result:
                            response.addValue("status", "Success")
                            response.addValue("message", result["success"])
                        else:
                            response.addValue("status", "Error")
                            response.addValue("message", result["error"])

            elif message.getType() == REQS.SRCH:
                if not logged_in:
                    response.addValue("status", "Unauthorized")
                else:
                    response.addValue("status", "Feature not implemented yet")

            elif message.getType() == REQS.EXIT:
                print(f"[SERVER] User '{username}' requested to exit")
                response.addValue("status", "Goodbye")
                pdu.send_message(response)
                break

            else:
                print(f"[ERROR] Unknown request type: {message.getType()}")
                response.addValue("status", "Unknown request type")

            print(f"[DEBUG] Sending response: {response.marshal()}")  
            pdu.send_message(response)

    except Exception as e:
        print(f"[SERVER ERROR] {e}")

    finally:
        conn.close()
        print(f"[SERVER] Connection closed with {addr}")


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(("127.0.0.1", 5000))
        server_socket.listen(5)
        print("[SERVER] Running on 127.0.0.1:5000")

        while True:
            try:
                conn, addr = server_socket.accept()
                # This will block until this client is done
                handle_client(conn, addr)
            except KeyboardInterrupt:
                print("\n[SERVER] Shutting down gracefully...")
                break
            
    except Exception as e:
        print(f"[SERVER ERROR] {e}")
    finally:
        server_socket.close()
        print("[SERVER] Server shut down")
        sys.exit(0)

if __name__ == "__main__":
    # Create data file if it doesn't exist
    load_data()
    start_server()