from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Set, Tuple, Union
from .function_wrapper import FunctionWrapper, arg_wrap
from .queries import QueryMaker, QueryReader
from ..network.protocol import ISocket, protocol
from ..network.client_manager import ClientManager
from ..network.utils import netMap, ip

class IBox(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def on(self) -> bool:
        pass

    @abstractmethod
    def overload(self) -> int:
        pass

    @abstractmethod
    def subscribe(self, name, function) -> None:
        pass

    @abstractmethod
    def call(self, name, *args, **kwargs) -> Any:
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
        self.connections : dict[str, ISocket] = {}
        self.envGlobals : dict[str, Any] = {}

    def subscribe(self, name, function) -> None:
        env = dict(self.envGlobals)
        env['wrap'] = arg_wrap(function)
        exec(function, env, env)
        self.envGlobals[name] = env[name] #In order to access from other functions
        self.functions[name] = env[name] #In order to be called

    def call(self, name, *args, **kwargs) -> Any:
        try:
            return self.functions[name](*args, **kwargs)
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
        elif query == 'on':
            protocol().write(QueryMaker.on(self.on()), sck)
        elif query == 'overload':
            protocol().write(QueryMaker.overload(self.overload()), sck)
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
        elif query == 'function':
            if not 'id' in query or not 'value' in query:
                pass #TODO: Log bad request
            self.subscribe(query['id'], query['value'])
            protocol().write(QueryMaker.ok(), sck)
        elif query == 'call':
            if not 'id' in query or not 'args' in query or not 'kwargs' in query:
                pass #TODO: Log bad request
            answer : Any = self.call(query['id'], *query['args'], **query['kwargs'])
            protocol().write(QueryMaker.call(query['id'], repr(answer)), sck)
    
    @staticmethod
    def seek(addr : Union[str, Tuple[str]], port : Union[int, Tuple[int]], matchs_per_second : int = 1000) -> BoxGroup:
        group = BoxGroup()
        addrs = addr
        if isinstance(addr, str):
            addrs = [addr]
        if isinstance(port, tuple) and len(addrs) != len(port):
            raise 'Expecting same number of addresses and ports'
        for sck in netMap(list(zip(addrs, port) if isinstance(port, tuple) else map(lambda a: (a, port), addrs)), 1/matchs_per_second):
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

    def name(self) -> str:
        if self.remote_name == None:
            self.remote_name = QueryReader(protocol().ask(QueryMaker.name_req(), self.client)).value()
        return self.remote_name

    def on(self) -> bool:
        return QueryReader(protocol().ask(QueryMaker.on_req(), self.client)).value()

    def overload(self) -> int:
        return QueryReader(protocol().ask(QueryMaker.overload_req(), self.client)).value()

    def subscribe(self, name, function) -> None:
        protocol().ask(QueryMaker.function_req(name, function), self.client)

    def call(self, name, *args, **kwargs) -> Any:
        return eval(QueryReader(protocol().ask(QueryMaker.call_req(name, *args, **kwargs), self.client)).value(), {}, {})

    def __setitem__(self, k: str, v: Any) -> None:
        protocol().ask(QueryMaker.global_set_req(k, repr(v)), self.client)

    def __getitem__(self, k: str) -> str:
        return eval(QueryReader(protocol().ask(QueryMaker.global_get_req(k), self.client)).value(), {}, {})

class BoxGroup(Set[IBox]):
    def __eq__(self, o: object) -> bool:
        if o == None and len(self) == 0:
            return True #avoid empty group to prevent never ended tasks
        return super().__eq__(o)
    
    def filter(self, fn : Callable[[str],bool]) -> None:
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

    def spread(self, function : Union[FunctionWrapper, List[FunctionWrapper]], mode : int = 2) -> Union[Any, List[Any], None]: #mode may be 0(subscription), 1(call), 2(both)
        mode %= 3
        fns : List[FunctionWrapper] = function
        if isinstance(function, FunctionWrapper):
            fns = [function]
        boxes : List[IBox] = [box for box in list(self) if box.on()]
        if len(boxes) == 0:
            raise Exception('No boxes available')
        boxes = sorted(boxes, key=lambda e : e.overload())
        ret : List[Any] = []
        for i in range(0, len(fns)):
            fn : FunctionWrapper = fns[i]
            if mode != 1:
                boxes[i % len(boxes)].subscribe(fn.name, repr(fn))
            if mode != 0:
                res = boxes[i % len(boxes)].call(fn.name, *fn.args(), **fn.kwargs())
                ret.append(res)
        if mode != 0:
            if isinstance(function, FunctionWrapper):
                    return ret[0]
            return ret