from .passclasses import BasicBlockPass
from ..ir import *

class DCE(BasicBlockPass):
    def run_on_block(self, block : BasicBlock):
        for ir in block.ir:
            if isinstance(ir, Assign):
                pass
