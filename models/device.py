class Device:
    def __init__(self, device_id: str, device_type: str, room_id: str, home_id: str):
        self.device_id = device_id
        self.device_type = device_type
        self.room_id = room_id
        self.home_id = home_id
        
        # Assign initial status based on device type
        if device_type == "Light":
            self.status = "off"  # Lights default to "off"
        elif device_type == "WindowBlind":
            self.status = "closed"  # Blinds start as "closed"
        elif device_type == "Lock":
            self.status = "locked"  # Locks start as "locked"
        elif device_type == "Alarm":
            self.status = "disarmed"  # Alarm starts "disarmed"
        else:
            self.status = "unknown"  # Default for unsupported types

    def get_status(self):
        return self.status
