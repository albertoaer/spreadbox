from spreadbox import Box, wrap, shared
from spreadbox.network.utils import ip

class MyBox(Box):
    x : int = 0
    def name(self) -> str : return 'MyBox'
    def on(self) -> bool: return True
    def overload(self) -> int: return 0
    @shared(True)
    def stored(self) -> None: return self.x
    @shared(True)
    def sum(self,y) -> None: self.x+=y

@wrap()
def factorial(x : int):
    if x < 0: assert False, "expecting positive number"
    if x < 2: return 1
    return factorial(x-1)*x

def server():
    box = MyBox()
    box.serve(303, False)

def client():
    box = Box.get(ip()[-1], 303).group()
    box.set(factorial=factorial)
    print(box.call('factorial', 5))
    box.call('sum', 2)
    box.call('sum', 3)
    print(box.call('stored'))
    #print(boxes.spread([factorial.make(3), factorial.make(5)]))

if __name__ == "__main__":
    server()
    client()