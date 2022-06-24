from spreadbox import Box, wrap

class MyBox(Box):
    def name(self): return 'MyBox'

@wrap()
def factorial(x : int):
    if x < 0: assert False, "expecting positive number"
    if x < 2: return 1
    return factorial(x-1)*x

def server():
    box = MyBox()
    print(box.name())
    box.serve(303)

def client():
    available = Box.network(303)
    print(available)
    #factorial.spread(available)

if __name__ == "__main__":
    server()
    client()
    #print(factorial)
    #print(repr(factorial))