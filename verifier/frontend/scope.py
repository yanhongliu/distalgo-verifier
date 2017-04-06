from .. import utils
from da.compiler import dast
import enum

def is_self(node):
    return isinstance(node, dast.NamedVar) and node.name == "self"

# mostly, this is what we care about
def is_simple_class_arglist(arglist : dast.Arguments):
    if arglist.vargs is not None or arglist.kwargs is not None or len(arglist.args2) != 0:
        return False

    for arg in arglist.args:
        # keyword arg
        if arg.name is not None or \
            not isinstance(arg.value, dast.NamedVar):
            return False

    return True

def is_process_class(arglist):
    if not is_simple_class_arglist(arglist):
        return False

    if len(arglist.args) == 1 and isinstance(arglist.args[0].value, dast.NamedVar) and arglist.args[0].value.name == "process":
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
    Process = 4
    Pattern = 5
    HandlerPattern = 6

@enum.unique
class ScopeType(enum.Enum):
    General = 1
    Main = 2
    Process = 3
    ProcessSetup = 4
    ReceiveHandler = 5

class Scope(object):
    def __init__(self, parent, ast, nonlocal_names : set, global_names : set):
        self.children = set()
        self.parent = parent
        self.ast = ast
        self.type = ScopeType.General
        self.names = dict()
        if self.parent is not None:
            self.parent.add_child(self)
        if isinstance(ast, dast.ClassStmt):
            # TODO
            pass
        elif isinstance(ast, dast.Process):
            self.type = ScopeType.Process
        elif isinstance(ast, dast.EventHandler):
            self.type = ScopeType.ReceiveHandler
        elif isinstance(ast, dast.Function):
            if parent.type == ScopeType.Process:
                if ast.name == "setup":
                    self.type = ScopeType.ProcessSetup
            elif isinstance(parent.ast, dast.Program) and ast.name == "main":
                self.type = ScopeType.Main

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

    def gen_name(self, name):
        scope = self
        result = ''
        while not isinstance(scope.ast, dast.Program):
            result = scope.ast.name + '_' + result
            scope = scope.parent

        return result + name

    def __repr__(self):
        return "Scope(ast:{0}, parent:{2} names:{1})".format(self.ast, self.names, self.parent.ast if self.parent is not None else None)

    def get_process_scope(self):
        scope = self
        while scope is not None and scope.type != ScopeType.Process:
            scope = scope.parent
        return scope

    def is_parent_of(self, other):
        scope = other.parent
        while scope is not self and scope is not None:
            scope = scope.parent

        if scope is self:
            # FIXME closure
            return True
        else:
            return False

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
    _nodebaseclass=dast.DistNode

    def __init__(self):
        super().__init__()
        self.node = None
        self.nonlocal_names = set()
        self.global_names = set()

    def visit_NonLocalStmt(self, node : dast.NonlocalStmt):
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
    def visit_ClassStmt(self, node):
        self.visit_scope(node)

    def visit_Process(self, node):
        self.visit_scope(node)

    def visit_Function(self, node):
        self.visit_scope(node)

    def visit_EventHandler(self, node : dast.EventHandler):
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
    _nodebaseclass=dast.DistNode

    def __init__(self, scope):
        super().__init__()
        self.names = set()
        self.scope = scope

    def visit(self, node):
        if self.scope.type == ScopeType.ProcessSetup and \
           isinstance(node, dast.AttributeExpr):
            if is_self(node.expr):
                self.scope.parent.add_name(node.name, NameType.Process)

        if isinstance(node, dast.TupleExpr) or isinstance(node, dast.SimpleExpr) or isinstance(node, dast.NamedVar):
            super().visit(node)

    def visit_NamedVar(self, node : dast.NamedVar):
        self.names.add(node.name)

