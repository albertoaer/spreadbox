import socket
from typing import Tuple
from .utils import ip
from .protocol import Protocol, ISocket, use_protocol
import json

class TCPSocket(ISocket): #TCP Socket uses TCP connections
    def __init__(self, protocol : Protocol, sck : socket.socket, addr: Tuple[str, int] = None) -> None:
        super().__init__(protocol, sck, addr)
        self.backlog = 5

    def intoServer(self, port : int) -> None:
        self.socket.bind((ip()[-1], port))
        self.port = port
        self.socket.listen(self.backlog)

    def intoConnection(self, addr : Tuple[str, int]) -> None:
        self.addr = addr
        self.socket.connect(addr)

    def time(self, seconds : float) -> None:
        self.socket.settimeout(seconds)

    def accept(self) -> ISocket:
        sck, addr = self.socket.accept()
        return TCPSocket(self.protocol, sck, addr)

@use_protocol
class TCPProtocol(Protocol): #Default TCP Protocol uses TCP Sockets and protocol and shares information in json format
    def __init__(self) -> None:
        super().__init__('tcp')

    def createSocket(self) -> ISocket:
        return TCPSocket(self, socket.socket(socket.AF_INET, socket.SOCK_STREAM))

    def wrapSocket(self, sck : socket.socket, addr: Tuple[str, int] = None) -> ISocket:
        return TCPSocket(self, sck, addr)

    def write(self, payload : dict, sck : ISocket) -> None:
        msg = json.dumps(payload)
        sck.socket.sendall(bytearray(msg, 'utf-8'))

    def read(self, sck : ISocket, size : int = 1024) -> dict:
        msg = sck.socket.recv(size)
        if not msg: return None
        return json.loads(msg)

    def ask(self, payload : dict, sck : ISocket) -> dict:
        self.write(payload, sck)
        return self.read(sck)

    def close(self, sck : ISocket) -> None:
        self.write({'close':True}, sck)
        sck.socket.close()