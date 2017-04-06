from .passmanager import PassManager
from .passclasses import FunctionPass, ModulePass, iter_instructions
from .buildcfg import BuildCFGPass
from .ssa import SSAPass
from .simplifycfg import SimplifyCFGPass
from .dumpfunction import DumpFunction
from .tagvariables import TagVariables, AssignTargetVisitor
from .constantprop import ConstantProp
from .normalizepass import NormalizePass
from .replacebuiltinfunction import ReplaceBuiltinFunctionPass
from .inliner import Inliner
from .getvariables import GetVariablesPass
from .insertifelse import InsertIfElse
from .utils import CheckSpecialBranchInstruction

__all__ = [
    "PassManager",
    "BuildCFGPass",
    "SSAPass",
    "SimplifyCFGPass",
    "FunctionPass",
    "DumpFunction",
    "ConstantProp",
    "TagVariables",
    "NormalizePass",
    "ReplaceBuiltinFunctionPass",
    "Inliner",
    "AssignTargetVisitor",
    "ModulePass",
    "GetVariablesPass",
    "InsertIfElse",
    "CheckSpecialBranchInstruction",
    "iter_instructions"
]
