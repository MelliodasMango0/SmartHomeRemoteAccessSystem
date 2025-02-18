from models.device import Device

class Light(Device):
    def __init__(self, device_id, room_id, home_id, brightness=100, color="white"):
        super().__init__(device_id, "Light", room_id, home_id)
        self.brightness = brightness
        self.color = color
    
    def turn_on(self):
        self.status = "on"
    
    def turn_off(self):
        self.status = "off"
    
    def dim(self, level: int):
        self.brightness = level
    
    def change_color(self, color: str):
        self.color = color