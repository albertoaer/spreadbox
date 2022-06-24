from __future__ import annotations
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING: #Avoid circular dependency
    from .box import Box

class Resource:
    __slots__ = ('resource','container')

    def __init__(self, resource : int, container : Box) -> None:
        self.resource = resource
        self.container = container

    def get(self, permanent : bool = True) -> Any:
        return self.container.resource(self.resource, permanent)