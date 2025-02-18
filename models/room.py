from models.device import Device

class Room:
    def __init__(self, room_id: str, name: str, home_id: str):
        self.room_id = room_id
        self.name = name
        self.home_id = home_id
        self.devices = []

    def list_devices(self):
        return self.devices