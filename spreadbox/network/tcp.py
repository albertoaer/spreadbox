import socket
from typing import Tuple, Union
from .utils import ip
from .protocol import Protocol, ISocket, SocketRole, use_protocol
import json

class TCPSocket(ISocket): #TCP Socket uses TCP connections
    def __init__(self, protocol : Protocol, sck : socket.socket, addr: Tuple[str, int] = None) -> None:
        super().__init__(protocol, sck, addr)
        self.backlog = 5
        self.role : SocketRole = SocketRole.Undefined

    def intoServer(self, port : int) -> None:
        if self.role != SocketRole.Undefined: raise "Expecting unassigned socket"
        self.socket.bind((ip()[-1], port))
        self.port = port
        self.socket.listen(self.backlog)
        self.role = SocketRole.Server

    def intoConnection(self, addr : Tuple[str, int]) -> None:
        if self.role != SocketRole.Undefined: raise "Expecting unassigned socket"
        self.addr = addr
        self.socket.connect(addr)
        self.role = SocketRole.Client

    def time(self, seconds : Union[float,None]) -> None:
        self.socket.settimeout(seconds)

    def accept(self) -> ISocket:
        sck, addr = self.socket.accept()
        return TCPSocket(self.protocol, sck, addr)

    def close(self) -> None:
        self.socket.close()

    def migrate(self, base : Union[ISocket, None] = None) -> Union[ISocket, None]:
        nSocket = base or self.protocol.createSocket()
        self.protocol.close(self)
        if self.role == SocketRole.Server:
            nSocket.intoServer(self.port)
        elif self.role == SocketRole.Client:
            nSocket.intoConnection(self.addr)
        return nSocket

@use_protocol
class TCPProtocol(Protocol): #Default TCP Protocol uses TCP Sockets and protocol, besides it uses json format as data format
    def __init__(self) -> None:
        super().__init__('tcp')

    def createSocket(self) -> ISocket:
        return TCPSocket(self, socket.socket(socket.AF_INET, socket.SOCK_STREAM))

    def wrapSocket(self, sck : socket.socket, addr: Tuple[str, int] = None) -> ISocket:
        return TCPSocket(self, sck, addr)

    def write(self, payload : dict, sck : ISocket) -> None:
        msg = json.dumps(payload)
        sck.socket.sendall(bytearray(msg, 'utf-8'))

    def read(self, sck : ISocket, size : int = 1024) -> Union[dict, None]:
        msg = sck.socket.recv(size)
        if not msg: return None
        return json.loads(msg)

    def ask(self, payload : dict, sck : ISocket) -> dict:
        self.write(payload, sck)
        return self.read(sck)

    def close(self, sck : ISocket) -> None:
        sck.socket.close()