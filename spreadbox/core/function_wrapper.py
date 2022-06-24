from __future__ import annotations
from types import FunctionType, ModuleType
from typing import Any, Dict, List, Tuple, Union
import inspect

def no_indent(src : str) -> str: return '\n'.join([s.lstrip() for s in src.split('\n')])

class FunctionWrapper:
    __slots__ = ('fn','name','src','wrapname','libs','preparation')

    def __init__(self, fn : FunctionType, src : str = None, wrapname : str = "wrap", libs : set[str] = None) -> None:
        self.fn = fn
        self.name = fn.__name__
        self.src = src or no_indent(inspect.getsource(fn)) #removes indentation, wrapped function are not holded in any scope
        self.wrapname = wrapname
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
        nf = FunctionWrapper(self.fn, wrapname=self.wrapname)
        nf.preparation = (args, kwargs)
        return nf

    def __repr__(self) -> str:
        return self.src

    def __str__(self) -> str:
        return str(self.fn)

    def spread(self, over, mode : int = 2) -> Union[Any, None]:
        return over.spread(self, mode)

def name_of(f : inspect.FrameType) -> str:
    from_ = inspect.getframeinfo(f)
    name = from_.code_context[0].strip()
    if name.find('@') == 0: name = name[1:]
    i = name.find('(')
    if i >= 0: name = name[0:i]
    if name: return name
    raise "Name not found, unexpected behaviour"

def wrap():
    name = name_of(inspect.currentframe().f_back)
    def wrapped(fn):
        wrapper = FunctionWrapper(fn, wrapname=name)
        return wrapper
    return wrapped

def arg_wrap(src : str = None, wrapname : str = 'wrap', libs : set[str] = None):
    def wrap():
        def wrapped(fn):
            wrapper = FunctionWrapper(fn, src, wrapname, libs)
            return wrapper
        return wrapped
    return wrap