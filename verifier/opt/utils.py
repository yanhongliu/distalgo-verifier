from .. import utils

class CheckSpecialBranchInstruction(utils.NodeVisitor):
    def __init__(self):
        self.result = False

    def visit(self, node):
        if self.result:
            return
        else:
            super().visit(node)

    def visit_Call(self, node):
        self.result = True

    def visit_Label(self, node):
        self.result = True
