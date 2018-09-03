from .passclasses import ModulePass, iter_instructions
from verifier.ir import *
from verifier.utils import *
from .utils import CheckSpecialBranchInstruction

class CallFinder(NodeVisitor):
    _nodebaseclass = Value

    def __init__(self):
        self.result = set()

    def visit_Call(self, node : Call):
        if isinstance(node.func, IRName):
            pass
        elif isinstance(node.func, Function):
            self.result.add(node)

class ArgumentReplace(NodeVisitor):
    _nodebaseclass = Value

    def __init__(self, replaces):
        self.result = set()
        self.replaces = replaces

    def visit_IRName(self, node : IRName):
        if node.name in self.replaces:
            node.replace_uses_with(self.replaces[node.name])

class Inliner(ModulePass):
    def __init__(self):
        pass

    def inlinable(self, function : Function):
        # Let's handle the simplest case for now
        if len(function.basicblocks) != 2:
            return False
        block = function.basicblocks[0]
        end = function.basicblocks[1]
        if block.succ != {end}:
            return False
        if any(CheckSpecialBranchInstruction.run(inst) for inst in block.ir):
            return False
        # TODO
        if isinstance(block.ir[0], Return):
            return True

        return False

    def run_on_module(self, module):
        caller = dict()
        for function in module.functions:

            for inst in iter_instructions(function):
                nodes = CallFinder.run(inst)
                for node in nodes:
                    if node.func not in caller:
                        caller[node.func] = []
                    caller[node.func].append((node, inst))

        for function in module.functions:
            if function in caller and self.inlinable(function):
                ret = function.basicblocks[0].ir[0]
                for call, inst in caller[function]:
                    clone = ret.expr.clone()
                    ast = function.scope.ast
                    block = inst.parent
                    caller_function = block.function

                    names = [(function.scope.gen_name(arg.name), self.pass_manager.tempvar(caller_function.scope)) for arg in ast.args.args]
                    for arg, (_, var) in zip(call.args, names):
                        block.insert_inst(Assign(var, "=", arg), inst)

                    ArgumentReplace.run(clone, dict(names))

                    call.replace_uses_with(clone)



