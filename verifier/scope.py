from . import utils
from . import dast
import enum

@enum.unique
class NameType(enum.Enum):
    Local = 1
    Global = 2
    NonLocal = 3
    Free = 4

class Scope(object):
    def __init__(self, parent, ast, nonlocal_names : set, global_names : set):
        self.children = set()
        self.parent = parent
        self.ast = ast
        self.nonlocal_names = set() if nonlocal_names is None else nonlocal_names
        self.global_names = set() if global_names is None else global_names
        self.is_process = False
        self.names = dict()
        if self.parent is not None:
            self.parent.add_child(self)

    def add_child(self, scope):
        self.children.add(scope)

    def add_name(self, name, type = NameType.Free):
        self.names[name] = type

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
        self.nonlocal_names = set()
        self.global_names = set()

    def visit_NonLocalStmt(self, node : dast.NonLocalStmt):
        for name in node.names:
            self.nonlocal_names.add(name)

    def visit_GlobalStmt(self, node : dast.GlobalStmt):
        for name in node.names:
            self.global_names.add(name)

    # don't cross the bonduary of scope
    def visit_ClassDef(self, node):
        pass

    def visit_FuncDef(self, node):
        pass

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

class ScopeBuilder(utils.NodeVisitor):
    _result = "scopes"
    _nodebaseclass=dast.AstNode

    def __init__(self):
        super().__init__()
        self.scopes = utils.ObjectDictionary()
        self.current_scope = None
        self.top_scope = None

    # mostly, this is what we care about
    def is_simple_class_arglist(self, arglist : dast.ArgList):
        if arglist.vargs is not None or arglist.kwargs is not None or len(arglist.args2) != 0:
            return False

        for arg in arglist.args:
            # keyword arg
            if arg.name is not None or \
               not isinstance(arg.value, dast.Name):
                return False

        return True

    def is_process_class(self, arglist):
        if not self.is_simple_class_arglist(arglist):
            return False

        if len(arglist.args) == 1 and isinstance(arglist.args[0].value, dast.Name) and arglist.args[0].value.name == "process":
            return True

        return False


    def visit_scope(self, node):
        nonlocal_names, global_names = GlobalAndNonLocalFinder.run(node)
        if len(nonlocal_names) != 0 and self.current_scope is None:
            raise SyntaxError("nonlocal declaration not allowed at module level")

        with ScopeSetter(self, node, nonlocal_names, global_names) as scope:
            # set the top-level scope for global name
            if len(self.scopes) == 1:
                assert(self.top_scope is None)
                self.top_scope = self.current_scope
            self.generic_visit(node)

    def assign_to_name(self, name):
        self.current_scope.add_name(name, NameType.Local)

    def visit_Program(self, node : dast.Program):
        # create a scope for top-level
        self.visit_scope(node)

    def visit_ClassDef(self, node : dast.ClassDef):
        self.assign_to_name(node.name)
        self.visit_scope(node)

        if not self.is_simple_class_arglist(node.args):
            raise NotImplementedError("Currently only simple class is supported")
        elif self.is_process_class(node.args):
            self.current_scope.is_process = True

    def visit_FuncDef(self, node : dast.FuncDef):
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
        assert(node.targets_list is not None)
        if len(node.targets_list) == 0:
            pass
        for targets in node.targets_list:
            for target in targets:
                if isinstance(target, dast.Name):
                    self.assign_to_name(target.name)
