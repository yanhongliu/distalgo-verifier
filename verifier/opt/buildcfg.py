from .passclasses import FunctionPass
from ..ir import *
import collections

def is_branch(ir):
    return isinstance(ir, Branch) or isinstance(ir, CondBranch) or isinstance(ir, Return)

class BuildCFGPass(FunctionPass):

    def run_on_function(self, function : Function):
        blocks_todo = collections.deque(function.basicblocks)

        blocks = []

        while blocks_todo:
            block = blocks_todo.popleft()
            for idx, i in enumerate(block.ir):
                if is_branch(i):
                    if idx + 1 != len(block.ir):
                        new_block = block.split(idx)
                        blocks_todo.appendleft(new_block)
                        break
            blocks.append(block)

        endblock = BasicBlock(function, "end")
        blocks.append(endblock)
        for idx, block in enumerate(blocks[:-1]):
            if len(block.ir) > 0 and is_branch(block.ir[-1]):
                branch_ir = block.ir[-1]
                if isinstance(branch_ir, Return):
                    block.add_succ(endblock)
                elif isinstance(branch_ir, CondBranch):
                    block.add_succ(blocks[idx + 1])
                    block.add_succ(branch_ir.target_block)
                else:
                    block.add_succ(branch_ir.target_block)
            else:
                block.add_succ(blocks[idx + 1])

        function.basicblocks[:] = blocks[:]
