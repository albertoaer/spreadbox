from abc import ABCMeta, abstractmethod
from .resource import Resource
from typing import Any

class IBox(metaclass=ABCMeta):
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
    def call(self, name: str, *args, **kwargs) -> Any:
        pass

    @abstractmethod
    def callasync(self, name: str, *args, **kwargs) -> Resource:
        pass

    @abstractmethod
    def resource(self, id : int, delete : bool) -> Any:
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
        if not isinstance(o, IBox): return False
        return self.name() == o.name()

def shared(use_self : bool = False):
    def shared_obj(obj : Any) -> Any: #Allows properties be accessed from the outside
        obj.__is_shared__ = True
        obj.__use_self__ = use_self
        return obj
    return shared_obj

class MetaBox(ABCMeta):
    def __call__(cls, *args, **kwargs):
        #Includes all the shared elements into the shared methods dictionary
        cls.shared_methods = {}
        share_by_default = ['name', 'on', 'overload']
        for id in dir(cls):
            fn = getattr(cls, id)
            if id in share_by_default:
                cls.shared_methods[id] = fn
                setattr(fn, '__use_self__', True)
                cls.shared_methods[id] = fn
            elif hasattr(fn, '__is_shared__') and fn.__is_shared__:
                cls.shared_methods[id] = fn
        return super().__call__(*args, **kwargs)