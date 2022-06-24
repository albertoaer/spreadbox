from abc import abstractmethod
from time import sleep
from typing import List, Tuple
from ..environment.stoppable import Stoppable
from .protocol import ISocket, protocol
from threading import Thread

class ClientManager(Stoppable):
    def __init__(self) -> None:
        super().__init__()
        self.running : bool = False
        self.clients : List[Tuple[ISocket,Thread]] = []
        self.server : ISocket = None
        self.thread : Thread = None

    def stopServer(self):
        self.running = False

    def runFor(self, server : ISocket):
        self.running = True
        while self.running:
            client : ISocket
            try:
                client = server.accept()
            except:
                self.running = False
            else:
                thread = Thread(target=self.attachClient, args=(client,))
                self.clients.append((client, thread))
                thread.start()

    def attachClient(self, con : ISocket):
        while self.running:
            data = protocol().read(con)
            if data:
                self.managerMessage(data, con)
            else: sleep(0.001)

    def serve(self, port : int, prevail : bool = False) -> None: #create a service that manage users
        if self.server != None:
            raise "Already served"
        self.server = protocol().createSocket()
        self.server.intoServer(port)
        #Thread configuration and execution
        self.thread = Thread(target=self.runFor, args=(self.server,), daemon=prevail)
        self.thread.start()
    
    def stop(self) -> None:
        if self.server != None:
            self.server.close()
        if self.thread != None:
            self.stopServer()
            self.thread.join()

    @abstractmethod
    def managerMessage(self, message: dict, sck : ISocket):
        pass