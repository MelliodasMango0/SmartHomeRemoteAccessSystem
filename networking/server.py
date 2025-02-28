import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import socket
from datetime import datetime
from messaging.csmessage import CSmessage, REQS
from messaging.cspdu import SmartHomePDU as CSpdu

# Track login status and device states
logged_in = False
devices = {
    "light": {"status": "off", "brightness": 100, "color": "255,255,255"},
    "lock": {"status": "unlocked"},
    "alarm": {"status": "disarmed", "code": "1234"}
}

def log_message(event, details):
    """Logs server events with timestamps."""
    print(f"\n[SERVER] ---- {event} ----")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    for key, value in details.items():
        print(f"{key}: {value}")

def handle_client(conn, addr):
    """Handles client requests and processes responses."""
    global logged_in
    pdu = CSpdu(conn)

    try:
        log_message("New Connection", {"Client Address": addr})
        
        message = pdu.receive_message()
        log_message("Received Request", {"Raw Message Data": message._data, "Marshaled": message.marshal()})

        response = CSmessage()
        response.setType(message.getType())

        if message.getType() == REQS.LGIN:
            username = message.getValue("username")
            password = message.getValue("password")

            if logged_in:
                response.addValue("status", "Already logged in")
            elif username == "admin" and password == "pass123":
                logged_in = True
                response.addValue("status", "Login successful")
            else:
                response.addValue("status", "Invalid credentials")

        elif message.getType() == REQS.LOUT:
            if logged_in:
                logged_in = False
                response.addValue("status", "Logged out successfully")
            else:
                response.addValue("status", "User not logged in")

        elif message.getType() == REQS.LIST:
            if not logged_in:
                response.addValue("status", "Unauthorized request")
            else:
                device_list = "|".join([f"{name},{','.join(f'{k}={v}' for k,v in info.items())}" for name, info in devices.items()])
                response.addValue("status", "OK")
                response.addValue("devices", device_list)

        elif message.getType() == REQS.CHG_STATUS:
            if not logged_in:
                response.addValue("status", "Unauthorized request")
            else:
                device_name = message.getValue("device")
                if device_name in devices:
                    for key, value in message._data.items():
                        if key not in ["type", "device"]:
                            devices[device_name][key] = value
                    response.addValue("status", f"{device_name} updated successfully")
                else:
                    response.addValue("status", "Invalid device")

        else:
            response.addValue("status", "Unknown request type")

        log_message("Sending Response", {"Raw Response Data": response._data, "Marshaled": response.marshal()})
        pdu.send_message(response)

    except Exception as e:
        log_message("Error", {"Message": str(e)})

    finally:
        log_message("Connection Closed", {"Client Address": addr})
        conn.close()


def start_server():
    """Starts the Smart Home Remote Access Server."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", 5000))
    server_socket.listen(5)
    print("[SERVER] Server started on 127.0.0.1:5000")

    while True:
        conn, addr = server_socket.accept()
        handle_client(conn, addr)

if __name__ == "__main__":
    start_server()
