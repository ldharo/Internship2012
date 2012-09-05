import treeClass
import parser
import sys

from pypy.rlib.jit import JitDriver, elidable

##########################
# Class Function for CPS #
##########################

class Contk:
    def __init__(self):
        pass
    
    def apply(self,arg):
        return arg

class Idk(Contk):
    def __init__(self):
        pass
    
    def apply(self,arg):
        return arg

class Opk(Contk):
    def __init__(self,argLeft,op,k):
        self.argLeft=argLeft
        self.op=op
        self.k=k


    def apply(self,arg):
        if self.op == '+':
            return self.k.apply(self.argLeft + arg)
        elif self.op == '-':
            return self.k.apply(self.argLeft - arg)
        elif self.op == '*':
            return self.k.apply(self.argLeft * arg)
        elif self.op == '/':
            return self.k.apply(self.argLeft / arg)
        elif self.op == '%':
            return self.k.apply(self.argLeft % arg)
        elif self.op == '=':
            if self.argLeft - arg == 0:
                return self.k.apply(1)
            else:
                return self.k.apply(0)
        else:
            print("Parsing Error, symobl "+ self.op +" shouldn't be here.")
            return 2

class OpLeftk(Contk):
    def __init__(self, exprRight, funDict, env, k, op):
        self.exprRight=exprRight
        self.funDict=funDict
        self.env=env
        self.k=k
        self.op=op

    def apply(self, arg):
        return Interpk(self.exprRight,self.funDict,self.env, Opk(arg,self.op,self.k))

class Appk(Contk):
    def __init__(self, funName, funDict, k):
        self.funName=funName
        self.funDict=funDict
        self.k=k

    def apply(self, arg):
        g = GetFunc(self.funDict, self.funName)
        if not isinstance(g, treeClass.NoneFunc):
            return Interpk(g.body,self.funDict, {g.argName: arg}, self.k)
        else:
            return 2

class Ifk(Contk):
    def __init__(self, true, false, funDict, env, k):
        self.true=true
        self.false=false
        self.funDict=funDict
        self.env=env
        self.k=k

    def apply(self,arg):
        if arg != 0:
            return Interpk(self.true, self.funDict, self.env, self.k)
        else:
            return Interpk(self.false, self.funDict, self.env, self.k)

class Withk(Contk):
    def __init__(self, body, funDict, name, env, k):
        self.body = body
	self.funDict = funDict
        self.name = name
        self.env = env
        self.k = k

    def apply(self, arg):
        newEnv = self.env
        newEnv[self.name] = arg
        return Interpk(self.body, self.funDict, newEnv, self.k)

#################
# Interpret CPS #
#################
        
@elidable
def GetFunc(funDict, name):
    """Equivalent to funDict[name], but labelled as elidable in JITing version to be run faster by the JITing VM."""

    body = funDict.get(name, treeClass.NoneFunc())
    if isinstance(body, treeClass.NoneFunc) :
        print("Inexistant function : "+ name)
    return body

def GetInEnv(env, name):
    """Equivalent to env[name], but labelled as elidable to be run faster by the JITing VM."""

    try:
        val = env[name]
    except KeyError:
        print("Interpret Error: free identifier :\n" + name)
        val = 2
    return val

# JITing instructions

def get_printable_location(funDict, expr):
    return treeClass.treePrint(expr)

jitdriver = JitDriver(greens=['funDict', 'expr'], reds=['env', 'k'],
       get_printable_location = get_printable_location)

#Interpret CPS - tail recursive

def Interpk(expr, funDict, env, k):
    """ Interpret the ifF1WAE AST given a set of defined functions. We use deferred substituion and eagerness."""

    jitdriver.jit_merge_point(expr=expr, funDict=funDict, env=env, k=k)
    #
    if isinstance(expr, treeClass.Num):
        return k.apply(expr.n)
    #
    elif isinstance(expr, treeClass.Op):
        k2 = OpLeftk(expr.rhs, funDict, env, k, expr.op)
        return Interpk(expr.lhs, funDict, env, k2)
    #
    elif isinstance(expr, treeClass.With):
	k2 = Withk(expr.body, funDict, expr.name, env, k)	
        return Interpk(expr.nameExpr, funDict, env, k2)
    #
    elif isinstance(expr, treeClass.Id):
        return k.apply(GetInEnv(env, expr.name))
    #
    elif isinstance(expr, treeClass.App):
        k = Appk(expr.funName, funDict, k)
	expr = expr.arg
        jitdriver.can_enter_jit(expr=expr, funDict=funDict, env=env, k=k)
        return Interpk(expr, funDict, env, k)
    #
    elif isinstance(expr, treeClass.If):
        return Interpk(expr.cond,funDict,env,Ifk(expr.ctrue,expr.cfalse,funDict,env,k))
    #
    else: # Not an <ifF1WAE>
        print("Argument of Interpk is not a <ifF1WAE>:\n")
        return 2
    #

#############################    
# Translation and execution #
#############################

def Main(file):
    t,d = parser.Parse(file)
    j = Interpk(t,d,{},Idk())
    print("the answer is :" + str(j))

import os

def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()

def run(fp):
    program_envents = ""
    while True:
        read = os.read(fp, 4096)
        if len(read) == 0:
            break
        program_envents += read
    os.close(fp)
    Main(program_envents)

def entry_point(argv):
    try:
        filename = argv[1]
    except IndexError:
        print "You must supply a filename"
        return 1

    run(os.open(filename, os.O_RDONLY, 0777))
    return 0


def target(*args):
    return entry_point, None

if __name__ == "__main__":
    entry_point(sys.argv)
