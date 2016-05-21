from .passclasses import ModulePass, iter_instructions
from verifier.ir import *
from verifier.utils import *
import enum

class FunctionTag(enum.Enum):
    ReadGlobal = 1
    WriteGlobal = 2
    Recursion = 3
    ReadNonlocal = 4
    WriteNonlocal = 5

class AssignTargetVisitor(NodeVisitor):
    _nodebaseclass = Value
    _result = ('read_set', 'write_set')

    def __init__(self, inst, read_by, write_by):
        self.read_set = set()
        self.write_set = set()
        self.read_by = read_by
        self.write_by = write_by
        self.read = True
        self.inst = inst

    def visit_Assign(self, node : Assign):
        self.read = False
        self.visit_one_value(node.target)
        self.read = True
        self.visit_one_value(node.expr)

    def visit_IRName(self, node : IRName):
        if isinstance(self.inst, CondBranch):
            assert(self.read)
        rw_set = self.read_set if self.read else self.write_set
        rw_by = self.read_by if self.read else self.write_by
        rw_set.add(node.name)
        if node.name not in rw_by:
            rw_by[node.name] = set()
        rw_by[node.name].add((self.inst, node))

    def visit_SubScript(self, node : SubScript):
        self.visit_one_value(node.value)

    def visit_Tuple(self, node : Tuple):
        self.visit_one_value(node.operands)

class TagVariables(ModulePass):
    def __init__(self):
        self.read_by = dict()
        self.write_by = dict()
        self.function_write = dict()
        self.function_read = dict()

    def run_on_module(self, module):
        for function in module.functions:
            self.function_read[function] = set()
            self.function_write[function] = set()
            for inst in iter_instructions(function):
                read_set, write_set = AssignTargetVisitor.run(inst, inst, self.read_by, self.write_by)
                self.function_read[function] |= read_set
                self.function_write[function] |= write_set

        write_vars = self.write_by.keys()
        read_vars = self.read_by.keys()
        write_only_vars = write_vars - read_vars
        self.write_only_vars = write_vars - read_vars

        for var in self.write_only_vars:
            for inst, name in self.write_by[var]:
                # write only one var
                if isinstance(inst, Assign) and inst.target is name and not isinstance(inst.expr, Function):
                    inst.parent.replace_inst(inst, inst.expr)

        # remove temp var that used in same block
        for wvar, winsts in self.write_by.items():
            if len(winsts) == 1 and wvar in self.read_by and len(self.read_by[wvar]) == 1:
                winst, target = next(iter(winsts))
                rinst, node = next(iter(self.read_by[wvar]))
                if rinst.parent is winst.parent and isinstance(winst, Assign) and \
                   winst.target is target and not isinstance(winst.expr, Function) and winst.dominates(rinst):
                    winst.parent.remove_inst(winst)
                    node.replace_uses_with(winst.expr)
