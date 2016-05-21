#!/usr/bin/env python3

from .passclasses import Pass

class PassManager(object):
    def __init__(self):
        self.passes = []

    def add_pass(self, p : Pass):
        self.passes.append(p)
        p.pass_manager = self

    def run(self, modules):
        for p in self.passes:
            p.init()
            p.run(modules)

    def get_pass(self, pass_type):
        # Same pass may run multiple times
        for p in reversed(self.passes):
            if isinstance(p, pass_type):
                return p
        return None
