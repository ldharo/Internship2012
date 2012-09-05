import treeClass
import parser
import sys

from pypy.rlib.jit import JitDriver, elidable

##########################
# Class Function for CPS #
##########################
class Contk(object):
    def __init__(self):
        pass

class Endk(Contk):
    def __init__(self):
        pass

    def apply(self, arg):
        return NoMoreBounce(arg)

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
            return NoMoreBounce(2)

class OpLeftk(Contk):
    def __init__(self, exprRight, funDict, env, k, op):
        self.exprRight=exprRight
        self.funDict=funDict
        self.env=env
        self.k=k
        self.op=op

    def apply(self, arg):
        return ToBounce(self.exprRight, self.env, Opk(arg,self.op,self.k))

class Appk(Contk):
    def __init__(self, funName, funDict, k):
        self.funName=funName
        self.funDict=funDict
        self.k=k

    def apply(self, arg):
        g = GetFunc(self.funDict, self.funName)
        if not isinstance(g, treeClass.NoneFunc):
            return ToBounce(g.body, {g.argName: arg}, self.k)
        else:
            return NoMoreBounce(2)


class Ifk(Contk):
    def __init__(self, true, false, funDict, env, k):
        self.true=true
        self.false=false
        self.funDict=funDict
        self.env=env
        self.k=k

    def apply(self,arg):
        if arg != 0:
            return ToBounce(self.true, self.env, self.k)
        else:
            return ToBounce(self.false, self.env, self.k)

class Withk(Contk):
    def __init__(self, body, name, env, k):
        self.body = body
        self.name = name
        self.env = env
        self.k = k

    def apply(self, arg):
        self.env[self.name] = arg
        return ToBounce(self.body, self.env, self.k)

##########
# Bounce #
##########

class Bounce:
    def __init__(self):
        pass

class ToBounce(Bounce):
    def __init__(self, expr, env, k):
        self.expr = expr
        self.env = env
        self.k = k

class NoMoreBounce(Bounce):
    def __init__(self,value):
        self.value = value

##############
# Trampoline #
##############

def Trampoline(bouncer, funDict):
    """ Interpret the ifF1WAE AST given a set of defined functions, one step at a time. We use deferred substituion and eagerness."""

    assert isinstance(bouncer, ToBounce)
    expr = bouncer.expr
    env = bouncer.env
    k = bouncer.k
    
    #
    if isinstance(expr, treeClass.Num):
        return k.apply(expr.n)
    #
    elif isinstance(expr, treeClass.Op):
        k2 = OpLeftk(expr.rhs, funDict, env, k, expr.op)
        return ToBounce(expr.lhs, env, k2)
    #
    elif isinstance(expr, treeClass.With):
        k2 = Withk(expr.body, expr.name, env, k)
        return ToBounce(expr.nameExpr, env, k2)
    #
    elif isinstance(expr, treeClass.Id):
        arg = GetInEnv(env, expr.name)
        return k.apply(arg)
    #
    elif isinstance(expr, treeClass.App):
        return ToBounce(expr.arg, env, Appk(expr.funName, funDict, k))
    #
    elif isinstance(expr, treeClass.If):
        return ToBounce(expr.cond, env, Ifk(expr.ctrue,expr.cfalse,funDict,env,k))
    #
    else: # Not an <instr>
        print("Argument of Interpk is not a <instr>:\n")
        return NoMoreBounce(2)
    #
    
@elidable
def GetFunc(funDict, name):
    """Equivalent to funDict[name], but labelled as elidable in JITing version to be run faster by the JITing VM."""

    body = funDict.get(name, treeClass.NoneFunc())
    if isinstance(body, treeClass.NoneFunc) :
        print("Inexistant function : "+ name)
    return body

def GetInEnv(env, name):
    """Equivalent to env[name]."""

    try:
        val = env[name]
    except KeyError:
        print("Interpret Error: free identifier :\n" + name)
        val = 2
    return val

# JITing instructions

def get_printable_location(funDict, expr):
    return treeClass.treePrint(expr)

jitdriver = JitDriver(greens=['funDict', 'expr'], reds=['bouncer', 'env'],
        get_printable_location=get_printable_location)

def Interp(expr, funDict, env, k):

    bouncer = ToBounce(expr, env, k)
    
    while 1:

        jitdriver.jit_merge_point(funDict=funDict, bouncer=bouncer, expr=expr, env=env)
        if isinstance(bouncer, NoMoreBounce):
            break
        elif isinstance(bouncer, ToBounce):
            expr = bouncer.expr
            env = bouncer.env
            
            if isinstance(expr, treeClass.App):
                enter = True
            else:
                enter = False
            bouncer = Trampoline(bouncer, funDict)
            if enter:
                expr = bouncer.expr
                env = bouncer.env
                jitdriver.can_enter_jit(funDict=funDict, bouncer=bouncer, expr=expr, env=env)
                
    assert isinstance(bouncer, NoMoreBounce)
    return bouncer.value

#############################    
# Translation and execution #
#############################

def Main(file):
    t,d = parser.Parse(file)
    j = Interp(t,d,{},Endk())
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
