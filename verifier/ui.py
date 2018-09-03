import argparse
import os
import sys

from .utils import NodeDump, DefaultLogger
from .frontend import Translator
from .opt import *
from .target.tlaplus import CodeGen

from da.compiler import daast_from_str

class DASTNodeDump(NodeDump):
    def visit_Process(self, node):
        self.dump_visit(node, ["body", "events"], None)
    def visit_Program(self, node):
        self.dump_visit(node, ["body"], None)

def dpyfile_to_tla(infile, outfile=None):
    filename = os.path.basename(infile)
    purename, _, suffix = filename.rpartition(".")
    if len(purename) == 0:
        purename = suffix
        suffix = ""

    with open(infile, "r") as f:
        source = f.read()
        daast = daast_from_str(source, purename)
        DefaultLogger.is_debug = True
        #parser = Parser()
        #ast = parser.parse(source, infile)
        #print(ast)
        # DASTNodeDump.run(daast)
        translator = Translator()
        modules = [translator.run(purename, daast)]
        pass_manager = PassManager()
        # add pass
        pass_manager.add_pass(BuildCFGPass())
        #pass_manager.add_pass(DumpFunction())
        pass_manager.add_pass(NormalizePass())
        # pass_manager.add_pass(DumpFunction())
        pass_manager.add_pass(TagVariables())
        pass_manager.add_pass(ConstantProp())
        pass_manager.add_pass(ReplaceBuiltinFunctionPass())
        pass_manager.add_pass(InsertIfElse())
        pass_manager.add_pass(TagVariables())
        pass_manager.add_pass(ConstantProp())
        pass_manager.add_pass(SSAPass())
        #pass_manager.add_pass(DumpFunction())
        pass_manager.add_pass(SimplifyCFGPass())
        #pass_manager.add_pass(DumpFunction())
        pass_manager.add_pass(Inliner())
        pass_manager.add_pass(SimplifyCFGPass())
        pass_manager.add_pass(TagVariables())
        #pass_manager.add_pass(DumpFunction())
        pass_manager.add_pass(GetVariablesPass())
        pass_manager.add_pass(DumpFunction())
        pass_manager.run(modules)

        codegen = CodeGen(pass_manager)
        codegen.run(modules, outfile)

def main():
    """Main entry point when invoking compiler module from command line."""
    ap = argparse.ArgumentParser(description="DistAlgo to tla.")
    ap.add_argument('-o', help="Output file name.", dest="outfile")
    ap.add_argument('infile', help="DistPy input source file.")
    args = ap.parse_args()
    dpyfile_to_tla(args.infile, args.outfile)
