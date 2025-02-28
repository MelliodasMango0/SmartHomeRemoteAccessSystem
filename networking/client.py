import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import socket
from messaging.csmessage import CSmessage, REQS
from messaging.cspdu import SmartHomePDU as CSpdu
import time

HOST = "127.0.0.1"
PORT = 5000

def send_request(request_type, values={}):
    """Send a request to the server and print detailed response logs."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        pdu = CSpdu(client)

        message = CSmessage()
        message.setType(request_type)

        for key, value in values.items():
            message.addValue(key, value)

        print(f"\n[CLIENT] ---- Sending Request ----")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Raw Message Data: {message._data}")
        print(f"Marshaled: {message.marshal()}\n")

        pdu.send_message(message)

        response = pdu.receive_message()
        print(f"[CLIENT] ---- Received Response ----")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Raw Response Data: {response._data}")
        print(f"Marshaled: {response.marshal()}\n")

if __name__ == "__main__":
    print("\n===== Running Full Test Suite =====")

    print("\n[TEST] Successful Login")
    send_request(REQS.LGIN, {"username": "admin", "password": "pass123"})

    print("\n[TEST] Unsuccessful Login (Invalid Password)")
    send_request(REQS.LGIN, {"username": "admin", "password": "wrongpass"})

    print("\n[TEST] Login Attempt When Already Logged In")
    send_request(REQS.LGIN, {"username": "admin", "password": "pass123"})

    print("\n[TEST] Listing Devices")
    send_request(REQS.LIST)

    print("\n[TEST] Changing Device Status (Turning Light ON)")
    send_request(REQS.CHG_STATUS, {"device": "light", "status": "on"})

    print("\n[TEST] Setting Device Attributes (Brightness and Color)")
    send_request(REQS.CHG_STATUS, {"device": "light", "brightness": "75", "color": "255,0,0"})

    print("\n[TEST] Attempting to Change Status Without Logging In")
    send_request(REQS.CHG_STATUS, {"device": "lock", "status": "locked"})

    print("\n[TEST] Logout")
    send_request(REQS.LOUT)

    print("\n[TEST] Sending an Unknown Request Type")
    send_request(999, {"param": "unknown"})

    print("\n[TEST] Sending a Request With Missing Parameters")
    send_request(REQS.CHG_STATUS, {})

    print("\n[TEST] Handling Large Message Payloads")
    send_request(REQS.CHG_STATUS, {"device": "light", "brightness": "100", "color": "255,255,255", "extra_data": "x" * 500})

    print("\n===== Full Test Suite Completed =====")


