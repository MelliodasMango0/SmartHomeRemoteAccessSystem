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
def get_device_status(room_name=None, device_name=None):
    data = load_data()
    print(f"[DEBUG] get_device_status() called with room={room_name}, device={device_name}")
    
    try:
        # Make sure we have the expected data structure
        if "home" not in data or "rooms" not in data["home"]:
            return {"error": "Invalid data structure"}
            
        if room_name and device_name:
            # Return specific device in specific room
            if room_name in data["home"]["rooms"] and device_name in data["home"]["rooms"][room_name]["devices"]:
                return data["home"]["rooms"][room_name]["devices"][device_name]
            else:
                return {"error": f"Device '{device_name}' in room '{room_name}' not found"}
                
        elif room_name:
            # Return all devices in specific room
            if room_name in data["home"]["rooms"]:
                return data["home"]["rooms"][room_name]["devices"]
            else:
                return {"error": f"Room '{room_name}' not found"}
                
        else:
            # Return all rooms
            return data["home"]["rooms"]
    
    except KeyError as e:
        print(f"[ERROR] KeyError in get_device_status: {e}")
        return {"error": "Data structure error"}
    except Exception as e:
        print(f"[ERROR] Unexpected error in get_device_status: {e}")
        return {"error": "An unexpected error occurred"}

def change_device_status(room, device, new_status, pin=None):
    data = load_data()
    print(f"[DEBUG] Attempting to change {device} in {room} to {new_status}")
    
    try:
        # Validate room exists
        if room not in data["home"]["rooms"]:
            print(f"[ERROR] Room '{room}' not found")
            return {"error": f"Room '{room}' not found"}
            
        # Validate device exists
        if device not in data["home"]["rooms"][room]["devices"]:
            print(f"[ERROR] Device '{device}' not found in room '{room}'")
            return {"error": f"Device '{device}' not found in room '{room}'"}
            
        # Check if device requires PIN
        device_info = data["home"]["rooms"][room]["devices"][device]
        if "requires_pin" in device_info and device_info["requires_pin"] and not pin:
            return {"error": "PIN required for this device"}
            
        # Update device status
        data["home"]["rooms"][room]["devices"][device]["status"] = new_status
        data["home"]["rooms"][room]["devices"][device]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        save_data()
        print(f"[DEBUG] Successfully changed {device} status to {new_status}")
        return {"success": f"{device} status changed to {new_status}"}
        
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
                    room = message.getValue("room")
                    print(f"[DEBUG] Processing LIST request for room: {room}")
                    
                    # Fix for handling "all" rooms properly
                    if room == "all":
                        device_status = get_device_status(None)
                    else:
                        device_status = get_device_status(room)
                        
                    response.addValue("devices", device_status)
                    response.addValue("status", "Success")

            elif message.getType() == REQS.CHG_STATUS:
                if not logged_in:
                    print("[SERVER] Unauthorized CHG_STATUS attempt")
                    response.addValue("status", "Unauthorized")
                else:
                    room = message.getValue("room")
                    device = message.getValue("device")
                    new_status = message.getValue("status")
                    pin = message.getValue("pin") if "pin" in message._data else None

                    print(f"[DEBUG] User '{username}' changing {device} in {room} to {new_status}")
                    result = change_device_status(room, device, new_status, pin)

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