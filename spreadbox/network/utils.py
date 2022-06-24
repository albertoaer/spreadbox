import socket
from typing import List, Tuple
from .protocol import ISocket, protocol
import threading
import time

def ip() -> List[str]:
    host = socket.gethostname()
    return socket.gethostbyname_ex(host)[2]

def makeClient(addr : Tuple[str, int], timeout : float) -> ISocket:
    sck = protocol().createSocket()
    sck.time(timeout)
    sck.intoConnection(addr)
    return sck

def netMap(addrs : List[Tuple[str, int]], timeout : float = 0.001) -> List[ISocket]:
    results : List[Tuple[bool,ISocket]] = [] #Tuple(Ended,Socket)
    def connect(addr : Tuple[str, int], list : List[Tuple[bool,ISocket]], idx : int):
        try:
            client = makeClient(addr, timeout)
            client.time(None)
            list[idx] = (True, client)
        except socket.error:
            list[idx] = (True, None)
    for i, addr in enumerate(addrs):
        thread = threading.Thread(target=connect, args=(addr,results,i))
        results.append((False,None))
        thread.start()
    sockets : List[ISocket] = []
    for x in range(0, len(results)):
        if not results[x][0]:
            time.sleep(timeout)
            if not results[x][0]:
                continue
        if results[x][1]:
            sockets.append(results[x][1])
    return sockets