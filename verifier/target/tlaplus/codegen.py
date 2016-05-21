from ... import opt, ir
from ...frontend import dast, ScopeType
from .tlaast import *
from .tla_translator import *
import sys
import contextlib

@contextlib.contextmanager
def smart_open(filename=None):
    if filename and filename != '-':
        fh = open(filename, 'w')
    else:
        fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()

class Action(object):
    def __init__(self, pc):
        self.pc = pc

class CodeGen(object):
    def __init__(self, passmanager):
        self.vars = set()
        self.passmanager = passmanager
        self.translator = Translator()

    def var(self, name):
        self.vars.add(name)
        return name

    def gen_pc(self, pc_name, is_group):
        pass

    def fill_unchanged(self, action):
        pass

    def run(self, modules, outfile):
        with smart_open(outfile) as out:
            for module in modules:
                self.tla_module = TlaModule(module.name, [])
                # only scan through
                for function in module.functions:
                    if isinstance(function.ast_node, dast.Program):
                        self.gen_program(function)
                    elif isinstance(function.ast_node, dast.ClassDef):
                        if function.scope.type == ScopeType.Process:
                            self.gen_process(function)
                        else:
                            self.gen_entry_function(function)
                    elif function.scope.type == ScopeType.Main:
                        self.gen_main_function(function)
                #out.write(self.tla_module.to_tla())

    def gen_program(self, function):
        if not CodeGen.is_simple_program(function):
            raise NotImplementedError()

        print(send_action().to_tla())

    @staticmethod
    def is_simple_program(function : ir.Function):
        if len(function.basicblocks) != 2:
            return False
        for inst in function.basicblocks[0].ir:
            if isinstance(inst, ir.Call) and isinstance(inst.func.ast_node, dast.ClassDef):
                continue
            elif isinstance(inst, ir.Assign) and inst.op == '=' and isinstance(inst.target, ir.IRName) and isinstance(inst.expr, ir.Function):
                continue
            return False

        return True

    @staticmethod
    def is_simple_process_class(process):
        return len(process.basicblocks) == 2 and \
            all(isinstance(i, ir.Assign) and \
                isinstance(i.expr, ir.Function) and \
                isinstance(i.target, ir.IRName) \
                for i in process.basicblocks[0].ir)

    def gen_process(self, process):
        assert(self.is_simple_process_class(process))

        for i in process.basicblocks[0].ir:
            if isinstance(i, ir.Assign) and i.expr.ast_node.name == "setup":
                self.gen_init_function(i.expr)
        for i in process.basicblocks[0].ir:
            if isinstance(i, ir.Assign) and i.expr.scope.type == ScopeType.General:
                self.gen_entry_function(i.expr)

        message_handler = []
        for i in process.basicblocks[0].ir:
            if isinstance(i, ir.Assign) and i.expr.scope.type == ScopeType.ReceiveHandler:
                message_handler.append(i.expr)

        self.gen_message_handler(message_handler)

    def gen_main_function(self, func : ir.Function):
        pass

    def gen_init_function(self, func : ir.Function):
        self.translator.translate_function(func)

    def gen_entry_function(self, func : ir.Function):
        self.translator.translate_function(func)

    def gen_message_handler(self, func):
        self.translator.translate_message_handler(func)
