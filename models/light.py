from device import Device

class Light(Device):
    def __init__(self, device_id, room_id, home_id):
        super().__init__(device_id, "Light", room_id, home_id)
        self.brightness = 0  # Default brightness level
        self.color = "white"  # Default color

    def turn_on(self):
        self.status = "on"

    def turn_off(self):
        self.status = "off"

    def dim(self, level: int):
        if 0 <= level <= 100:
            self.brightness = level
            self.status = "dimmed"
        else:
            raise ValueError("Brightness level must be between 0 and 100")

    def change_color(self, color: str):
        self.color = color
