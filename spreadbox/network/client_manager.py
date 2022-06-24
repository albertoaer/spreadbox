from abc import ABC, abstractmethod
from time import sleep
from typing import List, Tuple
from .protocol import ISocket, protocol
from threading import Thread

class ClientManager(ABC):
    def __init__(self) -> None:
        super().__init__()
        self.running : bool = False
        self.clients : List[Tuple[ISocket,Thread]] = []

    def stop(self):
        self.running = False

    def runFor(self, server : ISocket):
        self.running = True
        while self.running:
            client = server.accept()
            thread = Thread(target=self.attachClient, args=(client,))
            self.clients.append((client, thread))
            thread.start()

    def attachClient(self, con : ISocket):
        while self.running:
            data = protocol().read(con)
            if data:
                self.managerMessage(data, con)
            else: sleep(0.001)

    @abstractmethod
    def managerMessage(self, message: dict, sck : ISocket):
        pass