from .passclasses import FunctionPass
from ..ir import *
import collections

class Dom(object):
    def __init__(self):
        self.dominated_by = dict()
        self.dominates = dict()
        self.immediate_dominated_by = dict()
        self.dominate_frontier = dict()

class SSAPass(FunctionPass):
    def __init__(self):
        pass

    def run_on_function(self, function : Function):
        dom = Dom()
        self.analysis_dominator(dom, function.basicblocks)
        self.ssa(dom, function.basicblocks)

    def analysis_dominator(self, dom, blocks):
        for b in blocks:
            if b is not blocks[0]:
                dom.dominated_by[b] = set(blocks)
            else:
                dom.dominated_by[b] = {blocks[0]}
            dom.dominates[b] = set()
            dom.immediate_dominated_by[b] = None
            dom.dominate_frontier[b] = set()

        q = collections.deque([blocks[0]])
        visited = set()

        while len(q) > 0:
            b = q.popleft()

            if b is not blocks[0]:
                # print(dom.dominated_by)
                # print([dom.dominated_by[p] for p in b.pred])
                s = set.intersection(*[dom.dominated_by[p] for p in b.pred])
                dom.dominated_by[b] = set.union(set([b]), s)

            for n in b.succ:
                if n not in visited:
                    q.append(n)
                    visited.add(n)

        for b in blocks:
            for n in dom.dominated_by[b]:
                dom.dominates[n].add(b)

                if n in b.pred:
                    dom.immediate_dominated_by[b] = n

        for b in blocks:
            for n in dom.dominates[b]:
                for z in n.succ:
                    if z is b or z not in dom.dominates[b]:
                        dom.dominate_frontier[b].add(z)

    def ssa(self, dom, blocks):
        pass
