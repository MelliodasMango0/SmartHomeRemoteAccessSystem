from device import Device

class Alarm(Device):
    def __init__(self, device_id, home_id, pin_code):
        super().__init__(device_id, "Alarm", None, home_id)  # No room assigned
        self.is_armed = False  # Default state is disarmed
        self.pin_code = pin_code  # 4-digit PIN required for disarming

    def arm(self):
        self.is_armed = True
        self.status = "armed"

    def disarm(self, pin: str):
        if pin == self.pin_code:
            self.is_armed = False
            self.status = "disarmed"
            return True
        return False  # Invalid PIN
