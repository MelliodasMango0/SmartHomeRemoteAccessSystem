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

    # def _loop_recv(self, size: int):
    #     """
    #     Ensures we receive exactly `size` bytes of data.
    #     """
    #     data = bytearray(b" " * size)
    #     data = bytearray(size)
    #     mv = memoryview(data)
    #     while size:
    #         rsize = self._sock.recv_into(mv, size)
    #         mv = mv[rsize:]
    #         size -= rsize
    #     return data

    def _loop_recv(self, size: int):
        data = bytearray(size)
        mv = memoryview(data)
        total_received = 0

        while size:
            rsize = self._sock.recv_into(mv, size)
            if rsize == 0:
                raise ConnectionError("[ERROR] Socket closed while receiving data")
            
            mv = mv[rsize:]
            size -= rsize
            total_received += rsize
            print(f"[DEBUG] Received {rsize} bytes, Total: {total_received}/{len(data)}")
        
        return data


    def send_message(self, message: CSmessage):
        """
        Marshals and sends a message over the socket.
        """
        mdata = message.marshal()
        size = len(mdata)
        sdata = '{:04}{}'.format(size, mdata)

        print(f"[DEBUG] Sending message: size={size}, content={sdata}")  # Debugging

        self._sock.sendall(sdata.encode('utf-8'))

    def receive_message(self) -> CSmessage:
        """
        Receives a message, unmarshals it, and returns a SmartHomeMessage object.
        """
        try:
            print("[DEBUG] Waiting to receive message...")  # Debugging
            m = CSmessage()
            
            size_data = self._loop_recv(4).decode('utf-8')  # Read the first 4 bytes (size)
            size = int(size_data)
            print(f"[DEBUG] Message size header received: {size}")  # Debugging
            
            params = self._loop_recv(size).decode('utf-8')  # Read the message body
            print(f"[DEBUG] Raw message data received: {params}")  # Debugging
            
            m.unmarshal(params)

        except Exception as e:
            print(f"[ERROR] Error receiving message: {e}")
            raise Exception('Error receiving message')
        else:
            print(f"[DEBUG] Successfully parsed message: {m.marshal()}")  # Debugging
            return m


    def close(self):
        """
        Closes the socket connection.
        """
        self._sock.close()
