import socket
from typing import List, Tuple
from .protocol import ISocket, protocol

def ip() -> List[str]:
    host = socket.gethostname()
    return socket.gethostbyname_ex(host)[2]

def makeClient(addr : Tuple[str, int], timeout : float) -> ISocket:
    sck = protocol().createSocket()
    sck.time(timeout)
    sck.intoConnection(addr)
    return sck

def netMap(addrs : List[Tuple[str, int]], timeout : float = 0.001) -> List[ISocket]:
    sockets : List[socket.socket] = []
    for addr in addrs:
        try:
            client = makeClient(addr, timeout)
            client.time(None)
            sockets.append(client)
        except socket.error:
            continue
    return sockets