from abc import ABCMeta, abstractmethod
import atexit

class Stoppable(metaclass=ABCMeta):
    def __init__(self) -> None:
        atexit.register(self.stop)

    @abstractmethod
    def stop(self) -> None:
        pass