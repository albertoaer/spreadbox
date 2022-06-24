from types import FunctionType, ModuleType
from typing import List, Tuple
from dataclasses import dataclass
from logging import Logger, getLogger

@dataclass
class Dependency:
    route: str
    selected_import: bool = False #if it's true: from x import y,z,..., else import x
    elements: List[Tuple[str,str]] = None #first element is original name, second is the alias it may have

    def __str__(self):
        return 'from %s import %s' % (self.route, ','.join(([x[0] if x[0] == x[1] else '%s as %s' % (x[0],x[1]) for x in self.elements]))) if self.selected_import else ('import %s' % self.route)

class Dependencies(List[Dependency]):
    def compact(self) -> None:
        c : int = 0
        while c < len(self):
            if self[c].selected_import:
                i : int = 0
                while i < len(self):
                    if i != c:
                        if self[i].selected_import and self[i].route == self[c].route:
                            self[c].elements.extend(self[i].elements)
                            del self[i]
                            continue
                    i += 1
            c += 1

    def format(self) -> List[dict]:
        return [{'route':d.route, 'selected_import':d.selected_import, 'elements':d.elements} for d in self]

class DependencySolver:
    @staticmethod
    def solve(fn : FunctionType) -> Dependencies:
        logger = getLogger('DependencySolver')
        res = Dependencies()
        for k, v in fn.__globals__.items():
            if k != "__builtins__":
                if hasattr(v, '__module__') and k != "__loader__" and v.__module__ != "__main__": #cannot import from the main file
                    if not hasattr(v, '__name__'):
                        logger.warn('Dependency: %s::%s could not be solved' % (k,v))
                    else:
                        res.append(Dependency(v.__module__, True, [(v.__name__, k)]))
                elif isinstance(v, ModuleType):
                    res.append(Dependency(k))
        res.compact()
        return res

    @staticmethod
    def fromlist(data : List[dict]) -> Dependencies:
        res = Dependencies()
        for d in data:
            res.append(Dependency(d['route'], d['selected_import'], d['elements']))
        return res