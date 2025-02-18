from models.room import Room

class Home:
    def __init__(self, home_id: str, address: str, owner):
        self.home_id = home_id
        self.address = address
        self.owner = owner
        self.rooms = []

    def list_rooms(self):
        return self.rooms
    
    def list_devices(self):
        devices = []
        for room in self.rooms:
            devices.extend(room.devices)
        return devices