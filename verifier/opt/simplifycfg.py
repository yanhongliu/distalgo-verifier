from .passclasses import FunctionPass
from verifier.ir import *

class SimplifyCFGPass(FunctionPass):
    def optimize(self, block_idx, function):
        block = function.basicblocks[block_idx]
        # eliminate trivial dead code
        if len(block.pred) == 0 and block_idx != 0:
            function.remove_block_by_idx(block_idx)
            return True

        # if this is a empty block, remove it
        if len(block.ir) == 0:
            assert len(block.succ) <= 1
            block.replace_uses_with(function.basicblocks[block_idx+1])
            function.remove_block_by_idx(block_idx)
            return True

        # if it contains only branch, remove it and merge it
        if len(block.ir) == 1 and isinstance(block.ir[0], Branch):
            assert len(block.succ) == 1
            branch = block.ir[0]
            next_block = branch.get_op(0)
            # make sure we don't remove dead loop
            if block is not next_block:
                block.replace_uses_with(next_block)
                function.remove_block_by_idx(block_idx)
                return True

        # if last ir is branch, and it jumps to next block, remove branch
        if len(block.ir) > 0 and isinstance(block.ir[-1], Branch):
            assert len(block.succ) == 1
            branch = block.ir[-1]
            next_block = branch.get_op(0)
            if next_block is function.basicblocks[block_idx + 1]:
                block.ir.pop()
                return True

        # for block that next to other, merge them
        next_block = function.basicblocks[block_idx + 1]
        if len(block.succ) == 1 and next_block is next(iter(block.succ)) and \
           len(next_block.pred) == 1 and block_idx + 2 != len(function.basicblocks):
            next_block.ir = block.ir + next_block.ir
            block.ir = []
            block.replace_uses_with(next_block)
            next_block.update_inst_parent()
            function.remove_block_by_idx(block_idx)
            return True

        if len(block.ir) > 0 and isinstance(block.ir[-1], CondBranch):
            cond_branch = block.ir[-1]
            if isinstance(cond_branch.condition, Constant):
                if cond_branch.condition.value:
                    block.ir[-1] = Branch(cond_branch.target_block)
                    block.remove_succ(cond_branch.target_block_alt)
                else:
                    block.ir[-1] = Branch(cond_branch.target_block_alt)
                    block.remove_succ(cond_branch.target_block)
                return True

        return False

    def run_on_function(self, function : Function):
        i = 0
        assert len(function.basicblocks) > 0
        while i < len(function.basicblocks) - 1:
            if not self.optimize(i, function):
                i += 1
