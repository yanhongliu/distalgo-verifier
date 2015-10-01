from .passclasses import FunctionPass
from verifier.ir import Function

class SimplifyCFGPass(FunctionPass):
    def optimize(self, block_idx, function):
        block = function.basicblocks[block_idx]
        # eliminate trivial dead code
        if len(block.pred) == 0 and block_idx != 0:
            function.remove_block(block_idx)
            return True

        if len(block.ir) == 0:
            assert len(block.succ) <= 1
            block.replace_uses_with(function.basicblocks[block_idx+1])
            function.remove_block(block_idx)
            return True
        return False

    def run_on_function(self, function : Function):
        i = 0
        assert len(function.basicblocks) > 0
        while i < len(function.basicblocks) - 1:
            if not self.optimize(i, function):
                i += 1
