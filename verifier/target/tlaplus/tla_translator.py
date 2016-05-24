from verifier import ir, utils
import enum
from .tlaast import *
from .tla_helper import *
from verifier.frontend import NameType, ScopeType
from verifier.opt import *
from verifier import types
from .fill_unchange import Fill

def check_loop(block, path):
    if block in path:
        return True
    path = path | {block}
    for succ in block.succ:
        if check_loop(succ, path):
            return True

    return False

TlaOperatorMap = {
    '>' : TLA_GT,
    '<' : TLA_LT,
    '==' : TLA_EQ,
    'and' : TLA_AND,
    'or' : TLA_OR,
    '%' : TLA_MOD,
    '-' : TLA_MINUS,
    '!=' : TLA_NEQ,
    'each' : TLA_ALL,
    'some' : TLA_EXISTS,
}

class GetIRNames(utils.NodeVisitor):
    def __init__(self):
        self.result = set()

    def visit_IRName(self, node):
        self.result.add(node.name)


class PatternTranslator(utils.NodeVisitor):
    _nodebaseclass=ir.Value
    def __init__(self, expr, translator, is_assign = False):
        self.stack = []
        self.constrains = []
        self.freevar = []
        self.result = (self.constrains, self.freevar)
        self.expr = expr
        self.is_assign = is_assign
        self.translator = translator

    def indexed_expr(self):
        result = self.expr
        for s in self.stack:
            result = TlaIndexExpr(result, TlaConstantExpr(s))
        return result

    def visit(self, node):
        # this can have bug
        #if len(node.ordered_freevars) == 0:
        #    self.constrains.append(tla_eq(self.indexed_expr(), self.translator.visit(node)))
        #else:
        super().visit(node)

    def visit_Tuple(self, node: ir.Tuple):
        self.constrains.append(tla_eq(TlaInstantiationExpr(TlaSymbol("Len"), [self.indexed_expr()]), TlaConstantExpr(len(node.operands))))
        self.stack.append(1)
        for pattern in node.operands:
            self.visit(pattern)
            self.stack[-1] += 1
        self.stack.pop()

    def visit_Constant(self, node: ir.Constant):
        self.constrains.append(tla_eq(self.indexed_expr(),
                                      TlaConstantExpr(node.value)))

    def is_freevar(self, name):
        for names in reversed(self.translator.quantifier_stack):
            if name in names:
                return False
        return True

    def visit_IRName(self, node: ir.IRName):
        if self.is_freevar(node.name) and (node.name_type == NameType.HandlerPattern or node.name_type == NameType.Pattern or self.is_assign):
            # FIXME, what if same free var appear twice?
            self.freevar.append((self.indexed_expr(), node.name))
        else:
            if node.name_type == NameType.HandlerPattern or node.name_type == NameType.Pattern:
                v = TlaSymbol(node.name)
            else:
                v = apply_expr(node.name, "self")
            self.constrains.append(tla_eq(self.indexed_expr(),
                                        v))

class RWTracker(object):
    def __init__(self):
        self.write_names = dict()
        self.read_names = dict()
        self.inst_to_read_names = dict()
        self.inst_to_write_names = dict()
        self.write_inst_count = dict()

    def update(self, inst, names, is_read):
        names_dict = self.read_names if is_read else self.write_names
        inst_to = self.inst_to_read_names if is_read else self.inst_to_write_names
        inst_to[inst] = names
        for name in names:
            if name not in names_dict:
                names_dict[name] = []
            names_dict[name].append(inst)
            if not is_read:
                if name not in self.write_inst_count:
                    self.write_inst_count[name] = 0
                self.write_inst_count[name] += 1

    def remove(self, inst):
        if inst in self.inst_to_write_names:
            for wname in self.inst_to_write_names[inst]:
                self.write_names[wname].remove(inst)
        if inst in self.inst_to_read_names:
            for rname in self.inst_to_read_names[inst]:
                self.read_names[rname].remove(inst)

    def is_real_assign(self, name):
        return len(self.write_names[name]) == 1

    def has_more_read(self, name):
        return name in self.read_names and len(self.read_names[name]) >= 1

    def get_ssa_name(self, name, read = False):
        if name in self.write_names:
            idx = self.write_inst_count[name] - len(self.write_names[name])
            if read:
                idx -= 1

            if idx < 0:
                return apply_expr(name, "self")
            else:
                return TlaSymbol("{0}_{1}".format(name, idx))
        else:
            return apply_expr(name, "self")

