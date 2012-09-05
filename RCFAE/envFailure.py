
class Map(object):
    def __init__(self):
        self.indexes = {}
        self.other_maps = {}

    def getindex(self, name):
        return self.indexes.get(name, -1)

    def add_attribute(self, name):
        if name not in self.other_maps:
            newmap = Map()
            newmap.indexes.update(self.indexes)
            newmap.indexes[name] = len(self.indexes)
            self.other_maps[name] = newmap
        return self.other_maps[name]

EMPTY_MAP = Map()

class FreeVariable(Exception):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return self.name

class Env(object):
    def __init__(self):
        self.map = EMPTY_MAP
        self.storage = []
        
    def get_attr(self, name):
        map = self.map
        index = map.getindex(name)
        if index != -1:
            return self.storage[index]
        else:
            raise FreeVariable(name)

    def write_attribute(self, name, value):
        assert isinstance(name, str)
        map = self.map
        index = map.getindex(name)
        if index != -1:
            self.storage[index] = value
            return
        self.map = map.add_attribute(name)
        self.storage.append(value)
        
def showFailure(env, i):
    env.write_attribute("x", i)
    env2 = env
    print "first"
    print "x in env : %s\nx in env2 : %s" % (str(env.get_attr("x")), str(env2.get_attr("x")))
    env.write_attribute("x", i-1)
    print "second"
    print "x in env : %s\nx in env2 : %s" % (str(env.get_attr("x")), str(env2.get_attr("x")))

print "Try with Env"
showFailure(Env(), 3)
print ""
print "Try with doct"
env = {"x":3}
env2 = env
print "x in env : %s\nx in env2 : %s" % (str(env["x"]), str(env2["x"]))
env["x"] = 2
print "x in env : %s\nx in env2 : %s" % (str(env["x"]), str(env2["x"]))
