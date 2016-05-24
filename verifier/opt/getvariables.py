from .passclasses import *
from verifier.ir import *
from verifier.frontend import NameType
from verifier.utils import NodeVisitor

class GetVariables(NodeVisitor):
    def __init__(self, function, gvpass):
        self.function = function
        self.gvpass = gvpass

    def visit_IRName(self, node : IRName):
        if node.name_type == NameType.Pattern or node.name_type == NameType.HandlerPattern:
            return

        self.gvpass.names[self.function].add(node.name)

    def visit_Received(self, node):
        self.gvpass.need_rcvd = True
        self.generic_visit(node)

class GetVariablesPass(FunctionPass):
    def __init__(self):
        self.names = dict()
        self.need_rcvd = False
        self.need_sent = False

    def run_on_module(self, module):
        super().run_on_module(module)

    def run_on_function(self, function):
        self.names[function] = set()
        for inst in iter_instructions(function):
            GetVariables.run(inst, function, self)
