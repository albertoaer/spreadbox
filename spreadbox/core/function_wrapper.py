from __future__ import annotations
from types import FunctionType
from typing import Any, Dict, List, Tuple, Union
from .dependencies import DependencySolver
import inspect

#Only valid for functions, it asumes first line is reference indentation
def fn_correct_indent(fn_src : str) -> str:
    lines = fn_src.split('\n')
    if not lines: return fn_src
    tabsize = len(lines[0]) - len(lines[0].lstrip())
    if tabsize == 0: return fn_src
    return '\n'.join([line[tabsize] for line in lines])

class FunctionWrapper:
    __slots__ = ('fn','name','src','wrapname','libs','preparation')

    def __init__(self, fn : FunctionType, src : str = None, wrapname : str = "wrap", libs : List[dict] = None) -> None:
        self.fn = fn
        self.name = fn.__name__
        self.src = src or fn_correct_indent(inspect.getsource(fn)) #removes indentation, wrapped function are not holded in any scope
        self.wrapname = wrapname
        self.libs = libs or DependencySolver.solve(fn).format()
        self.preparation : Tuple[List,Dict] = None #arguments for a delegated call (args,kwargs)

    def args(self) -> List:
        return self.preparation[0] if self.preparation != None else ()

    def kwargs(self) -> Dict:
        return self.preparation[1] if self.preparation != None else {}

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs) if self.preparation == None else self.fn(*self.preparation[0], **self.preparation[1])

    def make(self, *args, **kwargs) -> FunctionWrapper:
        nf = FunctionWrapper(self.fn, self.str, self.wrapname, self.libs)
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
    raise Exception("Name not found, unexpected behaviour")

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