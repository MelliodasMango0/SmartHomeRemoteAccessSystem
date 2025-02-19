import socket
from messaging.csmessage import CSmessage

class SmartHomePDU:
    """
    Handles sending and receiving messages over a TCP connection for the Smart Home system.
    """

    def __init__(self, comm: socket):
        """
        Initializes the PDU with a socket connection.
        """
        self._sock = comm

    def _loop_recv(self, size: int):
        """
        Ensures we receive exactly `size` bytes of data.
        """
        data = bytearray(b" " * size)
        mv = memoryview(data)
        while size:
            rsize = self._sock.recv_into(mv, size)
            mv = mv[rsize:]
            size -= rsize
        return data

    def send_message(self, message: CSmessage):
        """
        Marshals and sends a message over the socket.
        """
        mdata = message.marshal()
        size = len(mdata)
        sdata = '{:04}{}'.format(size, mdata)
        self._sock.sendall(sdata.encode('utf-8'))

    def receive_message(self) -> CSmessage:
        """
        Receives a message, unmarshals it, and returns a SmartHomeMessage object.
        """
        try:
            m = CSmessage()
            size = int(self._loop_recv(4).decode('utf-8'))  # Read the first 4 bytes (size)
            params = self._loop_recv(size).decode('utf-8')  # Read the message body
            m.unmarshal(params)
        except Exception:
            raise Exception('Error receiving message')
        else:
            return m

    def close(self):
        """
        Closes the socket connection.
        """
        self._sock.close()
