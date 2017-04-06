from .passclasses import FunctionPass, iter_instructions
from verifier.ir import *
from verifier.utils import *
from verifier.frontend import ScopeType, NameType

class ReplaceBuiltinFunction(NodeVisitor):
    _nodebaseclass = Value

    def visit_Assign(self, node : Assign):
        self.generic_visit(node)
        if isinstance(node.expr, Call):
            call_node = node.expr
            if isinstance(call_node.func, Property) and call_node.func.name == "pop":
                node.parent.replace_inst(node, Assign(Tuple([node.target, call_node.func.operands[0]]), '=', PopOneElement(call_node.func.operands[0], call_node.operands[1])))
            elif isinstance(call_node.func, Property) and call_node.func.name == "append":
                container = call_node.func.operands[0]
                elem = call_node.operands[1]
                node.parent.replace_inst(node, Assign(container, '=', Append(container, elem)))

    def visit_Call(self, node : Call):
        if isinstance(node.func, Property) and node.func.name == "choice":
            # random
            node.replace_uses_with(RandomSelect(node.operands[1]))
        elif isinstance(node.func, IRName) and node.func.name == "next" and len(node.operands) > 1 and \
             isinstance(node.operands[1], Call) and node.operands[1].func.name == "iter":
            node.replace_uses_with(RandomSelect(node.operands[1].operands[1]))

class ReplaceBuiltinFunctionPass(FunctionPass):
    def run_on_function(self, function : Function):
        for inst in iter_instructions(function):
            ReplaceBuiltinFunction.run(inst)
