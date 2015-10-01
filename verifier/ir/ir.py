import verifier.ir

def get_op_bind(n):
    def _get(o):
        return o.get_op(n)
    return _get

def set_op_bind(n):
    def _set(o, op):
        o.set_op(n, op)
    return _set

class Value(object):
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
    def __init__(self, block):
        super().__init__()
        assert block is None or block is BasicBlock
        self.parent = block
        self.operands = []

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

    def repr_operands(self):
        return ", ".join(repr(op) for op in self.operands)

    def __repr__(self):
        return "<{0} [{1}]>".format(self.__class__.__name__, self.repr_operands())

class Label(Instruction):
    def __init__(self, label, block = None):
        super().__init__(block)
        self.label = label

class Variable(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.name)

class Send(Instruction):
    def __init__(self, value, to, block = None):
        super().__init__(block)
        self.set_operands([value, to])

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

class Clock(Instruction):
    def __init__(self, block = None):
        super().__init__(block)

class Constant(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, repr(self.value))

class Property(Instruction):
    def __init__(self, value, name, block = None):
        super().__init__(block)
        self.name = name
        self.set_operands([value])

    def __repr__(self):
        return "<{0} {1} [{2}]>".format(self.__class__.__name__, repr(self.name), self.repr_operands())

class BinaryOp(Instruction):
    def __init__(self, op, left, right, block = None):
        super().__init__(block)
        self.op = op
        self.set_operands([left, right])

    def __repr__(self):
        return "<{0} {1} [{2}]>".format(self.__class__.__name__, repr(self.op), self.repr_operands())

class UnaryOp(Instruction):
    def __init__(self, op, expr, block = None):
        super().__init__(block)
        self.op = op
        self.set_operands([expr])

    def __repr__(self):
        return "<{0} {1} [{2}]>".format(self.__class__.__name__, repr(self.op), self.repr_operands())

class Assign(Instruction):
    def __init__(self, target, op, expr, block = None):
        super().__init__(block)
        self.op = op
        self.set_operands([target, expr])

    def __repr__(self):
        return "<{0} {1} [{2}]>".format(self.__class__.__name__, repr(self.op), self.repr_operands())

class Call(Instruction):
    def __init__(self, func, args, vargs, args2, kwargs, block = None):
        super().__init__(block)
        self.set_operands([func, args, vargs, args2, kwargs])

class CondBranch(Instruction):
    def __init__(self, cond, target_block, block = None):
        super().__init__(block)
        self.set_operands([cond, target_block])

    target_block = property(get_op_bind(1), set_op_bind(1))

class Branch(Instruction):
    def __init__(self, target_block, block = None):
        super().__init__(block)
        self.set_operands([target_block])

    target_block = property(get_op_bind(0), set_op_bind(0))

class PopOneElement(Instruction):
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

class IsEmpty(Instruction):
    def __init__(self, expr, block = None):
        super().__init__(block)
        self.set_operands([expr])

class Return(Instruction):
    def __init__(self, expr, block = None):
        super().__init__(block)
        self.expr = expr

class Function(Value):
    def __init__(self, module, ast_node, scope):
        super().__init__()
        self.module = module
        self.ast_node = ast_node
        self.scope = scope
        self.basicblocks = []

    def remove_block(self, block_idx):
        block = self.basicblocks.pop(block_idx)
        for pred in block.pred:
            pred.succ |= block.succ
            pred.succ.remove(block)
        for succ in block.succ:
            succ.pred |= block.pred
            succ.pred.remove(block)
        block.function = None

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

    def append_inst(self, inst):
        assert isinstance(inst, Instruction)
        self.ir.append(inst)
        inst.parent = self

    def split(self, idx):
        new_block = BasicBlock(self.function, self.label + "_s")
        new_block.ir = self.ir[idx+1:]
        self.ir = self.ir[0:idx+1]
        return new_block

    def add_succ(self, b):
        assert isinstance(b, BasicBlock)
        self.succ.add(b)
        b.pred.add(self)

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.label)


if __name__ == "__main__":
    parm1 = Constant(1)
    parm2 = Constant(2)
    op = BinaryOp('+', parm1, parm1)
    assert len(parm1.uses) == 2
    assert len(parm2.uses) == 0
    parm1.replace_uses_with(parm2)
    assert len(parm1.uses) == 0
    assert len(parm2.uses) == 2
