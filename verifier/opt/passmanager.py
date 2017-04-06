#!/usr/bin/env python3

from .passclasses import Pass
from .. import ir
from ..frontend import NameType

class PassManager(object):
    def __init__(self):
        self.passes = []
        self.idx = -1;
        self.tempvar_idx = 0

    def add_pass(self, p : Pass):
        self.passes.append(p)
        p.pass_manager = self

    def run(self, modules):
        for idx, p in enumerate(self.passes):
            self.idx = idx
            p.init()
            p.run(modules)
        self.idx = len(self.passes)

    def get_pass(self, pass_type):
        # Same pass may run multiple times
        for p in reversed(self.passes[0:self.idx]):
            if isinstance(p, pass_type):
                return p
        return None

    def tempvar(self, scope):
        self.tempvar_idx += 1
        name = "opttmp{0}".format(self.tempvar_idx)
        return ir.IRName(scope.gen_name(name), name, NameType.Local)
