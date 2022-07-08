from abc import abstractmethod
from typing import Dict, Tuple
from logging import Logger, getLogger
from ..environment import Stoppable
from .protocol import ISocket, Address, protocol
from threading import Thread

class ClientManager(Stoppable):
    def __init__(self, id : str = None) -> None:
        super().__init__()
        self.running : bool = False
        self.clients : Dict[Address, Tuple[ISocket,Thread]] = {}
        self.server : ISocket = None
        self.thread : Thread = None
        self.logger : Logger = getLogger(id or "Server")

    def stop_server(self):
        self.running = False

    def run(self):
        self.running = True
        self.logger.info("Running")
        while self.running:
            client : ISocket
            try:
                client = self.server.accept()
            except:
                self.running = False
            else:
                thread = Thread(target=self.attach_client, args=(client,))
                self.clients[client.addr] = (client, thread)
                thread.start()

    def attach_client(self, con: ISocket):
        while self.running:
            data = con.read()
            if data:
                self.handle_message(data, con)
            else:
                break #If no data is read the client must be gone
        del self.clients[con.addr]

    def serve(self, port : int, prevail : bool = True) -> None: #create a service that manage users
        if self.server != None:
            raise Exception('Already served')
        self.server = protocol().create_socket()
        self.server.into_server(port)
        #Thread configuration and execution
        self.thread = Thread(target=self.run, daemon=not prevail)
        self.thread.start()
    
    def stop(self) -> None:
        if self.server != None:
            self.server.close()
        if self.thread != None:
            self.stop_server()
            self.thread.join()

    @abstractmethod
    def handle_message(self, message: dict, sck : ISocket):
        pass