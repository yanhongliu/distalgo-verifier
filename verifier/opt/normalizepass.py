from .passclasses import FunctionPass, iter_instructions
from verifier.ir import *
from verifier.utils import *
from verifier.frontend import ScopeType, NameType

def is_self_property(v : Value):
    return isinstance(v, Property) and isinstance(v.operands[0], Variable) and \
           v.operands[0].name == "self"

class ReplaceSelfPropertyInSetup(NodeVisitor):
    _nodebaseclass = Value

    def __init__(self):
        pass

    def visit_Property(self, node : Property):
        if is_self_property(node):
            if node.name == "id":
                node.replace_uses_with(ProcessId())
            else:
                node.replace_uses_with(Variable(node.name))

class ReplaceVariableAndAllocateName(NodeVisitor):
    _nodebaseclass = Value

    def __init__(self, function, names):
        self.scope = function.scope
        self.names = names

    def gen_name(self, fullname, name, typ):
        if fullname not in self.names:
            self.names.add(fullname)
        return IRName(fullname, name, typ)

    def visit_Variable(self, node : Variable):
        if node.name[0] == '@':
            node.replace_uses_with(self.gen_name(self.scope.gen_name(node.name[1:]), node.name, NameType.Local))
            return
        result = self.scope.lookup_name(node.name)
        if result is not None:
            typ, scope = result
        else:
            # FIXME: missing name, probably in quantifier, but we need better check here
            # what if we have recursive quantifier?
            scope = self.scope
            typ = NameType.Pattern
        if typ == NameType.Global:
            # TODO
            pass
        elif typ == NameType.NonLocal:
            # TODO
            pass
        node.replace_uses_with(self.gen_name(scope.gen_name(node.name), node.name, typ))

class NormalizePass(FunctionPass):
    def __init__(self):
        self.names = set()

    def run_on_function(self, function : Function):
        if function.scope.type == ScopeType.ReceiveHandler:
            ReplaceVariableAndAllocateName.run(function.msg_pattern, function, self.names)
        for inst in iter_instructions(function):
            if function.scope.type == ScopeType.ProcessSetup or \
               (function.scope.parent is not None and function.scope.parent.type == ScopeType.Process):
                ReplaceSelfPropertyInSetup.run(inst)
            ReplaceVariableAndAllocateName.run(inst, function, self.names)

