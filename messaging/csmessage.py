from enum import Enum

class REQS(Enum):
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
        pairs = [CSmessage.VJOIN.format(k, v) for (k, v) in self._data.items()]
        return CSmessage.PJOIN.join(pairs)

    def unmarshal(self, data):
        self._data = {}
        if data:
            params = data.split(CSmessage.PJOIN)
            for p in params:
                k, v = p.split(CSmessage.VJOIN1)
                self._data[k] = v
