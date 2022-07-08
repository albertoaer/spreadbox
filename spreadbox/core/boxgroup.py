from .function_wrapper import FunctionWrapper
from .resource import Resource
from typing import Any, Callable, List, Set, Union, Dict
from .ibox import IBox

class BoxGroup(Set[IBox]):
    def __eq__(self, o: object) -> bool:
        if o == None and len(self) == 0: return True #empty group is equals to void group
        return super().__eq__(o)
    
    def filter(self, fn : Callable[[str],bool]) -> None:
        ln = set()
        for x in self:
            if not fn(x.name()):
                ln.add(x)
        self -= ln

    def __str__(self) -> str:
        return "BoxGroup{%s}" % ', '.join([box.name() for box in self])

    def members(self) -> Dict[str, IBox]:
        result : Dict[str, IBox] = {}
        for x in self:
            result[x.name()] = x
        return result

    def set(self, **kwargs):
        for k, v in kwargs.items():
            for x in self:
                x[k] = v

    def call(self, name: str, *args, **kwargs) -> Union[Any, List[Any]]:
        res = []
        for x in self:
            res.append(x.call(name, *args, **kwargs))
        return res[0] if len(res) == 1 else res

    def callasync(self, name: str, *args, **kwargs) -> Union[Resource, List[Resource]]:
        res = []
        for x in self:
            res.append(x.callasync(name, *args, **kwargs))
        return res[0] if len(res) == 1 else res

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
                boxes[i % len(boxes)][fn.name] = fn
            if mode != 0:
                res = boxes[i % len(boxes)].call(fn.name, *fn.args(), **fn.kwargs())
                ret.append(res)
        if mode != 0:
            if isinstance(function, FunctionWrapper):
                    return ret[0]
            return ret