from .. import utils
from . import dast
import enum

def is_self(node):
    return isinstance(node, dast.Name) and node.name == "self"

# mostly, this is what we care about
def is_simple_class_arglist(arglist : dast.ArgList):
    if arglist.vargs is not None or arglist.kwargs is not None or len(arglist.args2) != 0:
        return False

    for arg in arglist.args:
        # keyword arg
        if arg.name is not None or \
            not isinstance(arg.value, dast.Name):
            return False

    return True

def is_process_class(arglist):
    if not is_simple_class_arglist(arglist):
        return False

    if len(arglist.args) == 1 and isinstance(arglist.args[0].value, dast.Name) and arglist.args[0].value.name == "process":
        return True

    return False

class SemanticsError(Exception):
    def __init__(self, s):
        self.string = s

    def __str__(self):
        return self.string

@enum.unique
class NameType(enum.Enum):
    Local = 1
    Global = 2
    NonLocal = 3

@enum.unique
class ScopeType(enum.Enum):
    General = 1
    Process = 2
    ProcessSetup = 3
    ReceiveHandler = 4

class Scope(object):
    def __init__(self, parent, ast, nonlocal_names : set, global_names : set):
        self.children = set()
        self.parent = parent
        self.ast = ast
        self.type = ScopeType.General
        self.names = dict()
        if self.parent is not None:
            self.parent.add_child(self)
        if isinstance(ast, dast.ClassDef):
            if is_process_class(ast.args):
                self.type = ScopeType.Process
        elif isinstance(ast, dast.FuncDef):
            if parent.type == ScopeType.Process:
                if ast.name == "setup":
                    self.type = ScopeType.ProcessSetup
                elif ast.name == "receive":
                    self.type = ScopeType.ReceiveHandler

        for name in nonlocal_names:
            self.add_name(name, NameType.NonLocal)
        for name in global_names:
            self.add_name(name, NameType.Global)

    def add_child(self, scope):
        self.children.add(scope)

    def add_name(self, name, typ = NameType.Local):
        if name in self.names:
            if (self.names[name] == NameType.Global or self.names[name] == NameType.NonLocal) and \
               (typ == NameType.Global or typ == NameType.NonLocal) and \
               self.names[name] != typ:
                raise SemanticsError("{0} is nonlocal and global".format(name))
        else:
            self.names[name] = typ

    def lookup_name(self, name):
        if name in self.names:
            return self.names[name], self
        if self.parent is not None:
            return self.parent.lookup_name(name)
        return None

    def __repr__(self):
        return "Scope(ast:{0} names:{1})".format(self.ast, self.names)

class Setter(object):
    def __init__(self, obj, field, value):
        self.obj = obj
        self.field = field
        self.value = value
        self.old_value = None
        self.entered = False

    def __enter__(self):
        self.old_value = getattr(self.obj, self.field)
        if self.entered:
            raise RuntimeError("Should not be used recursively")
        self.entered = True
        setattr(self.obj, self.field, self.value)
        return self.value

    def __exit__(self, type, value, traceback):
        self.entered = False
        assert(getattr(self.obj, self.field) == self.value)
        setattr(self.obj, self.field, self.old_value)

class ScopeSetter(Setter):
    def __init__(self, builder, node, nonlocal_names = None, global_names = None):
        self.scope = Scope(builder.current_scope, node, nonlocal_names, global_names)
        builder.scopes[node] = self.scope
        super().__init__(builder, "current_scope", self.scope)

class GlobalAndNonLocalFinder(utils.NodeVisitor):
    _result = ("nonlocal_names", "global_names")
    _nodebaseclass=dast.AstNode

    def __init__(self):
        super().__init__()
        self.node = None
        self.nonlocal_names = set()
        self.global_names = set()

    def visit_NonLocalStmt(self, node : dast.NonLocalStmt):
        for name in node.names:
            self.nonlocal_names.add(name)

    def visit_GlobalStmt(self, node : dast.GlobalStmt):
        for name in node.names:
            self.global_names.add(name)

    def visit_scope(self, node):
        if node is self.node or self.node is None:
            self.node = node
            self.generic_visit(node)

    # don't cross the bonduary of scope
    def visit_ClassDef(self, node):
        self.visit_scope(node)

    def visit_FuncDef(self, node):
        self.visit_scope(node)

