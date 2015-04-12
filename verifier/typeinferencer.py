from . import utils
from . import dast

class TypeInferencer(utils.NodeVisitor):
    _nodebaseclass=dast.AstNode
    def __init__(self):
        pass

    
