from .passclasses import FunctionPass
from verifier.ir import Function

class DumpFunction(FunctionPass):
    def run_on_function(self, function : Function):
        print("----------{0}---------".format(function.ast_node))
        for b in function.basicblocks:
            print("{0}:".format(b.label))
            for inst in b.ir:
                print(inst)
