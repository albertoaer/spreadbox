from __future__ import annotations
import functools
from typing import List

"""
Query rules:
function request syntax: query_req
function answer syntax: query, query_
important parameters:
    type: the query type
    value: the main value itself
"""

def query(typename : str, is_request : bool = False):
    def wrapped(fn):
        @functools.wraps(fn)
        @staticmethod
        def call(*args, **kwrargs) -> dict:
            res = fn(*args, **kwrargs)
            res['type'] = typename
            res['request'] = is_request
            return res
        return call
    return wrapped

class QueryMaker:
    @query('ok')
    def ok() -> dict:
        return {}

    @query('set', True)
    def set_req(id : str, value_type : str, value : dict) -> dict:
        return {'id':id, 'value_type':value_type, 'value':value}

    @query('get')
    def get(id : str, value_type : str, value : dict) -> dict:
        return {'id':id, 'value_type':value_type, 'value':value}
    
    @query('get', True)
    def get_req(id : str) -> dict:
        return {'id':id}

    @query('call', True)
    def call_req(name : str, *args, **kwargs) -> dict:
        return {'id':name, 'args':args, 'kwargs':kwargs}

    @query('call')
    def call(name : str, value_type : str, value : dict) -> dict:
        return {'id':name, 'value_type':value_type, 'value':value}

    @query('callasync', True)
    def callasync_req(name : str, *args, **kwargs) -> dict:
        return {'id':name, 'args':args, 'kwargs':kwargs}

    @query('callasync')
    def callasync(name : str, id : int) -> dict:
        return {'id':name, 'value':id}

    @query('resource', True)
    def resource_req(id : int, delete : bool = False) -> dict:
        return {'id':id, 'delete':delete}

    @query('resource')
    def resource(id : int, value_type : str, value : dict) -> dict:
        return {'id':id, 'value_type':value_type, 'value':value}

    def function(name : str, code : str, wrapname : str = 'wrap', libs : List[dict] = []) -> dict:
        return {'name':name, 'value':code, 'wrapname':wrapname, 'libs':libs}

    def literal(data : str) -> dict:
        return {'value':data}

class QueryReader:
    def __init__(self, query : dict) -> None:
        self.__query : dict = query

    def __eq__(self, o: object) -> bool:
        if isinstance(o, str):
            return self.typename() == o
        return super().__eq__(o)

    def __contains__(self, item : str) -> bool:
        return item in self.__query

    def __getitem__(self, item : str) -> str:
        return self.__query[item]

    def typename(self) -> str:
        return self.__query['type']

    def value(self) -> str:
        return self.__query['value']

    def id(self) -> str:
        return self.__query['id']

    def morph(self, **kwargs) -> QueryReader:
        for x in kwargs.keys():
            self.__query[x] = kwargs[x]
        return self

    def query(self) -> dict:
        return self.__query