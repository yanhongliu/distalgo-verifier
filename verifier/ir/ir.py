import verifier.ir
from functools import reduce

class SliceMaker(object):
    def __getitem__(self, item):
        return item

make_slice = SliceMaker()

def get_op_bind(n):
    def _get(o):
        return o.get_op(n)
    return _get

def set_op_bind(n):
    def _set(o, op):
        o.set_op(n, op)
    return _set

class Value(object):
    _fields = []

    def __init__(self):
        self.uses = set()

    def __repr__(self):
        return "<{0}>".format(self.__class__.__name__)

    def replace_uses_with(self, new_value):
        if self is new_value:
            return
        while self.uses:
            use = self.uses.pop()
            use.user.set_op(use.idx, new_value)

class Use(object):
    def __init__(self, idx, user):
        self.user = user
        self.idx = idx

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.user == other.user and self.idx == other.idx

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.user, self.idx))

class Instruction(Value):
    _fields  = ["operands"]

    def __init__(self, block):
        super().__init__()
        assert block is None or block is BasicBlock
        self.parent = block
        self.operands = []

    def clone(self):
        return type(self)(*[op.clone() for op in self.operands])

    def get_op(self, n):
        if n is tuple:
            idx1, idx2 = n
            return self.operands[idx1][idx2]
        return self.operands[n]

    def set_op(self, n, op):
        old_op = self.get_op(n)
        if isinstance(old_op, list):
            for sub_idx, sub_op in enumerate(op):
                if sub_op is not None:
                    sub_op.uses.discard(Use((n, sub_idx), self))
        else:
            old_op.uses.discard(Use(n, self))

        if n is tuple:
            idx1, idx2 = n
            self.operands[idx1][idx2] = op
            op.uses.add(Use(n, self))
        else:
            self.operands[n] = op
            if isinstance(op, list):
                for sub_idx, sub_op in enumerate(op):
                    if sub_op is not None:
                        sub_op.uses.add(Use((n, sub_idx), self))
            else:
                op.uses.add(Use(n, self))


    def set_operands(self, ops):
        self.operands[:] = ops
        for idx, op in enumerate(ops):
            if op is not None:
                if isinstance(op, list):
                    for sub_idx, sub_op in enumerate(op):
                        if sub_op is not None:
                            sub_op.uses.add(Use((idx, sub_idx), self))
                else:
                    op.uses.add(Use(idx, self))

    def dominates(self, other, idom = None):
        if self is other:
            return True

        if self.parent is not None:
            if self.parent is other.parent:
                block = self.parent
                for inst in block.ir:
                    if inst is self:
                        return True
                    elif inst is other:
                        return False
                return False

            if self.parent.function is other.parent.function:
                if idom is not None:
                    block = other.parent
                    while block in idom:
                        if block is self.parent:
                            return True
                        if block is idom[block]:
                            break
                        block = idom[block]
                return False

            if self.parent.function.scope.is_parent_of(other.parent.function.scope):
                return True

        return False

    def repr_operands(self):
        return ", ".join(repr(op) for op in self.operands)

    def __repr__(self):
        return "<{0} [{1}]>".format(self.__class__.__name__, self.repr_operands())

class Label(Instruction):
    def __init__(self, label, block = None):

        super().__init__(block)
        self.label = label

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.label)

    def clone(self):
        return type(self)(self.label)

class Variable(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.name)

    def clone(self):
        return type(self)(self.name)

class Send(Instruction):
    def __init__(self, value, to, block = None):
        super().__init__(block)
        self.set_operands([value, to])

    value = property(get_op_bind(0), set_op_bind(0))
    to = property(get_op_bind(1), set_op_bind(1))

# API, see api.py, accept dict, list, or pid
class Start(Instruction):
    def __init__(self, process, args, block = None):
        super().__init__(block)
        self.set_operands([process, args])

class Setup(Instruction):
    def __init__(self, process, args, block = None):
        super().__init__(block)
        self.set_operands([process, args])