builtin_names = {
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes', 'callable', 'chr',
    'classmethod', 'compile', 'complex', 'copyright', 'credits', 'delattr', 'dict', 'dir',
    'divmod', 'enumerate', 'eval', 'exec', 'exit', 'filter', 'float', 'format', 'frozenset',
    'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
    'issubclass', 'iter', 'len', 'license', 'list', 'locals', 'map', 'max', 'memoryview', 'min',
    'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property', 'quit', 'range', 'repr',
    'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum',
    'super', 'tuple', 'type', 'vars', 'zip',
    # distalgo specific
    'process',
}

class AssignNameFinder(utils.NodeVisitor):
    _result = "names"
    _nodebaseclass=dast.AstNode

    def __init__(self, builder):
        super().__init__()
        self.names = set()
        self.builder = builder

    def visit(self, node):
        if self.builder.current_scope.type == ScopeType.ProcessSetup and \
           isinstance(node, dast.PropertyExpr):
            if is_self(node.expr):
                self.builder.current_scope.parent.add_name(node.name)

        if isinstance(node, dast.TupleExpr) or isinstance(node, dast.Name):
            super().visit(node)

    def visit_Name(self, node : dast.Name):
        self.names.add(node.name)

class ScopeBuilder(utils.NodeVisitor):
    _result = "scopes"
    _nodebaseclass=dast.AstNode

    def __init__(self):
        super().__init__()
        self.scopes = utils.ObjectDictionary()
        self.current_scope = None
        self.top_scope = None

    def init_top_scope(self):
        self.top_scope = self.current_scope
        self.top_scope.add_name('int')
        self.top_scope.add_name('len')

    def visit_scope(self, node):
        nonlocal_names, global_names = GlobalAndNonLocalFinder.run(node)
        if len(nonlocal_names) != 0 and self.current_scope is None:
            raise SyntaxError("nonlocal declaration not allowed at module level")

        with ScopeSetter(self, node, nonlocal_names, global_names) as scope:
            # set the top-level scope for global name
            if len(self.scopes) == 1:
                assert(self.top_scope is None)
                self.init_top_scope()
            self.generic_visit(node)

    def assign_to_name(self, name):
        self.current_scope.add_name(name, NameType.Local)

    def visit_Program(self, node : dast.Program):
        # create a scope for top-level
        self.visit_scope(node)

    def visit_ClassDef(self, node : dast.ClassDef):
        if not is_simple_class_arglist(node.args):
            raise NotImplementedError("Currently only simple class is supported")
        self.assign_to_name(node.name)
        self.visit_scope(node)

    def visit_FuncDef(self, node : dast.FuncDef):
        if self.current_scope.type != ScopeType.Process or \
           node.name not in {"setup", "receive"}:
            self.assign_to_name(node.name)
        self.visit_scope(node)

    def visit_YieldFrom(self, node : dast.YieldFrom):
        if isinstance(self.current_scope.ast, dast.FuncDef):
            self.current_scope.is_generator = True
        else:
            assert("Yield can be only used in function")

    def visit_YieldExpr(self, node : dast.YieldExpr):
        if isinstance(self.current_scope.ast, dast.FuncDef):
            self.current_scope.is_generator = True
        else:
            assert("Yield can be only used in function")


    def visit_ExprStmt(self, node : dast.ExprStmt):
        assert(node.target_list is not None)
        if len(node.target_list) == 0:
            pass
        for target in node.target_list:
            names = AssignNameFinder.run(target, self)
            for name in names:
                self.assign_to_name(target.name)

    def visit_ImportStmt(self, node : dast.ImportStmt):
        for import_item in node.imported_as:
            if import_item.asname is not None:
                self.assign_to_name(import_item.asname)
            else:
                for module in import_item.name:
                    self.assign_to_name(module)
