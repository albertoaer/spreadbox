from __future__ import annotations
from abc import ABC, abstractmethod
import socket
from typing import Tuple, Type
import socket

class ISocket(ABC):
    def __init__(self, protocol : Protocol, sck : socket.socket, addr: Tuple[str, int] = None) -> None:
        self.protocol = protocol
        self.socket = sck
        self.addr = addr

    @abstractmethod
    def intoServer(self, port : int) -> None:
        pass

    @abstractmethod
    def intoConnection(self, addr : Tuple[str, int]) -> None:
        pass

    @abstractmethod
    def time(self, seconds : float) -> None:
        pass

    @abstractmethod
    def accept(self) -> ISocket:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

class Protocol(ABC):
    def __init__(self, name : str) -> None:
        self.name = name

    @abstractmethod
    def createSocket(self) -> ISocket:
        pass

    @abstractmethod
    def wrapSocket(self, sck : socket.socket, addr: Tuple[str, int] = None) -> ISocket:
        pass

    @abstractmethod
    def write(self, payload : dict, sck : ISocket) -> None:
        pass

    @abstractmethod
    def read(self, sck : ISocket, size : int = 1024) -> dict:
        pass

    @abstractmethod
    def ask(self, payload : dict, sck : ISocket) -> dict: #Ask sends a payload and awaits its answer
        pass

    @abstractmethod
    def close(self, sck : ISocket) -> None:
        pass

active_protocol : Protocol = None

def use_protocol(protocol : Type[Protocol]):
    global active_protocol
    active_protocol = protocol()
    return protocol

def protocol() -> Protocol:
    return active_protocol