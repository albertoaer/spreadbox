from __future__ import annotations
import functools

"""
Query rules:
function request syntax: query_req
function answer syntax: query, query_
important parameters:
    type: the query type
    value: the main value itself
"""

def query(typename : str):
    def wrapped(fn):
        @functools.wraps(fn)
        @staticmethod
        def call(*args, **kwrargs) -> dict:
            res = fn(*args, **kwrargs)
            res['type'] = typename
            return res
        return call
    return wrapped

class QueryMaker:
    @query('ok')
    def ok() -> dict:
        return {}
    
    @query('name')
    def name(name : str) -> dict:
        return {'value':name}
    
    @query('name')
    def name_req() -> dict:
        return {}

    @query('global_set')
    def global_set_req(id : str, value : str) -> dict:
        return {'value':value, 'id':id}

    @query('global_get')
    def global_get(id : str, value : str) -> dict:
        return {'value':value, 'id':id}
    
    @query('global_get')
    def global_get_req(id : str) -> dict:
        return {'id':id}

class QueryReader:
    def __init__(self, query : dict) -> None:
        self.__query : dict = query

    def __eq__(self, o: object) -> bool:
        if isinstance(o, str):
            return self.__query['type'] == o
        return super().__eq__(o)

    def __contains__(self, item : str) -> bool:
        return item in self.__query

    def __getitem__(self, item : str) -> str:
        return self.__query[item]

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