def translate_insts_simple_one_block(top_exprs, insts, translator, skip_branch = True, next_name = None):
    exprs = top_exprs
    rwtracker = RWTracker()
    for inst in insts:
        if isinstance(inst, ir.Assign):
            write_names = GetIRNames.run(inst.target)
            read_names = GetIRNames.run(inst.expr)
            rwtracker.update(inst, write_names, is_read=False)
            rwtracker.update(inst, read_names, is_read=True)
        else:
            read_names = GetIRNames.run(inst)
            rwtracker.update(inst, read_names, is_read=True)

    def handle_assign(name, expr):
        nonlocal exprs

        is_real_assign = rwtracker.is_real_assign(name)
        has_more_read = rwtracker.has_more_read(name)

        if is_real_assign:
            if has_more_read:
                target_expr = rwtracker.get_ssa_name(name)
            else:
                target_expr = expr
        if not is_real_assign or has_more_read:
            next_exprs = []
            exprs.append(TlaLetExpr([TlaDefinitionStmt(rwtracker.get_ssa_name(name), [], expr)], tla_and(next_exprs)))
            exprs = next_exprs

        if is_real_assign:
            exprs.append(except_expr_helper(name, target_expr))

    for inst in insts:
        if isinstance(inst, ir.Assign):
            expr = ExprTranslator.run(inst.expr, rwtracker, translator)
            if isinstance(inst.target, ir.IRName):
                handle_assign(inst.target.name, expr)
            else:
                constrains, freevars = PatternTranslator.run(inst.target, TlaSymbol("_temp_assign"), translator, is_assign=True)
                tuple_exprs = []
                exprs.append(TlaLetExpr([TlaDefinitionStmt(TlaSymbol("_temp_assign"), [], expr)], tla_and(tuple_exprs)))
                exprs = tuple_exprs
                for (val, var) in freevars:
                    handle_assign(var, val)

        elif isinstance(inst, ir.Send):
            message = ExprTranslator.run(inst.value, rwtracker, translator)
            target = ExprTranslator.run(inst.to, rwtracker, translator)
            # FIXME a dirty hack to avoid ssa-ize msg handler
            if inst.parent.function.scope.type != ScopeType.ReceiveHandler:
                msgQ = TlaSymbol("msgQueue")
            else:
                msgQ = TlaExceptExpr(TlaSymbol("msgQueue"), [tla_eq(apply_expr("!", "self"), TlaInstantiationExpr(TlaSymbol("Tail"), [apply_expr("msgQueue", "self")]))])
            exprs.append(TlaInstantiationExpr(TlaSymbol("Send"),
                                                [TlaSymbol("self"), message,
                                                target, msgQ]))
        rwtracker.remove(inst)

    if not skip_branch:
        next_pc = None
        if len(insts) > 0:
            last_inst = insts[-1]
            if isinstance(last_inst, ir.Branch):
                next_block = last_inst.target_block
                next_pc = except_expr_helper('pc', TlaConstantExpr(next_block.function.scope.gen_name(next_block.label)))
            elif isinstance(last_inst, ir.CondBranch):
                block1 = last_inst.target_block
                block2 = last_inst.target_block_alt
                block1_label = block1.function.scope.gen_name(block1.label)
                block2_label = block2.function.scope.gen_name(block2.label)
                cond_expr = ExprTranslator.run(last_inst.condition, rwtracker, translator)
                expr = TlaIfExpr(cond_expr, TlaConstantExpr(block1_label), TlaConstantExpr(block2_label))
                next_pc = except_expr_helper('pc', expr)
        if next_pc is None:
            next_pc = except_expr_helper('pc', TlaConstantExpr(next_name))
        top_exprs.append(next_pc)

    return exprs

