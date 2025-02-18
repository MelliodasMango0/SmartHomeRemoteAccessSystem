class Device:
    def __init__(self, device_id: str, device_type: str, room_id: str, home_id: str):
        self.device_id = device_id
        self.device_type = device_type
        self.status = "off"
        self.room_id = room_id
        self.home_id = home_id
    
    def get_status(self):
        return self.status