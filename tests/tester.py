import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.home import Home
from models.room import Room
from models.light import Light
from models.window_blind import WindowBlind
from models.lock import Lock
from models.alarm import Alarm
from models.user import User

from messaging.csmessage import CSmessage, REQS
from messaging.cspdu import SmartHomePDU

# Simulate user and home creation
user = User("admin", "pass123")
home = Home("home1", "123 Main St", user)

# Create rooms and add devices
living_room = Room("room1", "Living Room", home.home_id)
bedroom = Room("room2", "Bedroom", home.home_id)

# Devices
light1 = Light("light1", living_room.room_id, home.home_id)
blind1 = WindowBlind("blind1", living_room.room_id, home.home_id)
lock1 = Lock("lock1", living_room.room_id, home.home_id, ["1234", "5678"])
alarm1 = Alarm("alarm1", bedroom.room_id, home.home_id, "4321")

# Add devices to rooms
living_room.devices.extend([light1, blind1, lock1])
bedroom.devices.append(alarm1)
home.rooms.extend([living_room, bedroom])

# **Testing Data Model Actions**
print("===== DATA MODEL TESTING =====")
light1.turn_on()
print(f"Light Status: {light1.get_status()}")
blind1.lower_blinds()
print(f"Blind is up: {blind1.is_up}")
unlock_status = lock1.unlock("1234")
print(f"Lock unlocked with correct PIN: {unlock_status}")
alarm_status = alarm1.disarm("4321")
print(f"Alarm disarmed with correct PIN: {alarm_status}")

# **Testing Application Protocol Message**
print("\n===== APPLICATION PROTOCOL MESSAGE TESTING =====")

# Simulate client message for turning on the light
msg_turn_on = CSmessage()
msg_turn_on.setType(REQS.TURN_ON)
msg_turn_on.addValue("device", "light")
msg_turn_on.addValue("room", "Living Room")

# Marshal and display
marshaled = msg_turn_on.marshal()
print(f"Marshaled TURN_ON Message: {marshaled}")

# Unmarshal the message
msg_received = CSmessage()
msg_received.unmarshal(marshaled)
print(f"Unmarshaled Message: {msg_received.getValue('device')} in {msg_received.getValue('room')}")

# Simulate server-side processing
if msg_received.getValue("device") == "light" and msg_received.getValue("room") == "Living Room":
    light1.turn_on()
    print(f"[Server Response] Light status in Living Room: {light1.get_status()}")

# **Simulate Lock Command**
msg_lock = CSmessage()
msg_lock.setType(REQS.UNLOCK)
msg_lock.addValue("device", "lock")
msg_lock.addValue("room", "Living Room")
msg_lock.addValue("pin", "1234")

marshaled_lock = msg_lock.marshal()
print(f"\nMarshaled UNLOCK Message: {marshaled_lock}")

msg_lock_received = CSmessage()
msg_lock_received.unmarshal(marshaled_lock)

# Server response simulation
pin_entered = msg_lock_received.getValue("pin")
if lock1.unlock(pin_entered):
    print(f"[Server Response] Lock status in Living Room: Unlocked")
else:
    print(f"[Server Response] Lock status in Living Room: Locked (Invalid PIN)")

# **Generate Sample Output**
print("\n===== FINAL OUTPUT =====")
print(f"Light Status: {light1.get_status()}")
print(f"Blind Position: {'Up' if blind1.is_up else 'Down'}")
print(f"Lock Status: {'Locked' if lock1.is_locked else 'Unlocked'}")
print(f"Alarm Status: {'Armed' if alarm1.is_armed else 'Disarmed'}")
