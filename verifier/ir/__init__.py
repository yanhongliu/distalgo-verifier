from .ir import *
from .module import Module

ir = [
    'Instruction',
    'Label',
    'Variable',
    'Send',
    'Start',
    'Setup',
    'New',
    'Config',
    'Tuple',
    'Clock',
    'Constant',
    'Property',
    'BinaryOp',
    'UnaryOp',
    'Assign',
    'Call',
    'CondBranch',
    'Branch',
    'PopOneElement',
    'Cardinality',
    'IsEmpty',
    'Return',
    'Integer',
    'Range',
    'SubScript',
]

__all__ = ir + ['BasicBlock', 'Module', 'Function']
