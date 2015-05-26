#!/usr/bin/env python3
from . import utils
from . import scope as sp
from . import dast
#from . import tlaast

class Label(object):
    def __repr__(self):
        return "<Label>"

class Variable(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Variable {0}>".format(self.name)

class Send(object):
    def __init__(self, value, to):
        self.value = value
        self.to = to

    def __repr__(self):
        return "<Send {0} {1}>".format(self.value, self.to)

# API, see api.py, accept dict, list, or pid
class Start(object):
    def __init__(self, process, args):
        self.process = process
        self.args = args

    def __repr__(self):
        return "<Start {0} {1}>".format(self.process, self.args)

class Setup(object):
    def __init__(self, process, args):
        self.process = process
        self.args = args

    def __repr__(self):
        return "<Setup {0} {1}>".format(self.process, self.args)

class New(object):
    def __init__(self, process_type, num):
        self.process_type = process_type
        self.num = num

    def __repr__(self):
        return "<New {0} {1}>".format(self.process_type, self.num)

class Config(object):
    def __init__(self, properties):
        self.properties = properties

    def __repr__(self):
        return "<Config {0}>".format(self.properties)

class Tuple(object):
    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return "<Tuple {0}>".format(self.items)


class Clock(object):
    def __repr__(self):
        return "<Clock>"

class Constant(object):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "<Constant {0}>".format(self.value)

class Property(object):
    def __init__(self, value, name):
        self.value = value
        self.name = name

    def __repr__(self):
        return "<Property {0} {1}>".format(self.value, self.name)

class BinaryOp(object):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class UnaryOp(object):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

class Assign(object):
    def __init__(self, target, op, expr):
        self.target = target
        self.expr = expr
        self.op = op

    def __repr__(self):
        return "<Assign {0} {1} {2}>".format(self.target, self.op, self.expr)

class Call(object):
    def __init__(self, func, args, vargs, args2, kwargs):
        self.func = func
        self.args = args
        self.vargs = vargs
        self.args2 = args2
        self.kwargs = kwargs

    def __repr__(self):
        return "<Call {0} {1} {2} {3} {4}>".format(self.func, self.args, self.vargs, self.args2, self.kwargs)

class CondBranch(object):
    def __init__(self, cond, label):
        self.cond = cond
        self.label = label

    def __repr__(self):
        return "<CondBranch {0} {1}>".format(self.cond, self.label)

class Branch(object):
    def __init__(self, label):
        self.label = label

    def __repr__(self):
        return "<Branch {0}>".format(self.label)

def argument_template(*items):
    return {item : idx for idx, item in enumerate(items)}

class CodeBlock:
    def __init__(self, label = None):
        self.ir = []
        self.label = label

    def append_inst(self, inst):
        self.ir.append(inst)

class BlockSetter(object):
    def __init__(self, translator, block):
        self.block = block
        self.translator = translator
        self.translator.blocks.append(self.block)

    def __enter__(self):
        self.translator.block_stack.append(self.block)

    def __exit__(self, type, value, traceback):
        item = self.translator.block_stack.pop()

class ScopeTranslator(utils.NodeVisitor):
    _nodebaseclass = dast.AstNode
    _result = "blocks"

    def __init__(self, translator, scope : sp.Scope):
        self.scope = scope
        self.translator = translator
        self.node = scope.ast
        self.tempvar_idx = 0
        self.blocks = [CodeBlock()]
        self.block_stack = [self.blocks[0]]
        self.label_dict = dict()

    def append_inst(self, inst):
        self.block_stack[-1].append_inst(inst)

    def new_label(self, name = None):
        if name is None:
            name = "label"
        if name in self.label_dict:
            self.label_dict[name] += 1
            return "{0}_{1}".format(name, self.label_dict[name])
        else:
            self.label_dict[name] = 0
            return "{0}_0".format(name)

    def tempvar(self):
        self.tempvar_idx += 1
        return Variable("@temp{0}".format(self.tempvar_idx))

    def set_block(self, block):
        self.block_stack[-1] = block
        self.blocks.append(block)

    def visit(self, node):
        return super().visit(node)

    def visit_ImportStmt(self, node : dast.ImportStmt):
        #print(node.imported_as)
        pass

    def is_label(self, node : dast.ExprStmt):
        if isinstance(node, dast.ExprStmt) and \
           len(node.target_list) == 0 and \
           node.op == '=' and \
           isinstance(node.value, dast.UnaryExpr) and \
           node.value.op == '-' and \
           isinstance(node.value.expr, dast.UnaryExpr) and \
           node.value.expr.op == '-' and \
           isinstance(node.value.expr.expr, dast.Name):
            return True
        return False

    def is_assign_simple(self, node : dast.ExprStmt):
        return len(node.target_list) == 0 or (len(node.target_list) == 1 and not isinstance(node.target_list[0], dast.TupleExpr))

    def visit_PassStmt(self, node : dast.PassStmt):
        pass

    def visit_ExprStmt(self, node : dast.ExprStmt):
        if self.is_label(node):
            self.append_inst(Label())
            return

        result = self.visit(node.value)

        is_assign_simple = self.is_assign_simple(node)
        if not is_assign_simple and not isinstance(result, Variable):
            tempvar = self.tempvar()
            self.append_inst(Assign(tempvar, "=", result))
            result = tempvar

        targets = [self.visit(target) for target in node.target_list]

        if is_assign_simple:
            if len(targets) == 1:
                self.append_inst(Assign(targets[0], node.op, result))
        else:
            #TODO
            pass

        #self.visit_one_value(node.target_list)
        #self.append_inst(Assign())

    def visit_GlobalStmt(self, node):
        pass

    def visit_NonlocalStmt(self, node):
        pass

    def visit_ForStmt(self, node : dast.ForStmt):
        iter =  self.visit(node.iter)
        forbody = CodeBlock(self.new_label("for"))
        with BlockSetter(self, forbody):
            self.visit_one_value(node.body)
            self.append_inst(Branch(forbody.label))

        if node.elsebody is not None:
            elsebody = CodeBlock()
            with BlockSetter(self, elsebody):
                self.visit_one_value(node.elsebody)

        endblock = CodeBlock()
        self.set_block(endblock)

    def visit_IfStmt(self, node : dast.IfStmt):
        cond = self.visit(node.cond)
        ifbody = CodeBlock()
        else_block = CodeBlock()
        with BlockSetter(self, ifbody):
            self.visit_one_value(node.branch)

        self.set_block(else_block)
        for elif_cond, elif_body in node.elif_list:
            cond = self.visit(elif_cond)
            new_else_block = CodeBlock()
            with BlockSetter(self, else_block):
                self.visit_one_value(elif_body)

            else_block = new_else_block
            self.set_block(else_block)

        if node.elsebranch is not None:
            new_else_block = CodeBlock()
            with BlockSetter(self, else_block):
                self.visit_one_value(new_else_block)

            else_block = new_else_block
            self.set_block(else_block)


    def visit_ReturnStmt(self, node : dast.ReturnStmt):
        self.visit(node.exprs)
        self.append_inst()

    def visit_YieldStmt(self, node : dast.YieldStmt):
        # not used in any examples
        raise NotImplementedError()

    def visit_scope(self, node):
        if node is self.node:
            self.generic_visit(node)

    # don't cross the bonduary of scope
    def visit_ClassDef(self, node):
        self.visit_scope(node)

    def visit_FuncDef(self, node):
        self.visit_scope(node)

    def visit_IfElseExpr(self, node : dast.IfElseExpr):
        cond = self.visit(node.cond)

        ifvalue = self.visit(node.ifvalue)
        elsevalue = self.visit(node.elsevalue)

    def visit_ArgList(self, node : dast.ArgList):
        print(node)
        assert(False)

    def visit_Argument(self, node : dast.Argument):
        print(node)
        assert(False)

    def visit_BinaryExpr(self, node : dast.BinaryExpr):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return BinaryOp(node.op, left, right)

    def visit_UnaryExpr(self, node : dast.UnaryExpr):
        expr = self.visit(node.expr)
        return UnaryOp(node.op, expr)

    def handle_send(self, node, args, vargs, args2, kwargs, kwarg):
        assert(kwargs is None)
        assert(vargs is None)
        assert(len(args2) == 0)
        if "to" not in kwarg:
            raise SyntaxError("send")

        self.append_inst(Send(args[0], args[kwarg["to"]]))

    def check_argument(self, template, args, vargs, args2, kwargs, kwarg):
        positional = len(args) - len(kwarg)
        values = [None] * len(template)

        for name, idx in template.items():
            if name in kwarg and idx < positional:
                raise TypeError("multiple value")
            values[idx] = args[kwarg[name]] if name in kwarg else (args[idx] if idx < positional else None)

        return values

    def handle_start(self, node, args, vargs, args2, kwargs, kwarg):
        procs, arg = self.check_argument(argument_template('procs', 'args'), args, vargs, args2, kwargs, kwarg)
        if procs is None:
            raise SyntaxError("start")

        self.append_inst(Start(procs, arg if arg is not None else Constant(None)))

    def handle_setup(self, node, args, vargs, args2, kwargs, kwarg):
        procs, arg = self.check_argument(argument_template('procs', 'args'), args, vargs, args2, kwargs, kwarg)
        if procs is None:
            raise SyntaxError("setup")

        self.append_inst(Setup(procs, arg if arg is not None else Constant(None)))

    def handle_output(self, node, args, vargs, args2, kwargs, kwarg):
        # output is a no op for us
        pass

    def handle_logical_clock(self, node, args, vargs, args2, kwargs, kwarg):
        return Clock()

    def handle_config(self, node, args, vargs, args2, kwargs, kwarg):
        # TODO, not important for now
        pass

    def handle_new(self, node, args, vargs, args2, kwargs, kwarg):
        pcls, arg, num = self.check_argument(argument_template('pcls', 'args', 'num'), args, vargs, args2, kwargs, kwarg)
        if pcls is None:
            raise SyntaxError("new")

        if arg is not None:
            var = self.tempvar()
            self.append_inst(Assign(var, "=", New(pcls, num)))
            self.append_inst(Setup(var, arg))
            return var

        else:
            return New(pcls, num)

    def visit_ApplyExpr(self, node : dast.ApplyExpr):
        if isinstance(node.expr, dast.Name):
            if node.expr.name == "each":
                return
            elif node.expr.name == "received":
                return


        builtin_function = {"new", "start", "config", "send", "setup", # api
                            "logical_clock", "incr_logical_clock", "work", "exit", "output",  #builtin
                            }
        args = [self.visit(arg.value) for arg in node.args.args]
        vargs = self.visit(node.args.vargs) if node.args.vargs is not None else None
        args2 = [self.visit(arg.value) for arg in node.args.args2]
        kwargs = self.visit(node.args.kwargs) if node.args.kwargs is not None else None

        kwarg = { arg.name : idx for idx, arg in enumerate(node.args.args) if arg.name is not None}
        if isinstance(node.expr, dast.Name) and \
           node.expr.name in builtin_function:
            func = getattr(self, "handle_{0}".format(node.expr.name))
            result = func(node, args, vargs, args2, kwargs, kwarg)
            if result is None:
                return Constant(None)
            else:
                return result
        else:
            func = self.visit(node.expr)
            tempvar = self.tempvar()
            self.append_inst(Assign(tempvar, "=", Call(func, args, vargs, args2, kwargs)))
            return tempvar


    def visit_TupleExpr(self, node : dast.TupleExpr):
        return Tuple([self.visit(sub) for sub in node.subs])

    def visit_Name(self, node : dast.Name):
        return Variable(node)

    def visit_String(self, node : dast.String):
        return Constant("".join(node.strs))

    def visit_Number(self, node: dast.Number):
        return Constant(node.number)

    def visit_ClassDef(self, node : dast.ClassDef):
        if node is self.node:
            return self.visit_one_value(node.body)

    def visit_FuncDef(self, node : dast.FuncDef):
        if node is self.node:
            return self.visit_one_value(node.body)

    def visit_PropertyExpr(self, node: dast.PropertyExpr):
        result = self.visit(node.expr)
        return Property(result, node.name)


class Translator(object):
    def __init__(self, scopes):
        super().__init__()
        self.scopes = scopes

    def run(self):
        for node, scope in self.scopes.items():
            ir = ScopeTranslator.run(node, self, scope)
            print(scope)
            for i in ir:
                for j in i.ir:
                    print(j)
            print("---------")

