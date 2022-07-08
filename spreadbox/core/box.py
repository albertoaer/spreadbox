from __future__ import annotations
from threading import Thread
from time import sleep
from typing import Any, Tuple
from queue import Queue
from logging import getLogger

from .ibox import IBox, MetaBox
from .resource import Resource
from .boxgroup import BoxGroup
from ..data_transport import QueryMaker, QueryReader, eval_from_query, get_value_query
from ..network.protocol import ISocket, protocol
from ..network.client_manager import ClientManager

class Box(IBox, ClientManager, metaclass=MetaBox):
    def __init__(self) -> None:
        self.connections : dict[str, ISocket] = {}
        self.envGlobals : dict[str, Any] = self.shared_methods
        self.idcounter : int = 0
        self.resources : dict[int, Tuple[Thread, Queue]] = {}
        super().__init__("%s::%s" % (type(self).__name__, self.name()))

    def call(self, name: str, *args, **kwargs) -> Any:
        try:
            fn = self.envGlobals[name]
            use_self = hasattr(fn, '__use_self__') and fn.__use_self__
            return fn(*args, **kwargs) if not use_self else fn(self, *args, **kwargs)
        except Exception as e:
            return e

    def callasync(self, name: str, *args, **kwargs) -> Resource:
        queue = Queue()
        id = self.idcounter
        t = Thread(target=lambda q: q.put(self.call(name, *args, **kwargs)), args=(queue,))
        self.resources[id] = (t, queue)
        self.idcounter += 1
        t.start()
        return Resource(id, self)

    def resource(self, id : int, delete : bool) -> Any:
        time = 0.0001
        if id in self.resources:
            while self.resources[id][1].qsize() == 0:
                sleep(time)
                time*=2
            val = self.resources[id][1].get()
            if delete:
                del self.resources[id]
            return val
        return None

    def __setitem__(self, k: str, v: Any) -> None:
        self.envGlobals[k] = v

    def __getitem__(self, k: str) -> str:
        return self.envGlobals[k]

    def handleMessage(self, message: dict, sck: ISocket):
        query = QueryReader(message)
        if query == 'name':
            protocol().write(QueryMaker.name(self.name()), sck)
        elif query == 'on':
            protocol().write(QueryMaker.on(self.on()), sck)
        elif query == 'overload':
            protocol().write(QueryMaker.overload(self.overload()), sck)
        elif query == 'get':
            if not 'id' in query: return self.logger.error("Wrong request")
            t, v = get_value_query(self[query['id']])
            protocol().write(query.morph(value_type=t, value=v).query(), sck) #morphing query instead of use global_get
        elif query == 'set':
            if not 'id' in query or not 'value_type' in query or not 'value' in query: return self.logger.error("Wrong request")
            self[query['id']] = eval_from_query(query['value_type'], query['value'], (self.envGlobals,{}))
            protocol().write(QueryMaker.ok(), sck)
        elif query == 'call':
            if not 'id' in query or not 'args' in query or not 'kwargs' in query: return self.logger.error("Wrong request")
            answer : Any = self.call(query['id'], *query['args'], **query['kwargs'])
            t, v = get_value_query(answer)
            protocol().write(QueryMaker.call(query['id'], t, v), sck)
        elif query == 'callasync':
            res = self.callasync(query['id'], *query['args'], **query['kwargs'])
            protocol().write(QueryMaker.callasync(query['id'], res.resource), sck)
        elif query == 'resource':
            val = self.resource(query['id'], query['delete'])
            t, v = get_value_query(val)
            protocol().write(QueryMaker.resource(query['id'], t, v), sck)

class RemoteBox(IBox):
    def __init__(self, client : ISocket) -> None:
        super().__init__()
        self.client = client
        self.remote_name = None
        self.logger = getLogger("Remote::"+self.name())

    def __del__(self):
        self.client.close()

    def name(self) -> str:
        if self.remote_name == None:
            self.remote_name = QueryReader(protocol().ask(QueryMaker.name_req(), self.client)).value()
        return self.remote_name

    def on(self) -> bool:
        return QueryReader(protocol().ask(QueryMaker.on_req(), self.client)).value()

    def overload(self) -> int:
        return QueryReader(protocol().ask(QueryMaker.overload_req(), self.client)).value()

    def call(self, name: str, *args, **kwargs) -> Any:
        query = QueryReader(protocol().ask(QueryMaker.call_req(name, *args, **kwargs), self.client))
        return eval_from_query(query['value_type'], query['value'], ({}, {}))

    def callasync(self, name: str, *args, **kwargs) -> Resource:
        query = QueryReader(protocol().ask(QueryMaker.callasync_req(name, *args, **kwargs), self.client))
        return Resource(query['value'], self)

    def resource(self, id: int, delete: bool) -> Any:
        ans = QueryReader(protocol().ask(QueryMaker.resource_req(id, delete), self.client))
        return eval_from_query(ans['value_type'], ans['value'], ({}, {}))

    def __setitem__(self, k: str, v: Any) -> None:
        t, v = get_value_query(v)
        protocol().ask(QueryMaker.set_req(k, t, v), self.client)

    def __getitem__(self, k: str) -> str:
        query = QueryReader(protocol().ask(QueryMaker.get_req(k), self.client))
        if not 'value_type' in query or not 'value' in query: return self.logger.error("Wrong answer")
        return eval_from_query(query['value_type'], query['value'], ({}, {}))

    def group(self) -> BoxGroup:
        return BoxGroup({self})