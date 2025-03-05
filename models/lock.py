from device import Device

class Lock(Device):
    def __init__(self, device_id, room_id, home_id, pin_codes):
        super().__init__(device_id, "Lock", room_id, home_id)
        self.is_locked = True  # Default state is locked
        self.pin_codes = pin_codes  # List of valid 4-digit PIN codes

    def lock(self):
        self.is_locked = True
        self.status = "locked"

    def unlock(self, pin: str):
        if pin in self.pin_codes:
            self.is_locked = False
            self.status = "unlocked"
            return True
        return False  # Invalid PIN
