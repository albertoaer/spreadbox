from typing import Iterator, List, Tuple
import socket
import threading
import time
import psutil

from .protocol import ISocket, protocol

def ip() -> List[str]:
    host = socket.gethostname()
    return socket.gethostbyname_ex(host)[2]

def hostname() -> str:
    return socket.gethostname()

def mask(ip : str) -> str:
    for _, v in psutil.net_if_addrs().items():
        for c in v:
            if c.netmask and in_same_net(c.address, ip, c.netmask):
                return c.netmask
    return ""

def in_same_net(ipa : str, ipb : str, mask : str) -> bool:
    for x, y, z in zip(ipa.split('.'), ipb.split('.'), mask.split('.')):
        if int(x)&int(z) != int(y)&int(z):
            return False
    return True

def get_net_addresses(ip : str, mask : str) -> Iterator[str]:
    pairs = []
    baseip = [int(v) for v in ip.split('.')]
    for i, d in enumerate([255^int(v) for v in mask.split('.')]): #identify the mask target bits
        for k in range(0, 8):
            if (d>>k)&1 != 0:
                baseip[i] = baseip[i]&(255^(1<<k))
                pairs.append((i,k))
    result = [[]]
    for i in pairs: #generate the power set of all combinations of bytes
        for j in range(len(result)):
            if len(result[j]) != len(pairs)-1: #avoid last element, full of 1 would be broadcast address
                result.append(result[j] + [i])
                cloneip = baseip.copy()
                for pair in result[len(result)-1]: #apply pairs
                    cloneip[pair[0]] = cloneip[pair[0]]|(1<<pair[1])
                yield ".".join(map(str, cloneip))

def make_client(addr : Tuple[str, int], timeout : float) -> ISocket:
    sck = protocol().create_socket()
    sck.time(timeout)
    sck.into_connection(addr)
    return sck

def net_map(addrs : List[Tuple[str, int]], timeout : float = 0.001) -> List[ISocket]:
    results : List[Tuple[bool,ISocket]] = [] #Tuple(Ended,Socket)
    def connect(addr : Tuple[str, int], list : List[Tuple[bool,ISocket]], idx : int):
        try:
            client = make_client(addr, timeout)
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