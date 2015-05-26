#!/usr/bin/env python3

import itertools
import collections
from . import dast
from . import utils
from .unify import Unifier
from .scope import TlaVar

def subtype_checker(u, v):
    return (u.name == v.name) \
            or (type(u.origin) is not type(v.origin) and (isinstance(u.origin, type(v.origin)) or isinstance(v.origin, type(u.origin))))

class Field(types.Type):
    _fields = ["field_name"]

    def __init__(self, field_name):
        self.field_name = field_name

class IndexedField(types.Type):
    _fields = ["field_name", "index"]

    def __init__(self, field_name, index):
        self.field_name = field_name
        self.index = index

class IfNoneThenVoid(types.Type):
    _fields = ["value"]

    def __init__(self, value):
        self.value = value

class FunctionExtract(types.Type):
    _fields = ["value"]

    def __init__(self, value):
        self.value = value

class MessageType(types.Type): pass
class PatternType(types.Type): pass
class FilteredPatternType(types.Type): pass
class FunctionArgsType(types.Type): pass
class FunctionType(types.Type): pass
class FunctionReturnVar(types.Type): pass
class FunctionArgsVar(types.Type): pass

class ProcessInitializer(types.Type):
    _fields = ["process"]
    def __init__(self, process):
        self.process = process

class ListField(types.Type):
    _fields = ["field_name"]

    def __init__(self, field_name, extract_all=False):
        self.field_name = field_name
        self.extract_all = extract_all

    def copy(self):
        f = super().copy()
        f.extract_all = self.extract_all
        return f

class ListConstrain:
    def __init__(self, field_name):
        self.field_name = field_name

class FunctionHasNoReturn:
    def check(self, node, type_inferencer):
        return not type_inferencer.scopes[node].has_return

def constant_resolver(node):
    if isinstance(node.value, str):
        return types.String(node.value)
    elif isinstance(node.value, bool):
        return types.Boolean()
    elif isinstance(node.value, int):
        return types.Integer()
    return None

