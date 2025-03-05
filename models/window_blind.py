from device import Device

class WindowBlind(Device):
    def __init__(self, device_id, room_id, home_id):
        super().__init__(device_id, "WindowBlind", room_id, home_id)
        self.is_up = False
        self.is_open = False

    def raise_blinds(self):
        self.is_up = True
        self.status = "up"

    def lower_blinds(self):
        self.is_up = False
        self.status = "down"

    def open_blinds(self):
        self.is_open = True
        self.status = "open"

    def close_blinds(self):
        self.is_open = False
        self.status = "closed"
