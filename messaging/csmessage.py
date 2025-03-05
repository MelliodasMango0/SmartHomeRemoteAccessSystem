from enum import Enum

class REQS(Enum):
    LGIN = 100  
    LOUT = 101  
    LIST = 102  
    CHG_STATUS = 103
    SRCH = 104
    EXIT = 105 

    TURN_ON = 200
    TURN_OFF = 201
    LOCK = 202
    UNLOCK = 203

    CHECK_STATUS = 204

class CSmessage:
    PJOIN = '&'
    VJOIN = '{}={}'
    VJOIN1 = '='

    def __init__(self):
        self._data = {}
        self._data['type'] = REQS.CHECK_STATUS

    def setType(self, t):
        self._data['type'] = t

    def getType(self):
        return self._data['type']

    def addValue(self, key, value):
        self._data[key] = value

    def getValue(self, key):
        return self._data.get(key)

    def marshal(self):

        """Convert message to string format for transmission"""
        pairs = [
            CSmessage.VJOIN.format(k, v.name if isinstance(v, REQS) else v)
            for (k, v) in self._data.items()
        ]
        return CSmessage.PJOIN.join(pairs)

    def unmarshal(self, data):
        """
        Convert received string data back into a structured message.
        """
        self._data = {}

        print(f"[DEBUG] Unmarshaling message: {data}")  # Debugging

        if data:
            params = data.split(CSmessage.PJOIN)
            for p in params:
                try:
                    k, v = p.split(CSmessage.VJOIN1, 1)
                    if k == "type":
                        try:
                            self._data[k] = REQS[v]  # Convert string back to REQS Enum
                        except KeyError:
                            self._data[k] = REQS(int(v))  # Try converting integer values
                    else:
                        self._data[k] = v
                except ValueError:
                    print(f"[ERROR] Failed to parse parameter: {p}")  # Debugging