class New(Instruction):
    def __init__(self, process_type, num, block = None):
        super().__init__(block)
        self.set_operands([process_type, num])

class Config(Instruction):
    def __init__(self, properties, block = None):
        super().__init__(block)
        self.set_operands([properties])

class Tuple(Instruction):
    def __init__(self, items, block = None):
        super().__init__(block)
        self.set_operands(items)

class FreePattern(Value):
    def __init__(self):
        super().__init__()

class List(Instruction):
    def __init__(self, items, block = None):
        super().__init__(block)
        self.set_operands(items)

class Clock(Instruction):
    def __init__(self, block = None):
        super().__init__(block)

class ProcessId(Instruction):
    def __init__(self, block = None):
        super().__init__(block)

    def __repr__(self):
        return "<{0}>".format(self.__class__.__name__)

class Constant(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, repr(self.value))

    def clone(self):
        return type(self)(self.value)

class SubScript(Instruction):
    def __init__(self, value, subscript, block = None):
        super().__init__(block)
        self.set_operands([value, subscript])

    value = property(get_op_bind(0), set_op_bind(0))
    subscript = property(get_op_bind(1), set_op_bind(1))

class Set(Instruction):
    def __init__(self, items, block = None):
        super().__init__(block)
        self.set_operands(items)

class IntegerSet(Instruction):
    def __init__(self, start, end, block = None):
        super().__init__(block)
        self.set_operands([start, end])

class Max(Instruction):
    def __init__(self, item, block = None):
        super().__init__(block)
        self.set_operands(item)

    value = property(get_op_bind(0), set_op_bind(0))

class Min(Instruction):
    def __init__(self, item, block = None):
        super().__init__(block)
        self.set_operands(item)

    value = property(get_op_bind(0), set_op_bind(0))

class SetComp(Instruction):
    def __init__(self, elem, conditions, block = None):
        super().__init__(block)
        self.set_operands([elem] + conditions)

    elem = property(get_op_bind(0), set_op_bind(0))

    @property
    def conditions(self):
        return self.operands[1:]

    def clone(self):
        return type(self)(self.elem.clone(), [c.clone() for c in self.conditions])

class Property(Instruction):
    def __init__(self, value, name, block = None):
        super().__init__(block)
        self.name = name
        self.set_operands([value])

    def __repr__(self):
        return "<{0} {1} [{2}]>".format(self.__class__.__name__, repr(self.name), self.repr_operands())

class Received(Value):
    def __init__(self):
        super().__init__()

class Sent(Value):
    def __init__(self):
        super().__init__()

class LogicOp(Instruction):
    def __init__(self, op, conds, block = None):
        super().__init__(block)
        self.op = op
        self.set_operands(conds)

    def __repr__(self):
        return "<{0} {1} [{2}]>".format(self.__class__.__name__, repr(self.op), self.repr_operands())

class BinaryOp(Instruction):
    def __init__(self, op, left, right, block = None):
        super().__init__(block)
        self.op = op
        self.set_operands([left, right])

    def __repr__(self):
        return "<{0} {1} [{2}]>".format(self.__class__.__name__, repr(self.op), self.repr_operands())

    left = property(get_op_bind(0), set_op_bind(0))
    right = property(get_op_bind(1), set_op_bind(1))

class UnaryOp(Instruction):
    def __init__(self, op, expr, block = None):
        super().__init__(block)
        self.op = op
        self.set_operands([expr])

    def __repr__(self):
        return "<{0} {1} [{2}]>".format(self.__class__.__name__, repr(self.op), self.repr_operands())

    expr = property(get_op_bind(0), set_op_bind(0))

class Assign(Instruction):
    def __init__(self, target, op, expr, block = None):
        super().__init__(block)
        self.op = op
        self.set_operands([target, expr])

    def __repr__(self):
        return "<{0} {1} [{2}]>".format(self.__class__.__name__, repr(self.op), self.repr_operands())

    target = property(get_op_bind(0), set_op_bind(0))
    expr = property(get_op_bind(1), set_op_bind(1))

