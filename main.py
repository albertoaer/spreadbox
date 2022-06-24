from spreadbox import Box, wrap, shared
from spreadbox.network.utils import ip

class MyBox(Box):
    def name(self) -> str : return 'MyBox'
    def on(self) -> bool: return True
    def overload(self) -> int: return 0
    @shared()
    def sum(x,y) -> None: return x+y

@wrap()
def factorial(x : int):
    if x < 0: assert False, "expecting positive number"
    if x < 2: return 1
    return factorial(x-1)*x

def server():
    box = MyBox()
    box.serve(303, False)

def client():
    box = Box.get(ip()[-1], 303)
    #box['factorial'] = factorial
    print(box.call('sum', 2, 3))
    #print(boxes.spread([factorial.make(3), factorial.make(5)]))

if __name__ == "__main__":
    server()
    client()