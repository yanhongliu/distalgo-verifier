from .passclasses import FunctionPass
from verifier.ir import Function
from .. import utils

class DumpFunction(FunctionPass):
    def run_on_module(self, module):
        super().run_on_module(module)
        utils.debug("===================================")

    def run_on_function(self, function : Function):
        utils.debug("----------{0}---------".format(function.ast_node))
        for b in function.basicblocks:
            utils.debug("{0}:".format(b.label))
            for inst in b.ir:
                utils.debug(inst)