# the purpose of rule is to find out the type of each variable, instead of all expression
# so with such rule, the constrain we need to construct
# and the rule should always be the form of [a] = f([b]), instead of f([a]) = g([b])
# otherwise it can be decomposed in the first place
# the visitor will return the type of visited expression
#
# so we define rule as a tuple
TypingRule = {
    # target = value
    # constrain: [target] = [value]
    dast.AssignmentStmt: [(IndexedField("targets", 0), Field("value"))],
    # for target in iter
    # constrain: iter = set[target] | iter = target[iter]
    dast.ForStmt: [(Field("iter"), types.Iterable(Field("target")))],
    # send(message, target)
    # target need to be a set or process
    # message type need to be consistant
    dast.SendStmt: [(Field("message"), MessageType())],
    # await(expr)
    dast.Branch: [(Field("condition"), types.Boolean())],
    # value[index]
    # contrains:
    dast.SubscriptExpr: [(types.List(TlaVar("$self")), Field("value")), (Field("index"), types.Integer())],
    # [a, b, c, d]
    dast.ListExpr: [(TlaVar("$self"), types.List(ListField("subexprs"))), ListConstrain("subexprs")],
    # {a, b, c, d}
    dast.SetExpr: [(TlaVar("$self"), types.Set(ListField("subexprs"))), ListConstrain("subexprs")],
    # (a, b, c, d)
    dast.TupleExpr: [(TlaVar("$self"), types.Tuple(ListField("subexprs", extract_all=True)))],
    # [false] = Bool
    dast.TrueExpr: [(TlaVar("$self"), types.Boolean())],
    # [true] = Bool
    dast.FalseExpr: [(TlaVar("$self"), types.Boolean())],
    # left < right
    dast.ComparisonExpr:[
        (TlaVar("$self"), types.Boolean()),
        ([("comparator", dast.EqOp)], Field("left"), Field("right"))
        ],
    # None
    # 
    dast.NoneExpr: [(TlaVar("$self"), TlaVar("$dummy"))],
    # len(value)
    # len(value) = [Integer]
    dast.SizeExpr: [(TlaVar("$self"), types.Integer()), (Field("value"), TlaVar("$dummy"))],
    dast.CallExpr: [
        ((types.Function(types.Tuple(ListField("args", extract_all=True)), TlaVar("$self"))), FunctionExtract(Field("func"))),
        ],
    dast.ApiCallExpr: [
        # createprocs(Process, num_of_process)
        ([("func", "createprocs")], TlaVar("$self"), types.Set(types.Process(IndexedField("args", 0)))),
        # setupprocs(set_of_process, arguments)
        ([("func", "setupprocs")], IndexedField("args", 0), types.Set(types.Process(TlaVar("$process_type")))),

        ([("func", "setupprocs")], ProcessInitializer(IndexedField("args", 0)), IndexedField("args", 1)),
        ],
    dast.BuiltinCallExpr: [
        ([("func", "logical_clock")], TlaVar("$self"), types.Integer())
        ],
    # something like x + y
    dast.ArithmeticExpr: [
        (TlaVar("$self"), Field("left")),
        (Field("left"), Field("right"))
        ],
    dast.AttributeExpr: [
        (TlaVar("$self"), TlaVar("$dummy")),
        ],
    dast.IfExpr: [
        (TlaVar("$self"), Field("body")),
        (Field("body"), Field("orbody")),
        (Field("condition"), types.Boolean()),
        ],
    dast.LogicalExpr: [
        (TlaVar("$self"), types.Boolean()),
        ],
    dast.QuantifiedExpr: [
        (TlaVar("$self"), types.Boolean()),
        ],
    # each/some pattern in D
    # D = iterable(pattern)
    dast.PatternDomainSpec: [
        (types.Iterable(PatternType()), IndexedField("subexprs", 1)),
        ],
    # each/some send/receiv
    # this rule is designed to match the message type and free/bound variable type
    dast.HistoryDomainSpec: [
        (PatternType(), MessageType()),
        ],
    dast.EventHandler: [
        (PatternType(), MessageType()),
        ],
    # rcvd(Type(a, b)) = set(bool) / set(tuple(free variable))
    # pattern = messagetype
    dast.ReceivedExpr: [
        (TlaVar("$self"), FilteredPatternType()),
        (PatternType(), MessageType())
        ],
    dast.SentExpr: [
        (TlaVar("$self"), FilteredPatternType()),
        (PatternType(), MessageType())
        ],
    dast.ReturnStmt: [
        (types.Function(FunctionArgsType(), IfNoneThenVoid(Field("value"))), FunctionType())
        ],
    dast.Function: [
        ([FunctionHasNoReturn()], FunctionReturnVar(), types.Void()),
        (FunctionArgsType(), FunctionArgsVar()),
        (types.Function(FunctionArgsVar(), FunctionReturnVar()), FunctionType())
        ],
    dast.SetCompExpr: [
        (TlaVar("$self"), types.Set(Field("elem"))),
        (IndexedField("iters", 0), types.Iterable(IndexedField("targets", 0))),
        ]
}

class CheckType(utils.NodeVisitor):
    _nodebaseclass=types.Type
    def __init__(self):
        self.result = True

    def visit(self, node):
        if isinstance(node, TlaVar):
            self.result = False
            return

        for field, value in utils.iter_fields(node):
            if isinstance(value, TlaVar):
                self.result = False
                return
            elif isinstance(value, list):
                for v in value:
                    if isinstance(v, TlaVar):
                        self.result = False
                        return

        super().visit(node)

class FieldDependencyCollector(utils.NodeVisitor):
    _nodebaseclass=(types.Type, TlaVar)
    def __init__(self):
        self.result = set()

    def visit_Field(self, node : Field):
        if node.field_name not in self.result:
            self.result.add(node.field_name)

    def visit_IndexedField(self, node : IndexedField):
        if node.field_name not in self.result:
            self.result.add(node.field_name)

    def visit_ListField(self, node : ListField):
        if node.field_name not in self.result:
            self.result.add(node.field_name)

class PatternToType(utils.NodeTransformer):
    _nodebaseclass=dast.PatternElement

    def __init__(self, type_inferencer):
        self.type_inferencer = type_inferencer

    def visit_FreePattern(self, node : dast.FreePattern):
        if node.value:
            assert(isinstance(node.value, dast.NamedVar))
            return self.type_inferencer.current_scope.lookup_var(node.value.name)
        else:
            return TlaVar(self.type_inferencer.temp_variable_name("$dummy"))

    def visit_ConstantPattern(self, node : dast.ConstantPattern):
        assert(isinstance(node.value, dast.ConstantExpr))
        return constant_resolver(node.value)

    def visit_BoundPattern(self, node : dast.BoundPattern):
        assert(isinstance(node.value, dast.NamedVar))
        return self.type_inferencer.current_scope.lookup_var(node.value.name)

    def visit_TuplePattern(self, node : dast.TuplePattern):
        return types.Tuple([self.visit(pat) for pat in node.value])

    def visit_ListPattern(self, node : dast.ListPattern):
        raise NotImplementedError()

