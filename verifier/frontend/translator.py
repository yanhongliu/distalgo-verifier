#!/usr/bin/env python3
import collections
from .. import utils
from . import scope as sp
from da.compiler import dast
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
    _nodebaseclass = dast.DistNode

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
        if isinstance(node, dast.Statement):
            # Looks like a hack, but await seems always has label.
            # and we need to handle branch there.
            if node.label and not isinstance(node, dast.AwaitStmt):
                self.append_inst(Label(node.label))
        return super().visit(node)

    def visit_Program(self, node: dast.Program):
        # avoid visit things twice
        self.visit_one_value(node.body)

    def visit_ImportStmt(self, node : dast.ImportStmt):
        #print(node.imported_as)
        pass

    def is_assign_simple(self, node : dast.AssignmentStmt):
        return len(node.targets) == 0 or (len(node.targets) == 1 and not isinstance(node.targets, dast.TupleExpr))

    def visit_PassStmt(self, node : dast.PassStmt):
        pass

    def visit_AssignmentStmt(self, node : dast.AssignmentStmt):
        result = self.visit(node.value)

        is_assign_simple = self.is_assign_simple(node)
        if not is_assign_simple and not isinstance(result, Variable):
            tempvar = self.tempvar()
            self.append_inst(Assign(tempvar, "=", result))
            result = tempvar

        targets = [self.visit(target) for target in node.targets]

        if is_assign_simple:
            if len(targets) == 1:
                self.append_inst(Assign(targets[0], node.operator if isinstance(node, dast.OpAssignmentStmt) else "=", result))
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
        iter =  self.visit(node.domain.domain)
        for_cond = self.new_block(self.new_label("for"))
        for_body = self.new_block(self.new_label("for_body"))
        iter_var = self.tempvar()
        target_var = self.visit(node.domain.pattern)
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
        cond = self.visit(node.condition)
        if_block = self.new_block(self.new_label("if"))
        endif_block = self.new_block(self.new_label("endif"))


        if node.elsebody is not None:
            else_block = self.new_block(self.new_label(if_block.label + "_else"))
        else:
            else_block = endif_block

        self.append_inst(CondBranch(cond, if_block, else_block))
        with BlockSetter(self, if_block):
            self.visit_one_value(node.body)
            if else_block is not endif_block:
                self.append_inst(Branch(endif_block))

        if node.elsebody is not None:
            # if cond holds, enter here
            with BlockSetter(self, else_block):
                self.visit_one_value(node.elsebody)

        self.set_block(endif_block)

    def visit_WhileStmt(self, node : dast.WhileStmt):
        while_cond_body = self.new_block(self.new_label("while"))
        while_body = self.new_block(self.new_label("while_body"))
        elsebody = endblock = self.new_block(self.new_label("while_end"))
        if node.elsebody is not None:
            elsebody = self.new_block(self.new_label("while_else"))

        with BlockSetter(self, while_cond_body):
            cond = self.visit(node.condition)
            self.append_inst(CondBranch(cond, while_body, elsebody))

        with BlockSetter(self, while_body):
            self.visit_one_value(node.body)
            self.append_inst(Branch(while_cond_body))

        if node.elsebody is not None:
            with BlockSetter(self, elsebody):
                self.visit_one_value(node.elsebody)

        self.set_block(endblock)

    def visit_ReturnStmt(self, node : dast.ReturnStmt):
        value = Constant(None) if node.value is None else self.visit_one_value(node.value)
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
    def visit_ClassStmt(self, node : dast.ClassStmt):
        # When a python class is defined, this need to be executed immediately.
        if node is not self.node:
            self.append_inst(Call(self.functions[node], [], None, None))
        self.visit_scope(node)

    # don't cross the bonduary of scope
    def visit_Process(self, node : dast.Process):
        # When a python class is defined, this need to be executed immediately.
        if node is not self.node:
            self.append_inst(Call(self.functions[node], [], None, None))
        self.visit_scope(node)

    def visit_Function(self, node : dast.Function):
        self.visit_scope(node)

    def visit_EventHandler(self, node : dast.EventHandler):
        envelop = Tuple([
            self.visit(next(iter(node.events[0].timestamps))) if node.events[0].timestamps else FreePattern(),
            self.visit(next(iter(node.events[0].sources))) if node.events[0].sources else FreePattern(),
            self.visit(next(iter(node.events[0].destinations))) if node.events[0].destinations else FreePattern()
            ])
        self.function.msg_pattern = Tuple([FreePattern(), envelop , self.visit(node.events[0].pattern)])
        utils.NodeDump.run(self.function.msg_pattern)
        self.visit_scope(node)

    def visit_IfExpr(self, node : dast.IfExpr):
        # We convert it into a if else stmt like thing
        cond = self.visit(node.condition)
        var = self.tempvar()

        if_block = self.new_block(self.new_label("if"))
        else_block = self.new_block(self.new_label("else"))
        endif_block = self.new_block(self.new_label("endif"))
        self.append_inst(CondBranch(cond, if_block, else_block))
        with BlockSetter(self, if_block):
            ifvalue = self.visit(node.body)
            self.append_inst(Assign(var, "=", ifvalue))
            self.append_inst(Branch(endif_block))
        with BlockSetter(self, else_block):
            elsevalue = self.visit(node.orbody)
            self.append_inst(Assign(var, "=", elsevalue))

        self.set_block(endif_block)
        return var

    def visit_Arguments(self, node : dast.Arguments):
        utils.debug(node)
        assert(False)

    def visit_BinaryExpr(self, node : dast.BinaryExpr):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return BinaryOp(node.operator, left, right)

    def visit_ComparisonExpr(self, node : dast.ComparisonExpr):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if node.comparator is dast.InOp and isinstance(node.left, dast.LiteralPatternExpr):
            return Quantifier(dast.ExistentialOp, [BinaryOp(node.comparator, left, right)], Constant(True))
        else:
            return BinaryOp(node.comparator, left, right)

    def visit_LogicalExpr(self, node : dast.LogicalExpr):
        if maybe_has_side_effect(node):
            end_block = self.new_block(self.new_label(node.operator + "_end"))
            if_blocks = [self.new_block(self.new_label(node.operator + "_if")) for _ in node.conds[:-1]]
            tempvars = [self.tempvar() for _ in node.conds[:-1]]
            else_blocks = [self.new_block(self.new_label(node.operator + "_else")) for _ in node.conds[:-1]]
            result = self.tempvar()
            for idx, cond in enumerate(node.subexprs):
                value = self.visit(cond)
                if node.operator is dast.AndOp:
                    if idx + 1 == len(node.subexprs):
                        self.append_inst(Assign(result, "=", value))
                        self.append_inst(Branch(end_block))
                    else:
                        self.append_inst(Assign(tempvars[idx], "=", value))
                        self.append_inst(CondBranch(tempvars[idx], if_blocks[idx], else_blocks[idx]))
                        self.set_block(if_blocks[idx])
                else: # node.operator is dast.OrOp
                    if idx + 1 == len(node.subexprs):
                        self.append_inst(Assign(result, "=", value))
                        self.append_inst(Branch(end_block))
                    else:
                        self.append_inst(Assign(tempvars[idx], "=", value))
                        self.append_inst(CondBranch(tempvars[idx], if_blocks[idx], else_blocks[idx]))
                        self.set_block(if_blocks[idx])
                        self.append_inst(Assign(result, "=", tempvars[idx]))
                        self.append_inst(Branch(end_block))
                        self.set_block(else_blocks[idx])
            for idx, cond in enumerate(node.subexprs):
                if node.op == "and" and idx + 1 < len(node.subexprs):
                    self.set_block(else_blocks[idx])
                    self.append_inst(Assign(result, "=", tempvars[idx]))
                    self.append_inst(Branch(end_block))

            self.set_block(end_block)

            return result
        else:
            return LogicOp(node.operator, self.visit_one_value(node.subexprs))

    def visit_UnaryExpr(self, node : dast.UnaryExpr):
        expr = self.visit(node.expr)
        return UnaryOp(node.op, expr)

    def visit_TrueExpr(self, node : dast.TrueExpr):
        return Constant(True)

    def visit_FalseExpr(self, node : dast.FalseExpr):
        return Constant(False)

    def visit_ListExpr(self, node : dast.ListExpr):
        if node.expr is None:
            # empty list
            return List([])
        else:
            raise NotImplementedError()

    def handle_send(self, node, args, vargs, kwargs, kwarg):
        assert(kwargs is None)
        assert(vargs is None)
        if "to" not in kwarg:
            raise SyntaxError("send")

        self.append_inst(Send(args[0], kwarg["to"]))

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

    def handle_output(self, node, args, vargs, kwargs, kwarg):
        # output is a no op for us
        pass

    def handle_logical_clock(self, node, args, vargs, kwargs, kwarg):
        return Clock()

    def handle_config(self, node, args, vargs, kwargs, kwarg):
        # TODO, not important for now
        pass

    def handle_new(self, node, args, vargs, kwargs, kwarg):
        pcls, arg, num = self.check_argument(argument_template('pcls', 'args', 'num'), args, vargs, kwargs, kwarg)
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

    def handle_randint(self, node, args, vargs, args2, kwargs, kwarg):
        value, = self.check_argument(argument_template('object'), args, vargs, args2, kwargs, kwarg)
        if value is None:
            raise SyntaxError("randint")
        print(value)
        return RandomSelect(value)

    def visit_PatternExpr(self, node: dast.PatternExpr):
        return self.visit_one_value(node.pattern)

    def visit_LiteralPatternExpr(self, node: dast.LiteralPatternExpr):
        return self.visit_one_value(node.pattern)

    def visit_FreePattern(self, node: dast.FreePattern):
        if node.value is None:
            return FreePattern()
        else:
            return self.visit_one_value(node.value)

    def visit_BoundPattern(self, node: dast.BoundPattern):
        return self.visit_one_value(node.value)

    def visit_ConstantPattern(self, node: dast.ConstantPattern):
        return self.visit_one_value(node.value)

    def visit_TuplePattern(self, node: dast.TuplePattern):
        return Tuple([self.visit(sub) for sub in node.subexprs])

    def visit_DomainSpec(self, node: dast.DomainSpec):
        return BinaryOp(dast.InOp, self.visit(node.pattern), self.visit(node.domain))

    def visit_QuantifiedExpr(self, node: dast.QuantifiedExpr):
        domain = self.visit_one_value(node.domains)
        predicate = self.visit_one_value(node.predicate)
        if node.operator == dast.UniversalOp:
            return Quantifier(node.operator, domain, predicate)
        elif node.operator == dast.ExistentialOp:
            return Quantifier(node.operator, domain, predicate)
        else:
            raise NotImplementedError("Unknown Quantifier Type {0}".format(node.operator))

    def visit_ReceivedExpr(self, node : dast.ReceivedExpr):
        return Received()

    def visit_SentExpr(self, node):
        return Sent()

    def handle_work(self, node, args, vargs, args2, kwargs, kwarg):
        return

    def visit_AwaitStmt(self, node : dast.AwaitStmt):
        await_cond_block = self.new_block(self.new_label("await"))
        await_block = self.new_block(self.new_label("await_loop"))
        await_body_block = None
        if len(node.branches[0].body):
            await_body_block = self.new_block(self.new_label("await_body"))
        end_block = self.new_block(self.new_label("await_end"))
        with BlockSetter(self, await_cond_block):
            self.append_inst(Label(node.label))
            # FIXME

            value = self.visit(node.branches[0].condition)
            next_block = await_body_block if len(node.branches[0].body) > 0 else end_block
            self.append_inst(CondBranch(value, next_block, await_block))

        with BlockSetter(self, await_block):
            self.append_inst(Branch(await_cond_block))
        if await_body_block:
            with BlockSetter(self, await_body_block):
                self.visit_one_value(node.branches[0].body)
                self.append_inst(Branch(end_block))
        self.set_block(end_block)
        return

    def visit_ApiCallExpr(self, node : dast.ApiCallExpr):
        assert(False)
        return

    def visit_BuiltinCallExpr(self, node : dast.BuiltinCallExpr):
        func = getattr(self, "handle_{0}".format(node.func))
        args = [self.visit(arg) for arg in node.args]
        vargs = self.visit(node.starargs) if node.starargs is not None else None
        kwargs = self.visit(node.kwargs) if node.kwargs is not None else None

        kwarg = { name : self.visit(arg) for name, arg in node.keywords}
        result = func(node, args, vargs, kwargs, kwarg)
        if result is None:
            return Constant(None)
        else:
            return result

    def visit_CallExpr(self, node : dast.CallExpr):
        builtin_function = {"int", "len", "range", "iter", "next", "randint" # Python builtin
                            }
        args = [self.visit(arg) for arg in node.args]
        vargs = self.visit(node.starargs) if node.starargs is not None else None
        kwargs = self.visit(node.kwargs) if node.kwargs is not None else None

        kwarg = { name : self.visit(arg) for name, arg in enumerate(node.keywords)}
        if isinstance(node.func, dast.NamedVar) and \
           node.func.name in builtin_function:
            func = getattr(self, "handle_{0}".format(node.func.name))
            result = func(node, args, vargs, kwargs, kwarg)
            if result is None:
                return Constant(None)
            else:
                return result
        else:
            func = self.visit(node.func)
            tempvar = self.tempvar()

            self.append_inst(Assign(tempvar, "=", Call(func, args, vargs, kwargs)))
            return tempvar


    def visit_SimpleExpr(self, node : dast.SimpleExpr):
        return self.visit_one_value(node.value)

    def visit_TupleExpr(self, node : dast.TupleExpr):
        return Tuple([self.visit(sub) for sub in node.subexprs])

    def visit_NamedVar(self, node : dast.NamedVar):
        return Variable(node.name)

    def visit_ConstantExpr(self, node : dast.ConstantExpr):
        return Constant(node.value)

    def visit_SelfExpr(self, node : dast.SelfExpr):
        return ProcessId()

    def visit_TrueExpr(self, node : dast.TrueExpr):
        return Constant(True)

    def visit_FalseExpr(self, node : dast.FalseExpr):
        return Constant(False)

    def visit_NoneExpr(self, node : dast.NoneExpr):
        return Constant(None)

    def visit_SelfExpr(self, node : dast.SelfExpr):
        return ProcessId()

    def visit_AttributeExpr(self, node: dast.AttributeExpr):
        result = self.visit(node.value)
        return Property(result, node.attr)

    def visit_SubscriptExpr(self, node: dast.SubscriptExpr):
        result = self.visit(node.value)
        subscript = self.visit(node.index)
        return SubScript(result, subscript)

    def visit_SetExpr(self, node: dast.SetExpr):
        result = self.visit_one_value(node.subexprs)
        return Set(result)

    def visit_MaxExpr(self, node: dast.MaxExpr):
        return Max(self.visit_one_value(node.args))

    def visit_MinExpr(self, node: dast.MinExpr):
        return Max(self.visit_one_value(node.args[0]))

    def visit_SizeExpr(self, node: dast.SizeExpr):
        return Cardinality(self.visit_one_value(node.args[0]))

    def visit_SetCompExpr(self, node: dast.SetCompExpr):
        return SetComp(self.visit_one_value(node.elem), self.visit_one_value(node.conditions))

class Translator(object):
    def __init__(self):
        pass

    def run(self, name, ast):
        self.scopes = sp.ScopeBuilder.run(ast)
        for scope in self.scopes.values():
            utils.debug(scope)
        module = Module(name)

        functions = collections.OrderedDict()

        for node, scope in self.scopes.items():
            args = []
            if isinstance(node, dast.Function):
                for arg in node.args.args:
                    args.append(Variable(arg.name))
            function = Function(module, node, scope, args)
            functions[node] = function

        for node, function in functions.items():
            ScopeTranslator.run(node, function, functions)
            module.add_function(function)

        return module


