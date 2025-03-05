import socket
import time
import getpass
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from messaging.csmessage import CSmessage, REQS
from messaging.cspdu import SmartHomePDU as CSpdu

HOST = "127.0.0.1"
PORT = 5000

def main():
    print("\n[SMART HOME APP]")
    
    # Create a single socket connection for the entire session
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(10)  # Longer timeout for entire session
        client.connect((HOST, PORT))
        pdu = CSpdu(client)
        
        # Login sequence
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
        
        # Create login message
        login_msg = CSmessage()
        login_msg.setType(REQS.LGIN)
        login_msg.addValue("username", username)
        login_msg.addValue("password", password)
        
        # Send login request
        print(f"\n[DEBUG] Sending login request: {login_msg.marshal()}")
        pdu.send_message(login_msg)
        
        # Get response
        print("[DEBUG] Waiting for server response...")
        response = pdu.receive_message()
        print(f"[DEBUG] Received response: {response.marshal()}")
        
        if response and response.getValue("status") == "Login successful":
            print("Login successful!")
            
            # Main application loop
            while True:
                print("\n1. Show Device Status")
                print("2. Change Device Status")
                print("3. Logout")
                print("4. Exit")
                choice = input("Choose an option: ")
                
                if choice == "1":
                    room = input("Enter room name (or 'all'): ").strip()
                    msg = CSmessage()
                    msg.setType(REQS.LIST)
                    msg.addValue("room", room)
                    
                    print(f"\n[DEBUG] Sending LIST request: {msg.marshal()}")
                    pdu.send_message(msg)
                    
                    print("[DEBUG] Waiting for server response...")
                    response = pdu.receive_message()
                    print(f"[DEBUG] Received response: {response.marshal()}")
                    
                    if response:
                        devices = response.getValue("devices")
                        if devices:
                            print("\nDevice Status:")
                            print(json.dumps(devices, indent=2))
                        else:
                            print("No devices found or unauthorized access")
                
                elif choice == "2":
                    room = input("Enter room: ")
                    device = input("Enter device: ")
                    new_status = input("Enter new status: ")
                    
                    msg = CSmessage()
                    msg.setType(REQS.CHG_STATUS)
                    msg.addValue("room", room)
                    msg.addValue("device", device)
                    msg.addValue("status", new_status)
                    
                    if "lock" in device.lower():
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
                
                elif choice == "3":
                    msg = CSmessage()
                    msg.setType(REQS.LOUT)
                    
                    print(f"\n[DEBUG] Sending LOUT request: {msg.marshal()}")
                    pdu.send_message(msg)
                    
                    print("[DEBUG] Waiting for server response...")
                    response = pdu.receive_message()
                    print(f"[DEBUG] Received response: {response.marshal()}")
                    
                    print("Logged out successfully")
                    break
                
                elif choice == "4":
                    msg = CSmessage()
                    msg.setType(REQS.EXIT)
                    
                    print(f"\n[DEBUG] Sending EXIT request: {msg.marshal()}")
                    pdu.send_message(msg)
                    
                    print("[DEBUG] Waiting for server response...")
                    response = pdu.receive_message()
                    print(f"[DEBUG] Received response: {response.marshal()}")
                    
                    print("Exiting...")
                    break
                
                else:
                    print("Invalid option, please try again.")
        else:
            print(f"Login failed: {response.getValue('status') if response else 'No response from server'}")
    
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
    # Add json import at the top of the file for pretty printing device status
    import json
    main()