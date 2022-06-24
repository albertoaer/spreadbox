from typing import List, Union
from ..network import ISocket, protocol

class Resource:
    def __init__(self, id : Union[str, int], machine : str) -> None:
        self.id = id
        self.machine = machine

    def take(self, group : List[ISocket]) -> dict:
        for elem in group:
            if elem.addr[0] == self.machine:
                return protocol().askFor(self.id, elem)
        return None