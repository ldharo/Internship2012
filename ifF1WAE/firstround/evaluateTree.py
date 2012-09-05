import treeClass
import parser

def depth(tree):

    if isinstance(tree, treeClass.Leaf):
        return 0
    elif isinstance(tree, treeClass.Op):
        lhs = depth(tree.lhs)
        rhs = depth(tree.rhs)
        return 1+max(lhs,rhs)
    else:
        print "Not arithmetic tree"
        return -1

def leafs(tree):

    if isinstance(tree, treeClass.Leaf):
        return 1
    elif isinstance(tree, treeClass.Op):
        lhs = leafs(tree.lhs)
        rhs = leafs(tree.rhs)
        return lhs + rhs
    else:
        print "Not arithmetic tree"
        return -1

def Main(file):
    t,d = parser.Parse(file)
    try:
        f = d["f"]
    except IndexError:
        print "Wrong supplied file"
    print "Depth : %s" % depth(f.body)
    print "Leafs : %s" % leafs(f.body)

if __name__ == "__main__":
    import sys
    try:
        with open(sys.argv[1],"r") as file:
                    prog = file.read()
                    Main(prog)
    except IndexError:
        print "You must supply a file"

