from models.room import Room

class Home:
    def __init__(self, home_id: str, address: str, owner, rooms: list):
        self.home_id = home_id
        self.address = address
        self.owner = owner
        self.rooms = rooms  # List of Room objects, provided at initialization

    def list_rooms(self):
        """Returns a list of room names"""
        return [room.name for room in self.rooms]

    def list_devices(self):
        """Returns a list of all devices in the home"""
        devices = []
        for room in self.rooms:
            devices.extend(room.list_devices())  # Using Room's list_devices() method
        return devices
