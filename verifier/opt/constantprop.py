from .passclasses import BasicBlockPass
from ..ir import *
from .tagvariables import TagVariables
from verifier import utils

def is_constant(node):
    return isinstance(node, Constant) or isinstance(node, Function)

class ConstantProp(BasicBlockPass, utils.NodeVisitor):
    _nodebaseclass = Value

    def __init__(self):
        pass

    def run_on_function(self, function : Function):
        self.idom = function.immediate_dominators()
        super().run_on_function(function)

    def visit_UnaryOp(self, node : UnaryOp):
        if node.op == 'not' and isinstance(node.expr, Constant):
            node.replace_uses_with(Constant(not node.expr.value))


    def run_on_block(self, block : BasicBlock):
        tagvariables_pass = self.pass_manager.get_pass(TagVariables)

        for var, insts in tagvariables_pass.write_by.items():
            if len(insts) != 1:
                continue

            write_inst, _ = next(iter(insts))

            if not isinstance(write_inst, Assign) or not isinstance(write_inst.operands[0], IRName) or \
               not write_inst.operands[0].name == var:
                continue

            value = write_inst.operands[-1]
            if not is_constant(value):
                continue

            if var in tagvariables_pass.read_by:
                read_insts = tagvariables_pass.read_by[var]
                for read_inst, node in read_insts:
                    if write_inst.dominates(read_inst, self.idom):
                        node.replace_uses_with(value)

        for inst in block.ir:
            self.visit(inst)
