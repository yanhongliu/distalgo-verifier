from verifier import utils

def naive_checker(u, v):
    return (u.name == v.name)


# normalized function/variable for internal use
class NormalizedFunction:

    def __init__(self, name, origin):
        self.name = name
        self.childs = []
        self.parents = set()
        self.origin = origin

    def __repr__(self):
        return "{0}({1})".format(self.name, ", ".join([repr(child) for child in self.childs]))

class NormalizedVariable:
    def __init__(self, name, origin):
        self.name = name
        self.parents = set()
        self.origin = origin

    def __repr__(self):
        return self.name

class Visitor(utils.NodeVisitor):
    _result = ("functions", "variables", "root")

    def __init__(self, varname):
        self.varname = varname
        self.f = set()
        self.v = set()
        self.root = None

    def visit(self, node):
        if self.root is None:
            self.root = node

        childs = getattr(node, "childs", None)
        if childs is not None:
            self.f.add(node)
        else:
            self.v.add(node)

        return super().visit(node)

    def post_run(self, result):
        self.variables = dict()
        self.function_norm = dict()
        self.functions = dict()
        for v in self.v:
            if v.name in self.varname:
                self.variables[v] = self.varname[v.name]
            else:
                self.varname[v.name] = NormalizedVariable(v.name, v)
                self.variables[v] = self.varname[v.name]

        for f in self.f:
            self.functions[f] = NormalizedFunction(f.name, f)

        for f in self.functions.values():
            f.childs = [self.functions[child] if child in self.functions else self.variables[child] for child in f.origin.childs]

        # build parent
        for f in self.functions.values():
            for child in f.childs:
                child.parents.add(f)

        self.root = self.functions[self.root] if self.root in self.functions else self.variables[self.root]

class Unifier(object):
    def __init__(self, checker):
        self.checker = checker

    def finish(self, r):
        if r in self.pointer:
            return False
        else:
            self.pointer[r] = r

        stack = []
        stack.append(r)
        while stack:
            s = stack.pop()
            if isinstance(r, NormalizedFunction) and isinstance(s, NormalizedFunction):
                if (not self.checker(r, s) or len(r.childs) != len(s.childs)):
                    return False

            for t in list(s.parents):
                self.finish(t)

            for (src, dest) in list(self.undirected_edge):
                t = None
                if src == s:
                    t = dest
                elif dest == s:
                    t = src
                if t is None:
                    continue

                if t == r:
                    pass
                elif t not in self.pointer:
                    self.pointer[t] = r
                    stack.append(t)
                elif self.pointer[t] != r:
                    return False

                self.undirected_edge.remove((src, dest))


            if s != r:
                if isinstance(s, NormalizedVariable):
                    self.result.append((s, r))
                elif isinstance(s, NormalizedFunction) and isinstance(r, NormalizedFunction) and len(s.childs) > 0:
                    for sonr, sons in zip(r.childs, s.childs):
                        self.undirected_edge.add((sonr, sons))
                self.remove_node(s)

        self.remove_node(r)
        return True

    def remove_node(self, r):
        if r in self.normfuncs:
            self.normfuncs.remove(r)
        elif r in self.normvars:
            self.normvars.remove(r)
        if isinstance(r, NormalizedFunction):
            for c in r.childs:
                if r in c.parents:
                    c.parents.remove(r)
            r.childs = []

    def test_unify(self, u, v):
        self.varname = dict()
        self.pointer = dict()
        (ufunc, uvar, u) = Visitor.run(u, self.varname)
        (vfunc, vvar, v) = Visitor.run(v, self.varname)
        self.normfuncs = set(ufunc.values()) | set(vfunc.values())
        self.normvars = set(uvar.values()) | set(uvar.values())
        self.undirected_edge = {(u, v)}

        self.result = []
        while self.normfuncs:
            r = next(iter(self.normfuncs))
            if not self.finish(r):
                return (False, [])
        while self.normvars:
            r = next(iter(self.normvars))
            if not self.finish(r):
                return (False, [])

        return (True, self.result)

    @classmethod
    def run(cls, u, v, checker=naive_checker):
        unifier = Unifier(checker)
        return unifier.test_unify(u, v)


