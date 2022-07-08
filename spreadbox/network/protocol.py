from __future__ import annotations
from abc import ABC, abstractmethod
import socket
from typing import Tuple, Type, Union, NewType
from enum import Enum

class SocketRole(Enum):
    Server = 0
    Client = 1
    Undefined = 2

Address = NewType('Address', Tuple[str, int])

class ISocket(ABC):
    def __init__(self, protocol : Protocol, sck : socket.socket, addr: Address = None) -> None:
        self.protocol = protocol
        self.socket = sck
        self.addr = addr

    @abstractmethod
    def into_server(self, port : int) -> None:
        pass

    @abstractmethod
    def into_connection(self, addr : Address) -> None:
        pass

    @abstractmethod
    def time(self, seconds : Union[float,None]) -> None:
        pass

    @abstractmethod
    def accept(self) -> ISocket:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def migrate(self, base : Union[ISocket, None] = None) -> Union[ISocket, None]:
        return None #if returns None, its not implemented

    @abstractmethod
    def write(self, payload : dict, sck : ISocket) -> None:
        pass

    @abstractmethod
    def read(self, sck : ISocket, size : int = 1024) -> Union[dict, None]:
        pass

    @abstractmethod
    def ask(self, payload : dict, sck : ISocket) -> dict: #Ask sends a payload and awaits its answer
        pass

class Protocol(ABC):
    def __init__(self, name : str) -> None:
        self.name = name

    @abstractmethod
    def create_socket(self) -> ISocket:
        pass

    @abstractmethod
    def wrap_socket(self, sck : socket.socket, addr: Address = None) -> ISocket:
        pass

active_protocol : Protocol = None

def use_protocol(protocol : Type[Protocol]):
    global active_protocol
    active_protocol = protocol()
    return protocol

def protocol() -> Protocol:
    return active_protocol