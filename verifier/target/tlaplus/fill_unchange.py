from .tlaast import *
from verifier.utils import NodeVisitor

class Fill(NodeVisitor):
    _nodebaseclass = TlaAST

    def __init__(self, vars):
        self.stack = []
        self.level = 1
        self.changed = set()
        self.vars = vars

    def visit_TlaAndOrExpr(self, node):
        push = False
        if node.op == "/\\":
            if self.level > len(self.stack):
                push = True
                self.stack.append(False)
        self.generic_visit(node)

        if push:
            has_subifelse = self.stack.pop()
            if not has_subifelse:
                node.exprs.append(TlaUnchangedExpr(self.vars, set(self.changed)))

    def visit_TlaExceptExpr(self, node):
        return

    def visit_TlaInstantiationExpr(self, node):
        if node.name.name == 'Send':
            self.changed.add('msgQueue')
        self.generic_visit(node)

    def visit_TlaSymbol(self, node):
        if node.name[-1] == '\'':
            self.changed.add(node.name[:-1])

    def visit_TlaIfExpr(self, node):
        self.level += 1
        self.stack[-1] = True
        # make a copy
        changed = set(self.changed)
        self.visit_one_value(node.ifexpr)
        self.changed = set(changed)
        self.visit_one_value(node.elseexpr)
        self.changed = set(changed)
        self.level -= 1

