import functools

class QueryMaker:
    @staticmethod
    def query(typename):
        def wrapped(fn):
            @functools.wraps(fn)
            def call(*args, **kwrargs):
                res = fn(*args, **kwrargs)
                res['type'] = typename
            return call
        return wrapped

    @query('name')
    @staticmethod
    def name():
        return {}

class QueryReader:
    def __init__(self, query : dict) -> None:
        self.query : dict = query

    def __eq__(self, o: object) -> bool:
        if isinstance(o, str):
            return self.query['type'] == o
        return super().__eq__(o)