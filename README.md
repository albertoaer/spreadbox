# SpreadBox

# Archived!

- Due to poor serialization system and bad approach the project has been abandoned
- The new one project is [Betterbox](https://github.com/albertoaer/betterbox), check it out 😀

## What is SpreadBox?
SpreadBox is a set of tools to share and run python code among a distributed group of systems

## What is a Box?

A box is an abstracted entry point for remote users storage and workspace deployment, besides execution of dynamic remote code

### How to create a box

Easy way is to inherit any premaded box
```python
class BoxClass(Box):
    def name(self) -> str : return 'MyBox'
    def on(self) -> bool: return True
    def overload(self) -> int: return 0
```

### How to deploy a box

```python
box = BoxClass() #create a box instance
box.serve(303) #serve the box at a port
```

### How to connect to a box

```python
#Use Box.seek for a collection of IPs (fastest way)
available = Box.seek(('XXX.XXX.XXX','XXX.XXX.XXX'), (303,304))

#Look through all the network for available boxes at some port
available = Box.network(303)
```