class ScopeNameResolver(utils.NodeVisitor):
    _nodebaseclass=dast.DistNode

    def __init__(self, scope):
        super().__init__()
        self.current_scope = scope

    def assign_to_name(self, name, name_type = NameType.Local):
        #utils.debug("Assign To: " + str(name) + " under " + str(self.current_scope) + " PARENT "  + str(self.current_scope.parent))
        result = self.current_scope.lookup_name(name)

        if result is not None:
            typ, scope = result
            if typ == NameType.Process:
                return
        if self.current_scope.type == ScopeType.ProcessSetup:
            self.current_scope.get_process_scope().add_name(name, NameType.Process)
        else:
            self.current_scope.add_name(name, name_type)

    def visit_scope(self, node):
        if node is self.current_scope.ast:
            if isinstance(node, dast.Program):
                self.visit_one_value(node.body)
            elif isinstance(node, dast.ClassStmt):
                self.visit_one_value(node.body)
            elif isinstance(node, dast.Process):
                self.visit_one_value(node.args)
                self.visit_one_value(node.body)
                self.visit_one_value(node.events)
            elif isinstance(node, dast.Function):
                self.visit_one_value(node.args)
                self.visit_one_value(node.body)
        elif not isinstance(node, dast.Program):
            self.assign_to_name(node.name)

    def visit_Program(self, node : dast.Program):
        self.visit_scope(node)

    def visit_ClassStmt(self, node : dast.ClassStmt):
        self.visit_scope(node)

    def visit_Process(self, node: dast.Process):
        self.visit_scope(node)

    def visit_Function(self, node : dast.Function):
        self.visit_scope(node)

    def visit_EventHandler(self, node : dast.EventHandler):
        self.visit_scope(node)

    def visit_Arguments(self, node : dast.Arguments):
        if self.current_scope.type == ScopeType.ReceiveHandler:
            for arg in node.args:
                if arg.name == 'msg' or arg.name == 'from_':
                    names = AssignNameFinder.run(arg.value, self.current_scope)
                    for name in names:
                        self.assign_to_name(name, NameType.HandlerPattern)
        else:
            if self.current_scope.type == ScopeType.Process:
                name_type = NameType.Process
            else:
                name_type = NameType.Local

            for arg in node.args:
                self.current_scope.add_name(arg.name, name_type)

    def visit_YieldFromStmt(self, node : dast.YieldFromStmt):
        if isinstance(self.current_scope.ast, dast.Function):
            self.current_scope.is_generator = True
        else:
            assert("Yield can be only used in function")

    def visit_YieldStmt(self, node : dast.YieldStmt):
        if isinstance(self.current_scope.ast, dast.Function):
            self.current_scope.is_generator = True
        else:
            assert("Yield can be only used in function")

    def visit_AssignmentStmt(self, node : dast.AssignmentStmt):
        assert(node.targets is not None)
        if len(node.targets) == 0:
            pass
        for target in node.targets:
            names = AssignNameFinder.run(target, self.current_scope)
            for name in names:
                self.assign_to_name(name)

    def visit_ForStmt(self, node : dast.ForStmt):
        names = AssignNameFinder.run(node.domain.pattern, self.current_scope)
        for name in names:
            self.assign_to_name(name)

        self.generic_visit(node)

    def visit_ImportFromStmt(self, node : dast.ImportFromStmt):
        for import_item in node.items:
            if import_item.asname is not None:
                self.assign_to_name(import_item.asname)
            else:
                self.assign_to_name(import_item.name)

    def visit_ImportStmt(self, node : dast.ImportStmt):
        for import_item in node.items:
            if import_item.asname is not None:
                self.assign_to_name(import_item.asname)
            else:
                self.assign_to_name(import_item.name)


class ScopeBuilder(utils.NodeVisitor):
    _result = "scopes"
    _nodebaseclass=dast.DistNode

    def __init__(self):
        super().__init__()
        self.scopes = utils.ObjectDictionary()
        self.current_scope = None
        self.top_scope = None

    def init_top_scope(self):
        self.top_scope = self.current_scope
        self.top_scope.add_name('int')
        self.top_scope.add_name('len')
        self.top_scope.add_name('list')
        self.top_scope.add_name('print')
        self.top_scope.add_name('next')
        self.top_scope.add_name('iter')

    def visit_scope(self, node):
        nonlocal_names, global_names = GlobalAndNonLocalFinder.run(node)
        if len(nonlocal_names) != 0 and self.current_scope is None:
            raise SyntaxError("nonlocal declaration not allowed at module level")

        with ScopeSetter(self, node, nonlocal_names, global_names) as scope:
            # set the top-level scope for global name
            if len(self.scopes) == 1:
                assert(self.top_scope is None)
                self.init_top_scope()
            ScopeNameResolver.run(node, self.current_scope)
            if isinstance(node, dast.Program):
                self.visit_one_value(node.body)
            elif isinstance(node, dast.ClassStmt):
                self.visit_one_value(node.body)
            elif isinstance(node, dast.Process):
                self.visit_one_value(node.body)
                self.visit_one_value(node.events)
            elif isinstance(node, dast.Function):
                self.visit_one_value(node.body)

    def visit_Program(self, node : dast.Program):
        # create a scope for top-level
        self.visit_scope(node)

    def visit_ClassStmt(self, node : dast.ClassStmt):
        self.visit_scope(node)

    def visit_Process(self, node: dast.Process):
        self.visit_scope(node)

    def visit_Function(self, node : dast.Function):
        self.visit_scope(node)

    def visit_EventHandler(self, node : dast.EventHandler):
        self.visit_scope(node)