# forward name declaration
class Action(object):
    def __init__(self, block, name, next_name):
        self.block = block
        self.name = name
        self.next_name = next_name

    def from_end(self):

        ret_addr_name = self.block.function.scope.gen_name("ret_pc")
        exprs = [self.check_pc()]
        if self.block.label == "end" and self.block.function.ast_node.name == "run":
            exprs.append(tla_eq(TlaSymbol("atomic_barrier'"), TlaConstantExpr(-1)))
        else:
            exprs.append(except_expr_helper('pc', apply_expr(ret_addr_name, 'self')))
        self.tla = TlaDefinitionStmt(TlaSymbol(self.name), [TlaSymbol('self')], tla_and(exprs))

    def from_call(self, call: ir.Call):
        if not isinstance(call.func, ir.Function):
            print(call.func)
            raise NotImplementedError()
        ret_addr_name = call.func.scope.gen_name("ret_pc")
        exprs = [self.check_pc(), except_expr_helper(ret_addr_name, TlaConstantExpr(self.next_name)), except_expr_helper('pc', TlaConstantExpr(call.func.entry_label()))]
        self.tla = TlaDefinitionStmt(TlaSymbol(self.name), [TlaSymbol('self')], tla_and(exprs))

    def from_yield(self):
        process_scope = self.block.function.scope.get_process_scope()
        assert(process_scope is not None)
        ret_addr_name = process_scope.gen_name("yield_ret_pc")
        yield_pc_name = process_scope.gen_name("yield")
        exprs = [self.check_pc(), except_expr_helper(ret_addr_name, TlaConstantExpr(self.next_name)), except_expr_helper('pc', TlaConstantExpr(yield_pc_name))]
        exprs.append(tla_eq(TlaSymbol("atomic_barrier'"), TlaConstantExpr(-1)))
        self.tla = TlaDefinitionStmt(TlaSymbol(self.name), [TlaSymbol('self')], tla_and(exprs))

    def from_insts(self, insts, translator):
        exprs = []
        translate_insts_simple_one_block(exprs, insts, translator, False, self.next_name)
        exprs = [self.check_pc()] + exprs
        self.tla = TlaDefinitionStmt(TlaSymbol(self.name), [TlaSymbol('self')], tla_and(exprs))

    def check_pc(self):
        return pc_is_expr(self.name)

    def read_vars(self):
        return self.wvars;

    def modified_vars(self):
        return

    def to_tla(self):
        return self.tla.to_tla()

