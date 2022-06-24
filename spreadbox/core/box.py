from __future__ import annotations
from abc import ABC, abstractmethod
import threading
from typing import Any, Callable, List, Set, Tuple, Union
from .function_wrapper import FunctionWrapper
from .queries import QueryMaker, QueryReader
from ..network.protocol import ISocket, protocol
from ..network.client_manager import ClientManager
from ..network.utils import netMap, ip
from threading import Thread

class IBox(ABC):
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def subscribe(self, name, function):
        pass

    @abstractmethod
    def call(self, name, *args, **kwargs):
        pass

    @abstractmethod
    def __setitem__(self, k: str, v: Any) -> None:
        pass

    @abstractmethod
    def __getitem__(self, k: str) -> str:
        pass

    def __hash__(self) -> int:
        return hash(self.name()) #hash only the name

    #if the names are equals they are the same besides maybe they are not
    #because on the network can not be two boxes with the same name
    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Box): return False
        return self.name() == o.name()

class Box(IBox, ClientManager):
    def __init__(self) -> None:
        super().__init__()
        self.functions : dict = {}
        self.server : ISocket = None
        self.connections : dict[str, ISocket] = {}
        self.envGlobals : dict[str, Any] = {}
        self.thread : threading.Thread = None

    def subscribe(self, name, function):
        self.envGlobals[name] = function #In order to access from other functions
        self.functions[name] = function #In order to be called

    def call(self, name, *args, **kwargs):
        try:
            self.functions[name](*args, **kwargs)
        except BaseException as e:
            return e

    def __setitem__(self, k: str, v: Any) -> None:
        self.envGlobals[k] = v

    def __getitem__(self, k: str) -> str:
        return repr(self.envGlobals[k])

    def managerMessage(self, message: dict, sck: ISocket):
        query = QueryReader(message)
        if query == 'name':
            protocol().write(QueryMaker.name(self.name()), sck)
        elif query == 'global_get':
            if 'id' in query:
                protocol().write(query.morph(value=self[query['id']]).query(), sck) #morphing query instead of use global_get
            else:
                pass #TODO: Log bad request
        elif query == 'global_set':
            if 'id' in query and 'value' in query:
                self[query['id']] = eval(query.value(), self.envGlobals, {})
                protocol().write(QueryMaker.ok(), sck)
            else:
                pass #TODO: Log bad request

    def serve(self, port : int): #allow remote devices connect and use the box
        if self.server != None:
            raise "Already served"
        self.server = protocol().createSocket()
        self.server.intoServer(port)
        #Thread configuration and execution
        self.thread = Thread(target=self.runFor, args=(self.server,))
        self.thread.start()
    
    @staticmethod
    def seek(addr : Union[str, Tuple[str]], port : int, matchs_per_second : int = 1000) -> BoxGroup:
        group = BoxGroup()
        addrs = addr
        if isinstance(addr, str):
            addrs = [addr]
        for sck in netMap(map(lambda a: (a, port), addrs), 1/matchs_per_second):
            group.add(RemoteBox(sck))
        if len(group) == 0: return None #avoid return empty group to prevent never ended tasks
        return group

    @staticmethod
    def network(port : int, filter : Callable[[str],bool] = None, matchs_per_second : int = 1000) -> BoxGroup:
        #only valid for IPV4
        thisip = ip()[-1]
        modableip = '.'.join(thisip.split('.')[0:-1]) + "."
        group = Box.seek([modableip + str(num) for num in range(0, 256)], port, matchs_per_second)
        if filter != None and group != None:
            group.filter(filter)
        return group

class RemoteBox(IBox):
    def __init__(self, client : ISocket) -> None:
        super().__init__()
        self.client = client
        self.remote_name = None

    def name(self):
        if self.remote_name == None:
            self.remote_name = QueryReader(protocol().ask(QueryMaker.name_req(), self.client)).value()
        return self.remote_name

    def subscribe(self, name, function):
        pass #TODO: Send subscription message

    def call(self, name, *args, **kwargs):
        pass #TODO: Send call message

    def __setitem__(self, k: str, v: Any) -> None:
        protocol().ask(QueryMaker.global_set_req(k, repr(v)), self.client)

    def __getitem__(self, k: str) -> str:
        return eval(QueryReader(protocol().ask(QueryMaker.global_get_req(k), self.client)).value(), {}, {})

class BoxGroup(Set[Box]):
    def __eq__(self, o: object) -> bool:
        if o == None and len(self) == 0:
            return True #avoid empty group to prevent never ended tasks
        return super().__eq__(o)
    
    def filter(self, fn : Callable[[str],bool]):
        ln = set()
        for x in self:
            if not fn(x.name()):
                ln.add(x)
        self -= ln

    def __str__(self) -> str:
        return "BoxGroup{%s}" % ', '.join([box.name() for box in self])

    def members(self) -> dict[str, Box]:
        result : dict[str, Box] = {}
        for x in self:
            result[x.name()] = x
        return result

    def spread(self, function : Union[FunctionWrapper, List[FunctionWrapper]]):
        pass