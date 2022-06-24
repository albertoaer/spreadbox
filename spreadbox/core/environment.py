from abc import ABC, abstractmethod
import atexit

class Stoppable(ABC):
    def __init__(self) -> None:
        atexit.register(self.stop)

    @abstractmethod
    def stop(self) -> None:
        pass