class Call(Instruction):
    def __init__(self, func, args, vargs, kwargs, block = None):
        super().__init__(block)
        ops = [func] + args
        if vargs is not None:
            self.vargs_idx = len(ops)
            ops.append(vargs)
        else:
            self.vargs_idx = -1

        if kwargs is not None:
            self.kwargs_idx = len(ops)
            ops.append(kwargs)
        else:
            self.kwargs_idx = -1

        self.set_operands(ops)

    func = property(get_op_bind(0), set_op_bind(0))
    @property
    def args(self):
        if self.vargs_idx > 0:
            return self.operands[1:self.vargs_idx]
        else:
            return self.operands[1:]

class CondBranch(Instruction):
    def __init__(self, cond, target_block, target_block2, block = None):
        super().__init__(block)
        self.set_operands([cond, target_block, target_block2])

    condition = property(get_op_bind(0), set_op_bind(0))
    target_block = property(get_op_bind(1), set_op_bind(1))
    target_block_alt = property(get_op_bind(2), set_op_bind(2))

class IfElse(Instruction):
    def __init__(self, cond, expr, elseexpr, block = None):
        super().__init__(block)
        self.set_operands([cond, expr, elseexpr])

    condition = property(get_op_bind(0), set_op_bind(0))
    expr = property(get_op_bind(1), set_op_bind(1))
    elseexpr = property(get_op_bind(2), set_op_bind(2))

class Branch(Instruction):
    def __init__(self, target_block, block = None):
        super().__init__(block)
        self.set_operands([target_block])

    target_block = property(get_op_bind(0), set_op_bind(0))

class PopOneElement(Instruction):
    def __init__(self, expr, index, block = None):
        super().__init__(block)
        self.set_operands([expr, index])

    expr = property(get_op_bind(0), set_op_bind(0))
    index = property(get_op_bind(1), set_op_bind(1))

class Append(Instruction):
    def __init__(self, container, item, block = None):
        super().__init__(block)
        self.set_operands([container, item])

    container = property(get_op_bind(0), set_op_bind(0))
    elem = property(get_op_bind(1), set_op_bind(1))

class RandomSelect(Instruction):
    def __init__(self, expr, block = None):
        super().__init__(block)
        self.set_operands([expr])

class Integer(Instruction):
    def __init__(self, expr, block = None):
        super().__init__(block)
        self.set_operands([expr])

class Range(Instruction):
    def __init__(self, expr, block = None):
        super().__init__(block)
        self.set_operands([expr])

class Cardinality(Instruction):
    def __init__(self, expr, block = None):
        super().__init__(block)
        self.set_operands([expr])
    expr = property(get_op_bind(0), set_op_bind(0))

class IsEmpty(Instruction):
    def __init__(self, expr, block = None):
        super().__init__(block)
        self.set_operands([expr])
    expr = property(get_op_bind(0), set_op_bind(0))

class Return(Instruction):
    def __init__(self, expr, block = None):
        super().__init__(block)
        self.set_operands([expr])

    expr = property(get_op_bind(0), set_op_bind(0))

