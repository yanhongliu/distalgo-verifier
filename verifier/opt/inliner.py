from .passclasses import ModulePass, iter_instructions
from verifier.ir import *
from verifier.utils import *

class CallFinder(NodeVisitor):
    _nodebaseclass = Value

    def __init__(self):
        self.result = set()

    def visit_Call(self, node : Call):
        if isinstance(node.func, IRName):
            pass
        elif isinstance(node.func, Function):
            self.result.add(node.func)

class Inliner(ModulePass):
    def __init__(self):
        pass

    def run_on_module(self, module):
        callee = dict()
        caller = dict()
        for function in module.functions:
            callee[function] = set()

            for inst in iter_instructions(function):
                 callee[function] |= CallFinder.run(inst)

        for function, sites in callee.items():
            for function2 in sites:
                if function2 not in caller:
                    caller[function2] = set()
                caller[function2].add(function)

        for func in caller:
            pass



