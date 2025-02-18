from models.device import Device

class Alarm(Device):
    def __init__(self, device_id, room_id, home_id, pin_code: str):
        super().__init__(device_id, "Alarm", room_id, home_id)
        self.is_armed = False
        self.pin_code = pin_code
    
    def arm(self):
        self.is_armed = True
    
    def disarm(self, pin: str):
        if pin == self.pin_code:
            self.is_armed = False
            return True
        return False