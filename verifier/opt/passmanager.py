#!/usr/bin/env python3

from .passclasses import Pass

class PassManager(object):
    def __init__(self):
        self.passes = []

    def add_pass(self, p : Pass):
        self.passes.append(p)

    def run(self, modules):
        for p in self.passes:
            p.init()
            p.run(modules)