class ExprTranslator(utils.NodeVisitor):
    _nodebaseclass = ir.Value
    def __init__(self, rwtracker, translator):
        self.rwtracker = rwtracker
        self.translator = translator

    def visit(self, node):
        result = super().visit(node)
        if result is None:
            print(node)
            raise NotImplementedError()
        return result

    def visit_Call(self, node : ir.Call):
        pass

    def visit_Constant(self, node : ir.Constant):
        return TlaConstantExpr(node.value)

    def visit_List(self, node : ir.List):
        return TlaTupleExpr(self.visit_one_value(node.operands))

    def visit_BinaryOp(self, node : ir.BinaryOp):
        return TlaBinaryExpr(TlaOperatorMap[node.op], self.visit(node.operands[0]), self.visit(node.operands[1]))

    def visit_IRName(self, node : ir.IRName):
        if node.name_type == NameType.Pattern or node.name_type == NameType.HandlerPattern:
            return TlaSymbol(node.name)
        else:
            # fake ssa-ize
            return self.rwtracker.get_ssa_name(node.name, read=True)

    def visit_Cardinality(self, node : ir.Cardinality):
        # TODO: SET
        return TlaInstantiationExpr(TlaSymbol("Len"), [self.visit(node.operands[0])])

    def visit_Received(self, node : ir.Received):
        rcvd = apply_expr('rcvd', 'self')
        temp = TlaSymbol(self.translator.get_tempname("_value"))
        constrains, freevar = PatternTranslator.run(node.pattern, temp, self.translator)
        tla = tla_exists(tla_in(temp, rcvd), tla_and(constrains))
        return tla

    def visit_Append(self, node : ir.Append):
        return tla_append(self.visit(node.container), self.visit(node.elem))

    def visit_PopOneElement(self, node : ir.PopOneElement):
        # FIXME: handle set
        # Move this complex implementation to our helper library?
        container = self.visit(node.expr)
        temp_idx = TlaSymbol("_temp_idx")
        temp_container = TlaSymbol("_temp_container")
        return TlaLetExpr([TlaDefinitionStmt(temp_idx, [], self.visit(node.index)),
                           TlaDefinitionStmt(temp_container, [], container)],
                          TlaTupleExpr([index_expr(temp_container, temp_idx),
                                        tla_concat(inst_expr('SubSeq', temp_container, TlaConstantExpr(1), temp_idx),
                                                   inst_expr('SubSeq', temp_container, TlaBinaryExpr(TLA_ADD, temp_idx, TlaConstantExpr(2)), inst_expr('Len', temp_container)))]))

    def visit_RandomSelect(self, node : ir.RandomSelect):
        return TlaChooseExpr(tla_in(TlaSymbol('_random'), self.visit(node.operands[0])), TlaConstantExpr(True))

    def visit_Range(self, node : ir.Range):
        # FIXME, it's actually seq
        return TlaIntegerSetExpr(TlaConstantExpr(0), TlaBinaryExpr('-', self.visit(node.operands[0]), TlaConstantExpr(1)))

    def visit_UnaryOp(self, node : ir.UnaryOp):
        return TlaUnaryExpr(node.op, self.visit(node.operands[0]))

    def visit_ProcessId(self, node):
        return TlaSymbol("self")

    def visit_Clock(self, node):
        return apply_expr("clock", "self")

    def visit_Set(self, node):
        return TlaSetExpr(self.visit_one_value(node.operands))

    def visit_Tuple(self, node : ir.Tuple):
        values = self.visit_one_value(node.operands)
        return TlaTupleExpr(values)

    def visit_LogicOp(self, node : ir.LogicOp):
        return TlaAndOrExpr(TlaOperatorMap[node.op], self.visit_one_value(node.operands))

    def visit_Quantifier(self, node : ir.Quantifier):
        domain = node.domain
        if isinstance(domain, ir.Received):
            constrains, freevars = PatternTranslator.run(domain.pattern, TlaSymbol("_value"), self.translator)
            self.translator.quantifier_stack.append({var for (_, var) in freevars})
            rcvd = apply_expr('rcvd', 'self')
            filtered_rcvd = TlaSetCompositionExpr(TlaSymbol("_value"), rcvd, tla_and(constrains))
            freevar_def = []
            for (val, var) in freevars:
                freevar_def.append(TlaDefinitionStmt(TlaSymbol(var), [], val))

            has_predicate = self.visit(node.predicate)
            full_predicate = TlaLetExpr(freevar_def, has_predicate)
            self.translator.quantifier_stack.pop()
            return TlaPredicateExpr(TlaOperatorMap[node.op], tla_in(TlaSymbol("_value"), filtered_rcvd), full_predicate)
        elif isinstance(domain, ir.BinaryOp) and domain.op == 'in':
            constrains, freevars = PatternTranslator.run(domain.left, TlaSymbol("_value"), self.translator)
            self.translator.quantifier_stack.append({var for (_, var) in freevars})
            domain_expr = self.visit(domain.right)
            filtered_domain_expr = TlaSetCompositionExpr(TlaSymbol("_value"), domain_expr, tla_and(constrains) if constrains else TlaConstantExpr(True))
            freevar_def = []
            for (val, var) in freevars:
                freevar_def.append(TlaDefinitionStmt(TlaSymbol(var), [], val))

            has_predicate = self.visit(node.predicate)
            full_predicate = TlaLetExpr(freevar_def, has_predicate)
            self.translator.quantifier_stack.pop()
            return TlaPredicateExpr(TlaOperatorMap[node.op], tla_in(TlaSymbol("_value"), filtered_domain_expr), full_predicate)
        return TlaPlaceHolder(node)

