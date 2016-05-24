#!/usr/bin/env python3
import collections
from .. import utils
from . import scope as sp
from . import dast
from verifier.ir import *

def argument_template(*items):
    return {item : idx for idx, item in enumerate(items)}

def maybe_has_side_effect(node):
    # FIXME
    return False

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

    def __init__(self, function : Function, functions : dict):
        self.function = function
        self.functions = functions
        self.scope = function.scope
        self.node = function.ast_node
        self.tempvar_idx = 0
        self.label_dict = dict()
        self.blocks = [self.new_block(self.new_label("label"))]
        self.block_stack = [self.blocks[0]]

    def post_run(self, result):
        self.function.basicblocks = self.blocks

    def append_inst(self, inst):
        self.block_stack[-1].append_inst(inst)

    def new_block(self, *args, **kwargs):
        return BasicBlock(self.function, *args, **kwargs)

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
            return node.value.expr.expr.name
        return None

    def is_assign_simple(self, node : dast.ExprStmt):
        return len(node.target_list) == 0 or (len(node.target_list) == 1 and not isinstance(node.target_list[0], dast.TupleExpr))

    def visit_PassStmt(self, node : dast.PassStmt):
        pass

    def visit_ExprStmt(self, node : dast.ExprStmt):
        label = self.is_label(node)
        if label is not None:
            self.append_inst(Label(label))
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
            for target in reversed(targets):
                if isinstance(target, Tuple):
                    for idx, element in enumerate(target.operands):
                        self.append_inst(Assign(element, node.op,
                                                SubScript(result, [Constant(idx)])))
                else:
                    self.append_inst(Assign(target, node.op, result))

    def visit_GlobalStmt(self, node):
        pass

    def visit_NonlocalStmt(self, node):
        pass

    def visit_ForStmt(self, node : dast.ForStmt):
        iter =  self.visit(node.iter)
        for_cond = self.new_block(self.new_label("for"))
        for_body = self.new_block(self.new_label("for_body"))
        iter_var = self.tempvar()
        target_var = self.visit(node.target)
        self.append_inst(Assign(iter_var, "=", iter))

        elsebody = endblock = self.new_block(self.new_label("for_end"))
        if node.elsebody is not None:
            elsebody = self.new_block(self.new_label("for_else"))

        with BlockSetter(self, for_cond):
            self.append_inst(CondBranch(IsEmpty(iter_var), elsebody, for_body))

        with BlockSetter(self, for_body):
            self.append_inst(Assign(Tuple([target_var, iter_var]), "=", PopOneElement(iter_var, Constant(0))))
            self.visit_one_value(node.body)
            self.append_inst(Branch(for_cond))

        if node.elsebody is not None:
            with BlockSetter(self, elsebody):
                self.visit_one_value(node.elsebody)

        self.set_block(endblock)

    def visit_IfStmt(self, node : dast.IfStmt):
        # block structure looks like this:
        #           cond
        #           |      \
        #        if_block  elif cond-------\
        #           |       |              else_block
        #           |      elif_block      |
        #           |      /              /
        #           |     /        /------
        #        endif_block
        cond = self.visit(node.cond)
        if_block = self.new_block(self.new_label("if"))
        endif_block = self.new_block(self.new_label("endif"))

        # get a copy of the list
        else_nodes = list(node.elif_list)
        if node.elsebranch is not None:
            else_nodes.append(dast.ElseIf(None, node.elsebranch))

        if else_nodes:
            else_block = self.new_block(self.new_label(if_block.label + "_else"))
        else:
            else_block = endif_block

        self.append_inst(CondBranch(cond, if_block, else_block))
        with BlockSetter(self, if_block):
            self.visit_one_value(node.branch)
            if else_block is not endif_block:
                self.append_inst(Branch(endif_block))

        while else_nodes:
            # elif_cond will be None if it's else instead of elif
            elif_node = else_nodes.pop(0)
            elif_cond = elif_node.cond
            elif_body = elif_node.branch
            next_else_block = self.new_block(self.new_label(if_block.label + "_else")) if else_nodes else endif_block
            if elif_cond is not None:
                with BlockSetter(self, else_block):
                    cond = self.visit(elif_cond)
                    else_block = self.new_block(self.new_label(if_block.label + "_elif"))
                    self.append_inst(CondBranch(cond, else_block, next_else_block))

            # if cond holds, enter here
            with BlockSetter(self, else_block):
                self.visit_one_value(elif_body)
                if else_nodes:
                    self.append_inst(Branch(endif_block))
            # if cond not holds, enter here
            else_block = next_else_block

        self.set_block(endif_block)

    def visit_WhileStmt(self, node : dast.WhileStmt):
        while_cond_body = self.new_block(self.new_label("while"))
        while_body = self.new_block(self.new_label("while_body"))
        elsebody = endblock = self.new_block(self.new_label("while_end"))
        if node.elsebody is not None:
            elsebody = self.new_block(self.new_label("while_else"))

        with BlockSetter(self, while_cond_body):
            cond = self.visit(node.cond)
            self.append_inst(CondBranch(cond, while_body, elsebody))

        with BlockSetter(self, while_body):
            self.visit_one_value(node.body)
            self.append_inst(Branch(while_cond_body))

        if node.elsebody is not None:
            with BlockSetter(self, elsebody):
                self.visit_one_value(node.elsebody)

        self.set_block(endblock)

    def visit_ReturnStmt(self, node : dast.ReturnStmt):
        value = Constant(None) if node.exprs is None else self.visit_one_value(node.exprs)
        self.append_inst(Return(value))

    def visit_YieldStmt(self, node : dast.YieldStmt):
        # not used in any examples
        raise NotImplementedError()

    def visit_scope(self, node):
        if node is self.node:
            self.visit_one_value(node.body)
        else:
            self.append_inst(Assign(Variable(node.name), "=", self.functions[node]))

    # don't cross the bonduary of scope
    def visit_ClassDef(self, node : dast.ClassDef):
        # When a python class is defined, this need to be executed immediately.
        if node is not self.node:
            self.append_inst(Call(self.functions[node], [], None, [], None))
        self.visit_scope(node)

    def visit_FuncDef(self, node : dast.FuncDef):
        if self.scope.type == sp.ScopeType.ReceiveHandler:
            for arg in node.args.args:
                if arg.name == 'msg':
                    pattern = arg.value
            self.function.msg_pattern = self.visit(pattern)
        self.visit_scope(node)

    def visit_IfElseExpr(self, node : dast.IfElseExpr):
        # We convert it into a if else stmt like thing
        cond = self.visit(node.cond)
        var = self.tempvar()

        if_block = self.new_block(self.new_label("if"))
        else_block = self.new_block(self.new_label("else"))
        endif_block = self.new_block(self.new_label("endif"))
        self.append_inst(CondBranch(cond, if_block, else_block))
        with BlockSetter(self, if_block):
            ifvalue = self.visit(node.ifvalue)
            self.append_inst(Assign(var, "=", ifvalue))
            self.append_inst(Branch(endif_block))
        with BlockSetter(self, else_block):
            elsevalue = self.visit(node.elsevalue)
            self.append_inst(Assign(var, "=", elsevalue))

        self.set_block(endif_block)
        return var


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

    def visit_LogicExpr(self, node : dast.LogicExpr):
        if maybe_has_side_effect(node):
            end_block = self.new_block(self.new_label(node.op + "_end"))
            if_blocks = [self.new_block(self.new_label(node.op + "_if")) for _ in node.conds[:-1]]
            tempvars = [self.tempvar() for _ in node.conds[:-1]]
            else_blocks = [self.new_block(self.new_label(node.op + "_else")) for _ in node.conds[:-1]]
            result = self.tempvar()
            for idx, cond in enumerate(node.conds):
                value = self.visit(cond)
                if node.op == "and":
                    if idx + 1 == len(node.conds):
                        self.append_inst(Assign(result, "=", value))
                        self.append_inst(Branch(end_block))
                    else:
                        self.append_inst(Assign(tempvars[idx], "=", value))
                        self.append_inst(CondBranch(tempvars[idx], if_blocks[idx], else_blocks[idx]))
                        self.set_block(if_blocks[idx])
                else: # node.op == "or"
                    if idx + 1 == len(node.conds):
                        self.append_inst(Assign(result, "=", value))
                        self.append_inst(Branch(end_block))
                    else:
                        self.append_inst(Assign(tempvars[idx], "=", value))
                        self.append_inst(CondBranch(tempvars[idx], if_blocks[idx], else_blocks[idx]))
                        self.set_block(if_blocks[idx])
                        self.append_inst(Assign(result, "=", tempvars[idx]))
                        self.append_inst(Branch(end_block))
                        self.set_block(else_blocks[idx])
            for idx, cond in enumerate(node.conds):
                if node.op == "and" and idx + 1 < len(node.conds):
                    self.set_block(else_blocks[idx])
                    self.append_inst(Assign(result, "=", tempvars[idx]))
                    self.append_inst(Branch(end_block))

            self.set_block(end_block)

            return result
        else:
            return LogicOp(node.op, self.visit_one_value(node.conds))

    def visit_UnaryExpr(self, node : dast.UnaryExpr):
        expr = self.visit(node.expr)
        return UnaryOp(node.op, expr)

    def visit_Boolean(self, node : dast.Boolean):
        return Constant(node.boolean)

    def visit_CompListMaker(self, node : dast.CompListMaker):
        if node.expr is None:
            # empty list
            return List([])
        else:
            raise NotImplementedError()

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
        # print(args, vargs, args2, kwargs, kwarg)
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

    def handle_domain(self, node):
        pass

    def handle_predicate(self, node):
        # print(node)
        pass

    def handle_int(self, node, args, vargs, args2, kwargs, kwarg):
        n, base = self.check_argument(argument_template('n', 'base'), args, vargs, args2, kwargs, kwarg)
        # TODO base
        return Integer(n)

    def handle_len(self, node, args, vargs, args2, kwargs, kwarg):
        len, = self.check_argument(argument_template('object'), args, vargs, args2, kwargs, kwarg)
        if len is None:
            raise SyntaxError("len")
        return Cardinality(len)

    def handle_range(self, node, args, vargs, args2, kwargs, kwarg):
        value, start, stop = self.check_argument(argument_template('value', 'start', 'stop'), args, vargs, args2, kwargs, kwarg)
        if value is None:
            raise SyntaxError("range")
        # TODO start, top
        return Range(value)

    def handle_quantifier(self, tp, node):
        kwarg = { arg.name : idx for idx, arg in enumerate(node.args.args) if arg.name is not None}
        domain = node.args.args[0].value
        if "has" in kwarg:
            predicate = self.visit(node.args.args[kwarg['has']].value)
        else:
            predicate = Constant(True)
        if tp == "each":
            return Quantifier(tp, self.visit(domain), predicate)
        elif tp == "some":
            return Quantifier(tp, self.visit(domain), predicate)
        else:
            raise NotImplementedError("Unknown Quantifier Type {0}".format(tp))

    def handle_message_history(self, tp, node):
        # TODO
        pattern = self.visit(node.args.args[0].value)
        return Received(pattern)

    def handle_work(self, node, args, vargs, args2, kwargs, kwarg):
        return

    def visit_ApplyExpr(self, node : dast.ApplyExpr):
        if isinstance(node.expr, dast.Name):
            if node.expr.name == "each":
                return self.handle_quantifier("each", node)
            elif node.expr.name == "received" or node.expr.name == "sent":
                return self.handle_message_history(node.expr.name, node)
            elif node.expr.name == "any":
                return self.handle_quantifier("some", node)
            elif node.expr.name == "await":

                await_cond_block = self.new_block(self.new_label("await"))
                await_block = self.new_block(self.new_label("await_body"))
                end_block = self.new_block(self.new_label("await_end"))
                with BlockSetter(self, await_cond_block):
                    self.append_inst(Label("await"))
                    value = self.visit(node.args.args[0].value)
                    self.append_inst(CondBranch(value, end_block, await_block))

                with BlockSetter(self, await_block):
                    self.append_inst(Branch(await_cond_block))
                self.set_block(end_block)
                return


        builtin_function = {"new", "start", "config", "send", "setup", # api
                            "logical_clock", "incr_logical_clock", "work", "exit", "output",  #builtin
                            "int", "len", "range", # Python builtin
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
        return Variable(node.name)

    def visit_String(self, node : dast.String):
        return Constant("".join(node.strs))

    def visit_Number(self, node: dast.Number):
        return Constant(node.number)

    def visit_PropertyExpr(self, node: dast.PropertyExpr):
        result = self.visit(node.expr)
        return Property(result, node.name)

    def visit_SubscriptExpr(self, node: dast.SubscriptExpr):
        result = self.visit(node.expr)
        subscripts = [self.visit(subscript) for subscript in node.subscripts]
        return SubScript(result, subscripts)

    def visit_EnumSetMaker(self, node: dast.EnumSetMaker):
        result = self.visit_one_value(node.items)
        return Set(result)

class Translator(object):
    def __init__(self):
        pass

    def run(self, name, ast):
        self.scopes = sp.ScopeBuilder.run(ast)
        #for scope in self.scopes.values():
            #print(scope)
        module = Module(name)

        functions = dict()

        for node, scope in self.scopes.items():
            args = []
            if isinstance(node, dast.FuncDef):
                for arg in node.args.args:
                    args.append(Variable(arg.name))
            function = Function(module, node, scope, args)
            functions[node] = function

        for node, function in functions.items():
            ScopeTranslator.run(node, function, functions)
            module.add_function(function)

        return module