class ConstrainPreparer(utils.NodeTransformer):
    _nodebaseclass=(types.Type, TlaVar)
    def __init__(self, type_inferencer, node, fields_value):
        self.type_inferencer = type_inferencer
        self.node = node
        self.fields_value = fields_value

    def visit_Field(self, node : Field):
        if not isinstance(self.node, dast.ReturnStmt):
            assert(node.field_name in self.fields_value)
            assert(self.fields_value[node.field_name] is not None)

        return self.fields_value[node.field_name] if node.field_name in self.fields_value else None

    def visit_IndexedField(self, node : IndexedField):
        assert(node.field_name in self.fields_value)
        assert(self.fields_value[node.field_name][node.index] is not None)
        return self.fields_value[node.field_name][node.index]

    def visit_ListField(self, node : ListField):
        if node.extract_all:
            return self.fields_value[node.field_name]
        if len(self.fields_value[node.field_name]) == 0:
            return TlaVar("$list_dummy")
        else:
            return self.fields_value[node.field_name][0]

    def visit_TlaVar(self, node: TlaVar):
        if node.name[0] == '$' and node.name != '$self':
            return TlaVar(self.type_inferencer.temp_variable_name(node.name))
        return node

    def visit_ProcessInitializer(self, node : ProcessInitializer):
        # the process type should be resolved before
        process = self.visit(node.process)
        assert(isinstance(process, types.Set))
        assert(isinstance(process.subtype, types.Process))
        proc_ast = process.subtype.process_class.process
        scope = self.type_inferencer.scopes[proc_ast]
        vars = [scope.lookup_var(arg.name) for arg in proc_ast.args.args]
        return types.Tuple(vars)

    def visit_MessageType(self, node : MessageType):
        if isinstance(self.node, dast.SendStmt):
            assert(isinstance(self.node.message, dast.TupleExpr))
            assert(isinstance(self.node.message.subexprs[0], dast.ConstantExpr))
            messageType = self.node.message.subexprs[0].value
        elif isinstance(self.node, dast.HistoryDomainSpec) or isinstance(self.node, dast.HistoryExpr):
            assert(isinstance(self.node.event, dast.Event))
            assert(isinstance(self.node.event.pattern, dast.PatternExpr))
            assert(isinstance(self.node.event.pattern.pattern, dast.TuplePattern))
            assert(isinstance(self.node.event.pattern.pattern.value[0], dast.ConstantPattern))
            assert(isinstance(self.node.event.pattern.pattern.value[0].value, dast.ConstantExpr))
            messageType = self.node.event.pattern.pattern.value[0].value.value
        elif isinstance(self.node, dast.EventHandler):
            assert(isinstance(self.node.events[0], dast.Event))
            assert(isinstance(self.node.events[0].pattern, dast.PatternExpr))
            assert(isinstance(self.node.events[0].pattern.pattern, dast.TuplePattern))
            assert(isinstance(self.node.events[0].pattern.pattern.value[0], dast.ConstantPattern))
            assert(isinstance(self.node.events[0].pattern.pattern.value[0].value, dast.ConstantExpr))
            messageType = self.node.events[0].pattern.pattern.value[0].value.value
        else:
            assert(False)
        var = self.type_inferencer.program_scope.lookup_or_add_var("_message_{0}".format(messageType))
        if var.tlatype is not None:
            return var.tlatype.copy()
        else:
            return var.copy()

    def visit_PatternType(self, node : PatternType):
        if isinstance(self.node, dast.HistoryDomainSpec) or isinstance(self.node, dast.HistoryExpr):
            assert(isinstance(self.node.event, dast.Event))
            assert(isinstance(self.node.event.pattern, dast.PatternExpr))
            pattern = self.node.event.pattern.pattern
        elif isinstance(self.node, dast.PatternDomainSpec):
            assert(isinstance(self.node.pattern, dast.PatternExpr))
            pattern = self.node.pattern.pattern
        elif isinstance(self.node, dast.EventHandler):
            assert(isinstance(self.node.events[0], dast.Event))
            assert(isinstance(self.node.events[0].pattern, dast.PatternExpr))
            pattern = self.node.events[0].pattern.pattern
        else:
            assert(False)
        patternType = PatternToType.run(pattern, self.type_inferencer)
        return patternType

    def visit_FilteredPatternType(self, node : FilteredPatternType):
        assert(isinstance(self.node, dast.HistoryExpr))
        assert(isinstance(self.node.event, dast.Event))
        if len(self.node.event.pattern.ordered_freevars) == 0:
            # see dpy/pattern.py filter
            return types.Boolean()
        else:
            # TODO
            print(self.node.event.pattern.ordered_freevars)
            vars = []
            for arg in self.node.event.pattern.ordered_freevars:
                var = self.type_inferencer.current_scope.lookup_var(arg.name)
                if var.tlatype is not None:
                    var = var.tlatype.copy()
                else:
                    var = var.copy()
                vars.append(var)
            return types.Set(types.Tuple(vars))

    def visit_IfNoneThenVoid(self, node: IfNoneThenVoid):
        type = self.visit(node.value)
        return type if type is not None else types.Void()

    def visit_FunctionType(self, node: FunctionType):
        assert(isinstance(self.type_inferencer.current_scope.ref, dast.Function))
        var = self.type_inferencer.current_scope.lookup_var_by_ref(self.type_inferencer.current_scope.ref)
        if var.tlatype is not None:
            return var.tlatype.copy()
        else:
            return var.copy()

    def visit_FunctionArgsType(self, node: FunctionArgsType):
        assert(isinstance(self.type_inferencer.current_scope.ref, dast.Function))
        vars = []
        for arg in self.type_inferencer.current_scope.ref.args.args:
            var = self.type_inferencer.current_scope.lookup_var(arg.name)
            if var.tlatype is not None:
                var = var.tlatype.copy()
            else:
                var = var.copy()
            vars.append(var)
        return types.Tuple(vars)

    def function_aux_var(self, var, name):
        var = var.scope.lookup_or_add_var_local("__{0}_{1}".format(var.name, name))
        if var.tlatype is not None:
            return var.tlatype.copy()
        else:
            return var.copy()
        return var

    def visit_FunctionReturnVar(self, node: FunctionReturnVar):
        assert(isinstance(self.type_inferencer.current_scope.ref, dast.Function))
        var = self.type_inferencer.current_scope.lookup_var_by_ref(self.type_inferencer.current_scope.ref)
        return self.function_aux_var(var, "return")

    def visit_FunctionArgsVar(self, node: FunctionArgsVar):
        assert(isinstance(self.type_inferencer.current_scope.ref, dast.Function))
        var = self.type_inferencer.current_scope.lookup_var_by_ref(self.type_inferencer.current_scope.ref)
        return self.function_aux_var(var, "args")

    def visit_FunctionExtract(self, node: FunctionExtract):
        func = self.visit(node.value)
        if isinstance(func, TlaVar):
            var = self.type_inferencer.current_scope.lookup_var(func.name)
            if isinstance(var.ref, dast.Function):
                return types.Function(self.function_aux_var(var, "args"), self.function_aux_var(var, "return"))

        return func.copy()