class CheckSpecialBranchInstruction(utils.NodeVisitor):
    def __init__(self):
        self.result = False

    def visit(self, node):
        if self.result:
            return
        else:
            super().visit(node)

    def visit_Call(self, node):
        self.result = True

    def visit_Label(self, node):
        self.result = True

class PatternToType(utils.NodeVisitor):
    _nodebaseclass = ir.Value

    def __init__(self):
        pass

    def visit_Tuple(self, node : ir.Tuple):
        return types.Tuple(self.visit_one_value(node.operands))

    def visit_Constant(self, node : ir.Constant):
        # TODO, check string, but anyway
        return types.ConstantString(node.value)

    def visit_IRName(self, node: ir.IRName):
        return types.Unknown(node.origin_name)

def translate_function_simple_one_block(top_exprs, block, translator, has_send):
    insts = block.ir
    exprs = translate_insts_simple_one_block(top_exprs, insts, translator, True)
    # FIXME dirty hack, only for msg handler phi like msgQ
    if not has_send:
        has_send = any(isinstance(inst, ir.Send) for inst in insts)
    if len(block.succ) == 0:
        if not has_send:
            exprs.append(except_expr_helper("msgQueue", inst_expr("Tail", TlaSymbol("@"))))
    if len(insts) > 0 and isinstance(insts[-1], ir.CondBranch):
        last_inst = insts[-1]
        block1 = last_inst.target_block
        block2 = last_inst.target_block_alt
        cond_expr = ExprTranslator.run(last_inst.condition, RWTracker(), translator)
        exprs1 = []
        exprs2 = []
        exprs.append(TlaIfExpr(cond_expr, tla_and(exprs1), tla_and(exprs2)))
        translate_function_simple_one_block(exprs1, block1, translator, has_send)
        translate_function_simple_one_block(exprs2, block2, translator, has_send)
    else:
        if block.succ:
            translate_function_simple_one_block(exprs, next(iter(block.succ)), translator, has_send)
    return exprs


