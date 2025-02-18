from models.device import Device

class Lock(Device):
    def __init__(self, device_id, room_id, home_id, pin_codes):
        super().__init__(device_id, "Lock", room_id, home_id)
        self.is_locked = True
        self.pin_codes = pin_codes
    
    def lock(self):
        self.is_locked = True
    
    def unlock(self, pin: str):
        if pin in self.pin_codes:
            self.is_locked = False
            return True
        return False