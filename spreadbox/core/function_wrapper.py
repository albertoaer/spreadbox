from __future__ import annotations
import functools
from types import FunctionType, ModuleType
from typing import Any, Dict, List, Tuple, Union
import inspect

class FunctionWrapper:
    def __init__(self, fn : FunctionType, src : str = None, libs : set[str] = None) -> None:
        self.fn = fn
        self.name = fn.__name__
        self.src = src or inspect.getsource(fn)
        #TODO: Get all the requeriments by the library (modules of functions for example)
        self.libs = libs or set(map(lambda v:v.__name__, filter(lambda x: isinstance(x,ModuleType), fn.__globals__.values())))
        self.preparation : Tuple[List,Dict] = None #arguments for a delegated call (args,kwargs)

    def args(self) -> List:
        return self.preparation[0] if self.preparation != None else ()

    def kwargs(self) -> Dict:
        return self.preparation[1] if self.preparation != None else {}

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs) if self.preparation == None else self.fn(*self.preparation[0], **self.preparation[1])

    def make(self, *args, **kwargs) -> FunctionWrapper:
        nf = FunctionWrapper(self.fn)
        nf.preparation = (args, kwargs)
        return nf

    def __repr__(self) -> str:
        return self.src

    def __str__(self) -> str:
        return str(self.fn)

    def spread(self, over, mode : int = 2) -> Union[Any, None]:
        return over.spread(self, mode)

def wrap():
    def wrapped(fn):
        wrapper = functools.wraps(fn)(FunctionWrapper(fn))
        return wrapper
    return wrapped


def arg_wrap(src : str = None, libs : set[str] = None):
    def wrap():
        def wrapped(fn):
            wrapper = functools.wraps(fn)(FunctionWrapper(fn, src, libs))
            return wrapper
        return wrapped
    return wrap