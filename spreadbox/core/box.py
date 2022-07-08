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
from ..network.protocol import ISocket
from ..network.client_manager import ClientManager

class Box(IBox, metaclass=MetaBox):
    def __init__(self) -> None:
        self.connections : dict[str, ISocket] = {}
        self.env_globals : dict[str, Any] = self.shared_methods
        self.idcounter : int = 0
        self.resources : dict[int, Tuple[Thread, Queue]] = {}
        self.server : ServedBox = None

    def call(self, name: str, *args, **kwargs) -> Any:
        try:
            fn = self.env_globals[name]
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
        self.env_globals[k] = v

    def __getitem__(self, k: str) -> str:
        return self.env_globals[k]

    def serve(self, port: int, prevail: bool = True) -> None:
        if self.server: raise Exception('Box already served')
        self.server = ServedBox(self, "%s::%s" % (type(self).__name__, self.name()))
        self.server.serve(port, prevail)

class ServedBox(ClientManager):
    def __init__(self, target: Box, id: str = None) -> None:
        super().__init__(id)
        self.target: Box = target

    def handle_get(self, query: QueryReader, sck: ISocket):
        if not 'id' in query: return self.logger.error("Wrong request")
        t, v = get_value_query(self.target[query['id']])
        sck.write(query.morph(value_type=t, value=v).query()) #morphing query instead of use global_get

    def handle_set(self, query: QueryReader, sck: ISocket):
        if not 'id' in query or not 'value_type' in query or not 'value' in query: return self.logger.error("Wrong request")
        self.target[query['id']] = eval_from_query(query['value_type'], query['value'], (self.target.env_globals,{}))
        sck.write(QueryMaker.ok())

    def handle_call(self, query: QueryReader, sck: ISocket):
        if not 'id' in query or not 'args' in query or not 'kwargs' in query: return self.logger.error("Wrong request")
        answer : Any = self.target.call(query['id'], *query['args'], **query['kwargs'])
        t, v = get_value_query(answer)
        sck.write(QueryMaker.call(query['id'], t, v))

    def handle_callasync(self, query: QueryReader, sck: ISocket):
        res = self.target.callasync(query['id'], *query['args'], **query['kwargs'])
        sck.write(QueryMaker.callasync(query['id'], res.resource))

    def handle_resource(self, query: QueryReader, sck: ISocket):
        val = self.target.resource(query['id'], query['delete'])
        t, v = get_value_query(val)
        sck.write(QueryMaker.resource(query['id'], t, v))

    def handle_message(self, message: dict, sck: ISocket):
        query = QueryReader(message)
        method = query.typename()
        m = getattr(ServedBox, f'handle_{method}')
        if m:
            m(self, query, sck)

class RemoteBox(IBox):
    def __init__(self, client : ISocket) -> None:
        super().__init__()
        self.client = client
        self.remote_name = None
        self.logger = getLogger("Remote::"+self.name())

    def __del__(self):
        self.client.close()

    def __call(self, name: str, do_async: bool, *args, **kwargs):
        req: dict = QueryMaker.callasync_req(name, *args, **kwargs) if do_async else QueryMaker.call_req(name, *args, **kwargs)
        query =  QueryReader(self.client.ask(req))
        if do_async:
            return Resource(query['value'], self)
        return eval_from_query(query['value_type'], query['value'], ({}, {}))

    def name(self) -> str:
        if not self.remote_name:
            self.remote_name = self.__call('name', False)
        return self.remote_name

    def on(self) -> bool:
        return self.__call('on', False)

    def overload(self) -> int:
        return self.__call('overload', False)

    def call(self, name: str, *args, **kwargs) -> Any:
        return self.__call(name, False, *args, **kwargs)

    def callasync(self, name: str, *args, **kwargs) -> Resource:
        return self.__call(name, True, *args, **kwargs)

    def resource(self, id: int, delete: bool) -> Any:
        ans = QueryReader(self.client.ask(QueryMaker.resource_req(id, delete)))
        return eval_from_query(ans['value_type'], ans['value'], ({}, {}))

    def __setitem__(self, k: str, v: Any) -> None:
        t, v = get_value_query(v)
        self.client.ask(QueryMaker.set_req(k, t, v))

    def __getitem__(self, k: str) -> str:
        query = QueryReader(self.client.ask(QueryMaker.get_req(k)))
        if not 'value_type' in query or not 'value' in query: return self.logger.error("Wrong answer")
        return eval_from_query(query['value_type'], query['value'], ({}, {}))

    def group(self) -> BoxGroup:
        return BoxGroup({self})