class TypeInferencer(utils.NodeVisitor, utils.Logger):
    _nodebaseclass=dast.AstNode
    _result="progress"

    def __init__(self, scopes, node_to_type):
        super().__init__()
        self.scopes = scopes
        self.program_scope = None
        self.current_scope = None
        self.temp_variable = dict()
        self.skip_handlers = utils.Flag(True)
        self.node_to_type = node_to_type
        self.progress = False

    def temp_variable_name(self, name):
        num = self.temp_variable
        if name in self.temp_variable:
            self.temp_variable[name] += 1
        else:
            self.temp_variable[name] = 0
        num = self.temp_variable[name]
        return "{0}{1}".format(name, num)

    def check_condition(self, node, condition):
        if isinstance(condition, tuple):
            (field, value) = condition
            return getattr(node, field, None) == value
        else:
            return condition.check(node, self)

    def fields_dependency(self, node):
        rules = TypingRule[type(node)]
        fields = set()
        for rule in rules:
            if isinstance(rule, tuple):
                if len(rule) == 3:
                    (conditions, left, right) = rule
                    if not all(self.check_condition(node, condition) for condition in conditions):
                        continue
                else:
                    (left, right) = rule

                fields = fields | FieldDependencyCollector.run(left)
                fields = fields | FieldDependencyCollector.run(right)

        return fields

    def unify(self, node, left, right):
        self.debug("==========")
        self.debug("for")
        self.debug(node.__class__.__name__)
        if isinstance(node, dast.ComparisonExpr):
            self.debug(node.comparator)
        self.debug(left)
        self.debug(right)

        (result, mapping) = Unifier.run(left, right, subtype_checker)
        if not result:
            assert(False)

        self.debug("unify result:")
        self.debug(result)
        self.debug(mapping)

        node_type = None
        for (var, f) in mapping:
            if var.name == "$self":
                # $self is special case for type of expression itself
                node_type = f.origin.copy()
            if f.name == "$self":
                node_type = var.origin.copy()
            elif var.name[0] != '$':
                # if name not start with $, which means it's a real variable
                assert(isinstance(var.origin, TlaVar))
                variable = var.origin.scope.lookup_var(var.name)
                assert(variable is not None)
                if CheckType.run(f.origin) and variable.tlatype is None:
                    variable.tlatype = f.origin.copy()
                    self.progress = True

        return node_type


    def visit(self, node):
        if isinstance(node, dast.DistNode) and isinstance(node, collections.Hashable) and node in self.scopes:
            self.current_scope = self.scopes[node]

        if type(node) in TypingRule:
            # we are trying to duplicate some logic in NodeVisitor
            # since we want to extract some field
            if isinstance(node, dast.Branch):
                pass

            fields = self.fields_dependency(node)
            fields_value = dict()
            for field, value in utils.iter_fields(node, fields):
                fields_value[field] = self.visit_one_value(value)
                #if fields_value[field] is None:
                    #self.visit_one_value(value)
                #elif isinstance(fields_value[field], list):
                    #for i, item in enumerate(fields_value[field]):
                        #if item is None:
                            #self.visit_one_value(value[i])

            # we extract the rule
            node_type = None
            rules = TypingRule[type(node)]
            for rule in rules:
                if isinstance(rule, tuple):
                    if len(rule) == 3:
                        (conditions, left, right) = rule
                        if not all(self.check_condition(node, condition) for condition in conditions):
                            continue
                    else:
                        (left, right) = rule
                    left = left.copy()
                    right = right.copy()
                    left = ConstrainPreparer.run(left.copy(), self, node, fields_value)
                    right = ConstrainPreparer.run(right.copy(), self, node, fields_value)
                    new_node_type = self.unify(node, left, right)
                    if node_type is None:
                        node_type = new_node_type
                elif isinstance(rule, ListConstrain):
                    lst = fields_value[rule.field_name]
                    assert(isinstance(lst, list))
                    for (item1, item2) in itertools.combinations(lst, 2):
                        self.unify(node, item1, item2)

            self.visit_other_fields(node, fields)

            result = node_type
        else:
            # this will help us to handle some simple type like constant, writing a non-general rule
            # for them doesn't worth it
            result = super().visit(node)

        if result is not None \
            and node not in self.node_to_type and CheckType.run(result):
            self.node_to_type[node] = result
            self.progress = True
        return result

    def visit_Program(self, node : dast.Program):
        self.program_scope = self.scopes[node]
        self.visit_one_value(node.body)
        self.visit_one_value(node.processes)

    def visit_Process(self, node : dast.Process):
        self.visit_one_value(node.args)
        self.visit_one_value(node.initializers)
        with self.skip_handlers:
            self.visit_one_value(node.events)
        self.visit_some_fields(node, ['methods', 'entry_point', 'body'])

    # skip all pattern here
    def visit_PatternElement(self, node):
        pass

    def visit_NamedVar(self, node : dast.NamedVar):
        var = self.current_scope.lookup_var(node.name)
        assert(var is not None)
        if var.tlatype is not None:
            return var.tlatype
        else:
            return var

    def visit_ConstantExpr(self, node):
        return constant_resolver(node)

    def visit_SimpleExpr(self, node : dast.SimpleExpr):
        return self.visit(node.value)

    def visit_SelfExpr(self, node: dast.SelfExpr):
        process = self.current_process()
        assert(isinstance(process, dast.Process))
        return types.Process(types.ProcessClass(process))

    # comparing with scope.py, we skip handler in upper calling stack
    # because the customized visit will change the scope before visit them.
    def visit_Event(self, node : dast.Event):
        if self.skip_handlers:
            return
        self.visit_one_value(node.handlers)

    def current_process(self):
        scope = self.current_scope
        while scope is not None and not isinstance(scope.ref, dast.Process):
            scope = scope.parent

        return None if scope is None else scope.ref
