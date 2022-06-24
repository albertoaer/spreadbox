from spreadbox import Box, wrap
from spreadbox.network.utils import ip

class MyBox(Box):
    def name(self) -> str : return 'MyBox'
    def on(self) -> bool: return True
    def overload(self) -> int: return 0

@wrap()
def factorial(x : int):
    if x < 0: assert False, "expecting positive number"
    if x < 2: return 1
    return factorial(x-1)*x

def server():
    box = MyBox()
    box2 = MyBox()
    box.serve(303, False)
    box2.serve(304, False)

def client():
    available = Box.seek((ip()[-1],ip()[-1]), (303,304))
    print(available.spread([factorial.make(3), factorial.make(5)]))

if __name__ == "__main__":
    server()
    client()