class Translator(object):
    def __init__(self, codegen):
        self.tempname = dict()
        self.codegen = codegen
        self.quantifier_stack = []

    def get_tempname(self, name):
        if name not in self.tempname:
            self.tempname[name] = 0
        self.tempname[name] += 1

        return "{0}_{1}".format(name, self.tempname[name])

    # This is a version with more restriction, but easy to handle before we have SSA/phi node
    def check_translable_as_single_action_restricted(self, function):
        # Let's just reuse our implementation
        # either it only has one basic block, so we don't need to introduce
        # phi but only var renaming
        # Or assigned variable is always dominates by its read
        if self.check_translable_as_single_action(function):
            # only start and end
            if len(function.basicblocks) == 2:
                return True

            idom = function.immediate_dominators()
            read_by = dict()
            write_by = dict()

            for inst in iter_instructions(function):
                AssignTargetVisitor.run(inst, inst, read_by, write_by)

            for wvar, winsts in write_by.items():
                for winst, target in winsts:
                    if wvar not in read_by:
                        continue
                    rinsts = read_by[wvar]
                    if not all(rinst.dominates(winst, idom) for rinst, _ in rinsts):
                        return False

            return True

        return False


    # This is the full version of checking, it actually requires SSA-ize and dominance frontier
    # But Let's not waste our time for this for now.
    def check_translable_as_single_action(self, function):
        visited = set()
        queue = [function.basicblocks[0]]
        # bfs
        while queue:
            block = queue.pop(0)
            visited.add(block)
            if any(CheckSpecialBranchInstruction.run(inst) for inst in block.ir):
                return False
            for next_block in block.succ:
                # no loop
                queue.append(next_block)

        if check_loop(function.basicblocks[0], set()):
            return False

        # can't reach end
        if function.basicblocks[-1] not in visited:
            return False

        assert(len(visited) == len(function.basicblocks))

        return True

    def translate_function(self, function):
        for b in function.basicblocks:
            actions = self.translate_basicblock(b)

    def translate_basicblock(self, block : ir.BasicBlock):

        insts = []
        actions = []

        def cur_name():
            return block.function.scope.gen_name(block.label + ("_" + str(len(actions)) if actions else ""))

        def general_action():
            nonlocal insts
            if insts:
                action = Action(block, cur_name(), next_name())
                action.from_insts(insts, self)
                actions.append(action)

                insts = []
        def next_name():
            if idx + 1 == len(block.ir):
                next_block = next(iter(block.succ))
                return next_block.function.scope.gen_name(next_block.label)

            return block.function.scope.gen_name(block.label + ("_" + str(len(actions) + 1)))

        if block.label == "end":
            action = Action(block, cur_name(), None)
            action.from_end()
            actions.append(action)
        else:
            for idx, inst in enumerate(block.ir):
                if isinstance(inst, ir.Label):
                    general_action()
                    # TODO yield point
                    action = Action( block, cur_name(), next_name())
                    action.from_yield()
                    actions.append(action)
                elif isinstance(inst, ir.Call):
                    general_action()
                    # TODO Simple function call
                    action = Action( block, cur_name(), next_name())
                    action.from_call(inst)
                    actions.append(action)
                else:
                    insts.append(inst)

            if len(insts) != 0:
                general_action()

        for a in actions:
            Fill.run(a.tla, self.codegen.names)
            self.codegen.defines.append(a.tla)

    def check_message_handler_overlap(self, message_handlers):
        pattern_type = {func : PatternToType.run(func.msg_pattern) for func in message_handlers}

        for i, func in enumerate(message_handlers):
            for func2 in message_handlers[i+1:]:
                result, mapping = types.Unifier.run(pattern_type[func], pattern_type[func2])
                if result:
                    print(func.msg_pattern)
                    print(func2.msg_pattern)
                    print(mapping)
                    return True

        return False

    def translate_message_handler(self, message_handlers):
        # TODO, maybe move check to somewhere else
        if self.check_message_handler_overlap(message_handlers) or \
           not all(self.check_translable_as_single_action_restricted(func) for func in message_handlers):
            raise NotImplementedError()

        msg = TlaFieldExpr(TlaSymbol("msg"), TlaSymbol("content"))

        top_exprs = []
        exprs = top_exprs

        for function in message_handlers:
            constrains, freevars = PatternTranslator.run(function.msg_pattern, msg, self)
            freevar_def = []
            for (val, var) in freevars:
                freevar_def.append(TlaDefinitionStmt(TlaSymbol(var), [], val))
            handler_exprs = []
            full_predicate = TlaLetExpr(freevar_def, tla_and(handler_exprs))
            translate_function_simple_one_block(handler_exprs, function.basicblocks[0], self, False)

            next_exprs = []
            exprs.append(TlaIfExpr(tla_and(constrains), full_predicate, tla_and(next_exprs)))
            exprs = next_exprs

        exprs.append(except_expr_helper("msgQueue", inst_expr("Tail", TlaSymbol("@"))))
        yield_action = yield_point_action(message_handlers[0].scope.get_process_scope(), tla_and(top_exprs),
                                 self.codegen.need_rcvd())
        Fill.run(yield_action, self.codegen.names)
        self.codegen.defines.append(yield_action)


if __name__ == "__main__":
    print("TEST")
    ir = ir.Assign(ir.Property(ir.Variable("self"), "s2r"), "=", ir.List([]))
    action = Action.from_inst(ir)
