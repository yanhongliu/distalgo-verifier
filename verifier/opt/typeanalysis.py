from .passclasses import *
from verifier.ir import *
from verifier.utils import NodeVisitor
from verifier import types

class TypeAnalysis(ModulePass, NodeVisitor):
    _nodebaseclass = Value

    def __init__(self):
        self.types = dict()

    def run_on_module(self, module : Module):
        for function in module.functions:
            for inst in iter_instructions(function):
                self.visit(inst)

    def visit(self, node):
        if node not in self.types:
            self.generic_visit(node)
        else:
            return self.types[node]

    def visit_Constant(self, node : Constant):
        if isinstance(node.value, int):
            return types.Integer()
        elif isinstance(node.value, str):
            return types.String()
        elif isinstance(node.value, bool):
            return types.Boolean()