class Function(Value):
    def __init__(self, module, ast_node, scope, args):
        super().__init__()
        self.module = module
        self.ast_node = ast_node
        self.scope = scope
        self.basicblocks = []
        self.args = []

    def remove_block_by_idx(self, block_idx):
        block = self.basicblocks.pop(block_idx)
        for pred in block.pred:
            pred.succ |= block.succ
            pred.succ.remove(block)
        for succ in block.succ:
            succ.pred |= block.pred
            succ.pred.remove(block)
        block.function = None

    def remove_block(self, block):
        for i, b in enumerate(self.basicblocks):
            if b is block:
                self.remove_block_by_idx(i)
                return

    def __repr__(self):
        return "<{0} ({1} {2})>".format(self.__class__.__name__, self.ast_node.__class__.__name__,
                                        self.ast_node.name if hasattr(self.ast_node, 'name') else '')

    def dfs(self):
        block = self.basicblocks[0]
        stack = [block]
        visited = set()
        order = []

        while stack:
            block = stack.pop()
            visited.add(block)
            order.append(block)
            new = [next_block for next_block in block.succ if next_block not in visited]
            stack = new + stack

        return order

    def immediate_dominators(self):
        idom = {self.basicblocks[0]: self.basicblocks[0]}

        order = self.dfs()
        dfn = {u: i for i, u in enumerate(reversed(order))}
        order.pop(0)
        # order.reverse()

        def intersect(u, v):
            while u != v:
                while dfn[u] < dfn[v]:
                    u = idom[u]
                while dfn[u] > dfn[v]:
                    v = idom[v]
            return u

        changed = True
        while changed:
            changed = False
            for u in order:
                new_idom = reduce(intersect, (v for v in u.pred if v in idom))
                if u not in idom or idom[u] != new_idom:
                    idom[u] = new_idom
                    changed = True

        return idom

    def entry_label(self):
        return self.scope.gen_name(self.basicblocks[0].label)

class BasicBlock(Value):
    def __init__(self, function, label):
        super().__init__()
        self.ir = []
        self.label = label
        self.succ = set()
        self.pred = set()
        self.function = function
        assert isinstance(function, Function) or function is None
        assert label is not None

    def update_inst_parent(self):
        for inst in self.ir:
            inst.parent = self;

    def append_inst(self, inst):
        assert isinstance(inst, Instruction)
        self.ir.append(inst)
        inst.parent = self

    def replace_inst(self, inst_from, inst_to):
        # FIXME, maybe more maintenance is required
        for idx, inst in enumerate(self.ir):
            if inst is inst_from:
                self.ir[idx] = inst_to
                inst_to.parent = self
                return

    def insert_inst(self, inst, before):
        for idx, i in enumerate(self.ir):
            if i is before:
                self.insert_inst_by_idx(inst, idx)
                return

    def insert_inst_by_idx(self, inst, idx):
        self.ir.insert(idx, inst)
        inst.parent = self

    def remove_inst(self, inst):
        self.ir.remove(inst)

    def split(self, idx):
        new_block = BasicBlock(self.function, self.label + "_s")
        new_block.ir = self.ir[idx+1:]
        self.ir = self.ir[0:idx+1]
        new_block.update_inst_parent()
        return new_block

    def add_succ(self, b):
        assert isinstance(b, BasicBlock)
        self.succ.add(b)
        b.pred.add(self)

    def remove_succ(self, b):
        assert isinstance(b, BasicBlock)
        self.succ.remove(b)
        b.pred.remove(self)

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.label)

class Module(object):
    def __init__(self, name):
        self.name = name
        self.functions = []

    def add_function(self, func):
        self.functions.append(func)

class Quantifier(Instruction):
    def __init__(self, op, domain, predicate, block=None):
        super().__init__(block)
        self.op = op
        self.set_operands([predicate] + domain)

    def __repr__(self):
        return "<{0} {1} {2} has={3}>".format(self.__class__.__name__, self.op, self.operands[1:], self.predicate)

    predicate = property(get_op_bind(0), set_op_bind(0))

class IRName(Value):
    def __init__(self, name, origin_name, typ):
        super().__init__()
        self.name = name
        self.origin_name = origin_name
        self.name_type = typ

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.name)

    def clone(self):
        return type(self)(self.name, self.origin_name, self.name_type)

if __name__ == "__main__":
    parm1 = Constant(1)
    parm2 = Constant(2)
    op = BinaryOp('+', parm1, parm1)
    assert len(parm1.uses) == 2
    assert len(parm2.uses) == 0
    parm1.replace_uses_with(parm2)
    assert len(parm1.uses) == 0
    assert len(parm2.uses) == 2
