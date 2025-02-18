from models.device import Device

class WindowBlind(Device):
    def __init__(self, device_id, room_id, home_id):
        super().__init__(device_id, "WindowBlind", room_id, home_id)
        self.is_up = True
        self.is_open = True
    
    def raise_blinds(self):
        self.is_up = True
    
    def lower_blinds(self):
        self.is_up = False
    
    def open_blinds(self):
        self.is_open = True
    
    def close_blinds(self):
        self.is_open = False