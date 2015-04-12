#!/usr/bin/env python3

import itertools

class AstNode(object):
    _fields=[]

class Program(AstNode):
    _fields=["stmts"]

    def __init__(self, stmts):
        self.stmts = stmts

class ExprStmt(AstNode):
    _fields=["targets_list", "op", "value"]

    def __init__(self, targets_list, op, value):
        self.targets_list = targets_list
        self.op = op
        self.value = value

class IfElseExpr(AstNode):
    _fields=["ifvalue", "cond", "elsevalue"]

    def __init__(self, ifvalue, cond, elsevalue):
        self.ifvalue = ifvalue
        self.cond = cond
        self.elsevalue = elsevalue

class LogicExpr(AstNode):
    _fields=["op", "conds"]
    def __init__(self, op, conds):
        self.op = op
        self.conds = conds

class UnaryExpr(AstNode):
    _fields = ["op", "expr"]
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

class BinaryExpr(AstNode):
    _fields = ["op", "left", "right"]
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class PropertyExpr(AstNode):
    _fields = ["expr", "name"]
    def __init__(self, expr, name):
        self.expr = expr
        self.name = name

class ApplyExpr(AstNode):
    _fields = ["expr", "args"]
    def __init__(self, expr, args):
        self.expr = expr
        self.args = args

class SubscriptExpr(AstNode):
    _fields = ["expr", "subscripts"]
    def __init__(self, expr, subscripts):
        self.expr = expr
        self.subscripts = subscripts

class DelStmt(AstNode):
    _fields = ["exprs"]
    def __init__(self, exprs):
        self.exprs = exprs

class PassStmt(AstNode): pass
class BreakStmt(AstNode): pass
class ContinueStmt(AstNode): pass

class ReturnStmt(AstNode):
    _fields = ["exprs"]
    def __init__(self, exprs):
        self.exprs = exprs

class YieldStmt(AstNode):
    _fields = ["expr"]
    def __init__(self, expr):
        self.expr = expr

class YieldExpr(AstNode):
    _fields = ["expr"]
    def __init__(self, expr):
        self.expr = expr

class YieldFrom(AstNode):
    _fields = ["expr"]
    def __init__(self, expr):
        self.expr = expr

class RaiseStmt(AstNode):
    _fields = ["expr", "source"]
    def __init__(self, expr, source):
        self.expr = expr
        self.source = source

class GlobalStmt(AstNode):
    _fields = ["names"]
    def __init__(self, names):
        self.names = names;

class NonLocalStmt(AstNode):
    _fields = ["names"]
    def __init__(self, names):
        self.names = names;

class AssertStmt(AstNode):
    _fields = ["cond", "expr"]
    def __init__(self, cond, expr):
        self.cond = cond
        self.expr = expr

class IfStmt(AstNode):
    _fields = ["cond", "branch"]
    def __init__(self, cond, branch):
        self.cond = cond
        self.branch = branch

class WhileStmt(AstNode):
    _fields = ["cond", "body", "elsebody"]
    def __init__(self, cond, body, elsebody):
        self.cond = cond
        self.body = body
        self.elsebody = elsebody

class ImportStmt(AstNode):
    _fields = ["imported_as", "path"]
    def __init__(self, imported_as, path = None):
        self.imported_as = imported_as
        self.path = path

class ImportName(AstNode):
    _fields = ["name", "asname"]
    def __init__(self, name, asname):
        self.name = name
        self.asname = asname

class ForStmt(AstNode):
    _fields = ["target", "iter", "body", "elsebody"]
    def __init__(self, target, iter, body, elsebody):
        self.iter = iter
        self.target = target
        self.body = body
        self.elsebody = elsebody

class EnumDictMaker(AstNode):
    _fields = ["items"]
    def __init__(self, items):
        self.items = items

class CompDictMaker(AstNode):
    _fields = ["key", "value", "comp"]
    def __init__(self, key, value, comp):
        self.key = key
        self.value = value
        self.comp = comp

class EnumSetMaker(AstNode):
    _fields = ["items"]
    def __init__(self, items):
        self.items = items

class CompSetMaker(AstNode):
    _fields = ["item", "comp"]
    def __init__(self, item, comp):
        self.item = item
        self.comp = comp

class ClassDef(AstNode):
    _fields = ["name", "args", "body"]
    def __init__(self, name, args, body):
        assert(isinstance(args, ArgList))
        self.name = name
        self.args = args
        self.body = body

class FuncDef(AstNode):
    _fields = ["name", "args", "ret_type", "body"]
    def __init__(self, name, args, ret_type, body):
        self.name = name
        self.args = args
        self.ret_type = ret_type
        self.body = body

class TypedArgList(AstNode):
    _fields = ["args", "vargs", "args2", "kwargs"]
    def __init__(self, args, vargs = None, args2 = [], kwargs = None):
        self.args2 = args2
        self.args = args
        self.kwargs = kwargs
        self.vargs = vargs

class ArgList(AstNode):
    _fields = ["args", "vargs", "args2", "kwargs"]
    def __init__(self, args, vargs = None, args2 = [], kwargs = None):
        self.args2 = args2
        self.args = args
        self.kwargs = kwargs
        self.vargs = vargs
        # a validation
        # python 3.4 is still using this stupid syntax
        found_keyword_arg = False
        for arg in itertools.chain(args, args2):
            # sanity check
            assert(isinstance(arg, Argument))
            if arg.name is not None:
                found_keyword_arg = True

            if arg.name is None and found_keyword_arg:
                raise SyntaxError("non-keyword arg after keyword arg")

class Argument(AstNode):
    _fields = ["name", "value", "tp"]
    def __init__(self, name, value, tp=None):
        self.name = name
        self.value = value
        self.tp = tp

class CompForExpr(AstNode):
    _fields = ["value_list", "comp"]
    def __init__(self, value_list, comp):
        self.value_list = value_list
        self.comp = comp

class CompFor(AstNode):
    _fields = ["target", "iter", "sub"]
    def __init__(self, target, iter, sub):
        self.target = target
        self.iter = iter
        self.sub = sub

class CompIf(AstNode):
    _fields = ["cond", "sub"]
    def __init__(self, cond, sub):
        self.cond = cond
        self.sub = sub
class Lambda(AstNode):
    _fields = ["args", "body"]
    def __init__(self, args, body):
        self.args = args
        self.body = body

class Name(AstNode):
    _fields = ["name"]
    def __init__(self, name):
        self.name = name

class Number(AstNode):
    _fields = ["number"]
    def __init__(self, number):
        self.number = number

class Boolean(AstNode):
    _fields = ["boolean"]
    def __init__(self, boolean):
        self.boolean = boolean

class EllipsisNode(AstNode):
    def __init__(self):
        pass

class NoneNode(AstNode):
    def __init__(self):
        pass

class String(AstNode):
    _fields = ["strs"]
    def __init__(self, strs):
        self.strs = strs

class TupleExpr(AstNode):
    _fields = ["subs"]
    def __init__(self, subs):
        self.subs = subs
