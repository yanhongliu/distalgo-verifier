from .passclasses import FunctionPass, iter_instructions
from .utils import CheckSpecialBranchInstruction
from verifier.ir import *
from verifier.utils import *
from verifier.frontend import ScopeType, NameType


class InsertIfElse(FunctionPass):
    def __init__(self):
        pass

    def optimize(self, function : Function):
        for block in function.basicblocks:
            if len(block.succ) == 2 and all(len(succ.succ) == 1 for succ in block.succ):
                i = iter(block.succ)
                succ1 = block.ir[-1].target_block
                succ2 = block.ir[-1].target_block_alt
                if len(succ1.succ) == 1 and succ1.succ == succ2.succ and \
                   not any(any(CheckSpecialBranchInstruction.run(inst) for inst in succ.ir) for succ in [succ1, succ2]) and \
                   all((len(succ.ir) == 1 or \
                        (len(succ.ir) == 2 and isinstance(succ.ir[1], Branch)) and \
                       isinstance(succ.ir[0], Assign) and succ.ir[0].op == '=') for succ in [succ1, succ2]):

                    assign1 = succ1.ir[0]
                    assign2 = succ2.ir[0]
                    if isinstance(assign1.target, IRName) and isinstance(assign2.target, IRName) and \
                       assign1.target.name == assign2.target.name:
                        next_block = next(iter(succ2.succ))
                        if next_block is not block:
                            next_block.ir = block.ir[:-1] + [Assign(assign1.target, assign1.op, IfElse(block.ir[-1].condition, assign1.expr, assign2.expr))] + next_block.ir
                            function.remove_block(succ1)
                            function.remove_block(succ2)
                            block.replace_uses_with(next_block)
                            function.remove_block(block)
                            next_block.update_inst_parent()
                            return True


    def run_on_function(self, function : Function):
        while self.optimize(function):
            pass





