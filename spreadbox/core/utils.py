from typing import Callable, Tuple, Union

from .box import BoxGroup, RemoteBox
from ..network.utils import get_net_addresses, net_map, ip, mask

def get(addr : str, port : int, timeout : float = 1) -> Union[RemoteBox, None]:
    res = net_map([(addr, port)], timeout)
    return RemoteBox(res[0]) if res else None
    
def seek(addr : Union[str, Tuple[str]], port : Union[int, Tuple[int]], matchs_per_second : int = 1000) -> BoxGroup:
    group = BoxGroup()
    addrs = addr
    if isinstance(addr, str):
        addrs = [addr]
    if isinstance(port, tuple) and len(addrs) != len(port):
        raise Exception('Expecting same number of addresses and ports')
    for sck in net_map(list(zip(addrs, port) if isinstance(port, tuple) else map(lambda a: (a, port), addrs)), 1/matchs_per_second):
        group.add(RemoteBox(sck))
    return group if group else None #avoid return empty group to prevent never ended tasks

def network(port : int, filter : Callable[[str],bool] = None, matchs_per_second : int = 1000) -> BoxGroup:
    #only valid for IPV4
    thisip = ip()[-1]
    ipmask = mask(thisip)
    group = seek(list(get_net_addresses(thisip, ipmask)), port, matchs_per_second)
    if filter and group:
        group.filter(filter)
    return group