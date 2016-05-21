import re
from ply import yacc
from .lexer import Lexer
from . import dast as ast

class ParseError(Exception):
    def __init__(self, s, lineno):
        self.lineno = lineno
        self.string = s
        self.filename = None
        self.text = None

    def __str__(self):
        return "{0}:{1}:{3}\n{2}".format(self.filename, self.lineno, self.text, self.string)


class Parser(object):

    def __init__(self):
        self.lexer = Lexer()
        self.lexer.build()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self,start="program")

    def _parse_error(self, s, s2):
        raise ParseError(s, s2.lineno)

    def p_program(self, p):
        """program  :  file_input_star ENDMARKER
        """
        p[0] = ast.Program(p[1])

    def p_file_input_star_1(self, p):
        """file_input_star : NEWLINE
                           |
        """
        p[0] = []

    def p_file_input_star_2(self, p):
        """file_input_star : stmt
        """
        p[0] = p[1]

    def p_file_input_star_3(self, p):
        """
            file_input_star : file_input_star stmt
        """
        p[0] = p[1] + p[2]

    def p_decorator(self, p):
        """decorator : AT dotted_name LPAR arglist RPAR NEWLINE
                     | AT dotted_name NEWLINE"""
        p[0] = ast.Decorator(p[2], [] if len(p) == 4 else p[4])

    def p_decorators(self, p):
        """decorators : decorator
                      | decorators decorator"""
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

    def p_decorated(self, p):
        """decorated : decorators classdef
                     | decorators funcdef"""
        p[0] = p[2]
        p[0].decorators = p[1]

    def p_arrow_test_opt(self, p):
        """arrow_test_opt : ARROW test
                          |"""
        p[0] = None if len(p) == 1 else p[2]

    def p_funcdef(self, p):
        """funcdef : DEF NAME parameters arrow_test_opt COLON suite"""
        p[0] = ast.FuncDef(p[2], p[3], p[4], p[6])

    def p_parameters(self, p):
        """parameters : LPAR typedargslist RPAR
                      | LPAR RPAR"""
        p[0] = ast.TypedArgList([], None, [], None) if len(p) == 3 else p[2]

    def p_typedargslist(self, p):
        """typedargslist : typedargs_with_default typedargs_with_default_list
                         | typedargs_with_default typedargs_with_default_list COMMA
                         | typedargs_with_default typedargs_with_default_list COMMA star_typedargslist
                         | star_typedargslist"""
        if len(p) == 2:
            (args, second_arg_list, kwargs) = p[1]
            p[0] = ast.TypedArgList([], args, second_arg_list, kwargs)
        elif len(p) == 3 or len(p) == 4:
            p[0] = ast.TypedArgList([p[1]] + p[2], None, [], None)
        else: # len(p) == 5
            (args, second_arg_list, kwargs) = p[4]
            p[0] = ast.TypedArgList([p[1]] + p[2], args, second_arg_list, kwargs)

    def p_star_typedargslist_1(self, p):
        """star_typedargslist : STAR typedargs_with_default_list
                                | STAR tfpdef typedargs_with_default_list
                                | STAR typedargs_with_default_list COMMA STARSTAR tfpdef
                                | STAR tfpdef typedargs_with_default_list COMMA STARSTAR tfpdef"""
        if len(p) == 3:
            p[0] = (ast.Argument(None, None, None), p[2], None)
        elif len(p) == 4:
            p[0] = (p[2], p[3], None)
        elif len(p) == 6:
            p[0] = (ast.Argument(None, None, None), p[2], p[5])
        else: # len(p) == 7
            p[0] = (p[2], p[3], p[6])

    def p_star_typedargslist_2(self, p):
        """star_typedargslist : STARSTAR tfpdef"""
        p[0] = (None, [], p[2])

    def p_typedargs_with_default_list(self, p):
        """typedargs_with_default_list :
                                       | typedargs_with_default_list COMMA typedargs_with_default"""
        p[0] = [] if len(p) == 1 else p[1] + [p[3]]

    def p_typedargs_with_default(self, p):
        """typedargs_with_default : tfpdef EQUAL test
                                  | tfpdef"""
        if len(p) == 4:
            p[1].value = p[3]
        p[0] = p[1]

    def p_tfpdef(self, p):
        """tfpdef : NAME
                  | NAME COLON test"""
        p[0] = ast.Argument(p[1], None, None if len(p) == 2 else p[3])

    def p_varargslist(self, p):
        """varargslist : varargs_with_default varargs_with_default_list
                       | varargs_with_default varargs_with_default_list COMMA
                       | varargs_with_default varargs_with_default_list COMMA star_varargslist
                       | star_varargslist"""
        if len(p) == 2:
            (args, second_arg_list, kwargs) = p[1]
            p[0] = ast.TypedArgList([], args, second_arg_list, kwargs)
        elif len(p) == 3 or len(p) == 4:
            p[0] = ast.TypedArgList([p[1]] + p[2], None, [], None)
        else: # len(p) == 5
            (args, second_arg_list, kwargs) = p[4]
            p[0] = ast.TypedArgList([p[1]] + p[2], args, second_arg_list, kwargs)

    def p_star_varargslist_1(self, p):
        """star_varargslist : STAR varargs_with_default_list
                                | STAR vfpdef varargs_with_default_list
                                | STAR varargs_with_default_list COMMA STARSTAR vfpdef
                                | STAR vfpdef varargs_with_default_list COMMA STARSTAR vfpdef"""
        if len(p) == 3:
            p[0] = (ast.Argument(None, None, None), p[2], None)
        elif len(p) == 4:
            p[0] = (p[2], p[3], None)
        elif len(p) == 6:
            p[0] = (ast.Argument(None, None, None), p[2], p[5])
        else: # len(p) == 7
            p[0] = (p[2], p[3], p[6])

    def p_star_varargslist_2(self, p):
        """star_varargslist : STARSTAR vfpdef"""
        p[0] = (None, [], p[2])

    def p_varargs_with_default_list(self, p):
        """varargs_with_default_list :
                                       | varargs_with_default_list COMMA varargs_with_default"""
        p[0] = [] if len(p) == 2 else p[1] + [p[3]]

    def p_varargs_with_default(self, p):
        """varargs_with_default : vfpdef EQUAL test"""
        p[1].value = p[3]
        p[0] = p[1]

    def p_vfpdef(self, p):
        """vfpdef : NAME"""
        p[0] = p[1]

    # stmt is a list
    def p_stmt_1(self, p):
        """stmt : simple_stmt"""
        p[0] = p[1]

    def p_stmt_2(self, p):
        """stmt : compound_stmt"""
        p[0] = [p[1]]

    def p_simple_stmt_1(self, p):
        """simple_stmt : simple_stmt_star NEWLINE
                       | simple_stmt_star SEMI NEWLINE"""
        p[0] = p[1]

    def p_simple_stmt_star_1(self, p):
        """simple_stmt_star : small_stmt
                            | simple_stmt_star SEMI small_stmt
        """
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

    def p_small_stmt(self, p):
        """small_stmt : expr_stmt
                      | del_stmt
                      | pass_stmt
                      | flow_stmt
                      | import_stmt
                      | global_stmt
                      | nonlocal_stmt
                      | assert_stmt
        """
        p[0] = p[1]
        p[0].lineno = self.lineno

    def p_expr_stmt_1(self, p):
        """expr_stmt : testlist_star_expr augassign yield_expr
                     | testlist_star_expr augassign testlist
        """
        p[0] = ast.ExprStmt([p[1]], p[2], p[3])

    def p_expr_stmt_2(self, p):
        """expr_stmt : testlist_star_expr equal_yield_expr_testlist_star_expr_star"""
        if len(p[2]) == 0:
            p[0] = ast.ExprStmt([], '=', p[1])
        else:
            p[0] = ast.ExprStmt([p[1]] + p[2][:-1], '=', p[2][-1])

    def p_equal_yield_expr_testlist_star_expr_star(self, p):
        """equal_yield_expr_testlist_star_expr_star :
                                                    | equal_yield_expr_testlist_star_expr_star EQUAL yield_expr
                                                    | equal_yield_expr_testlist_star_expr_star EQUAL testlist_star_expr """
        p[0] = [] if len(p) == 1 else p[1] + [p[3]]

    def p_testlist_star_expr(self, p):
        """testlist_star_expr : test_star_expr_star COMMA
                              | test_star_expr_star
           testlist : test_star COMMA
                    | test_star
           exprlist : expr_star_expr_star COMMA
                    | expr_star_expr_star"""
        if len(p[1]) == 1 and len(p) == 2:
            p[0] = p[1][0]
        else:
            p[0] = ast.TupleExpr(p[1])

    def p_test_star_expr(self, p):
        """test_star_expr : test
                          | star_expr"""
        p[0] = p[1]

    def p_test_star_expr_star(self, p):
        """test_star_expr_star : test_star_expr
                               | test_star_expr_star COMMA test_star_expr
           test_star : test
                     | test_star COMMA test
           expr_star_expr_star : expr_star_expr
                               | expr_star_expr_star COMMA expr_star_expr"""
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

    def p_augassign(self, p):
        """augassign : PLUSEQUAL
                     | MINUSEQUAL
                     | STAREQUAL
                     | SLASHEQUAL
                     | PERCENTEQUAL
                     | AMPEREQUAL
                     | BAREQUAL
                     | CARETEQUAL
                     | LTLTEQUAL
                     | GTGTEQUAL
                     | STARSTAREQUAL
                     | SLASHSLASHEQUAL
        """
        p[0] = p[1]

    def p_del_stmt(self, p):
        """del_stmt : DEL exprlist"""
        p[0] = ast.DelStmt(p[2])

    def p_pass_stmt(self, p):
        """pass_stmt : PASS"""
        p[0] = ast.PassStmt()

    def p_flow_stmt(self, p):
        """flow_stmt : break_stmt
                     | continue_stmt
                     | return_stmt
                     | raise_stmt
                     | yield_stmt"""
        p[0] = p[1]

    def p_break_stmt(self, p):
        """break_stmt : BREAK"""
        p[0] = ast.BreakStmt()

    def p_continue_stmt(self, p):
        """continue_stmt : CONTINUE"""
        p[0] = ast.ContinueStmt()

    def p_return_stmt(self, p):
        """return_stmt : RETURN testlist
                       | RETURN"""
        p[0] = ast.ReturnStmt(None if len(p) == 2 else p[2])

    def p_yield_stmt(self, p):
        """yield_stmt : yield_expr"""
        p[0] = ast.YieldStmt(p[1])

    def p_raise_stmt(self, p):
        """raise_stmt : RAISE
                      | RAISE test
                      | RAISE test FROM test"""
        p[0] = ast.RaiseStmt(None if len(p) < 3 else p[2], None if len(p) < 5 else p[4])

    def p_import_stmt(self, p):
        """import_stmt : import_name
                       | import_from"""
        p[0] = p[1]

    def p_import_name(self, p):
        """import_name : IMPORT dotted_as_names"""
        p[0] = ast.ImportStmt(p[2])

    def p_relative_dot_list_opt(self, p):
        """relative_dot_list_opt : relative_dot_list
                                 |"""
        p[0] = p[1] if len(p) == 2 else []

    def p_relative_dot_list(self, p):
        """relative_dot_list : ELLIPSIS
                             | relative_dot_list ELLIPSIS"""
        p[0] = ["..."] if len(p) == 2 else p[1] + ["..."]

    def p_relative_dot_list_2(self, p):
        """relative_dot_list : DOT
                             | relative_dot_list DOT"""
        p[0] = ["."] if len(p) == 2 else p[1] + ["."]

    def p_import_from_path(self, p):
        """import_from_path : relative_dot_list_opt dotted_name
                            | relative_dot_list"""
        p[0] = p[1] if len(p) == 2 else p[1] + [p[2]]

    def p_import_from_1(self, p):
        """import_from : FROM import_from_path IMPORT STAR"""
        p[0] = ast.ImportStmt([ast.ImportName('*')], p[2])

    def p_import_from_2(self, p):
        """import_from : FROM import_from_path IMPORT LPAR import_as_names RPAR"""
        p[0] = ast.ImportStmt(p[5], p[2])

    def p_import_from_3(self, p):
        """import_from : FROM import_from_path IMPORT import_as_names"""
        p[0] = ast.ImportStmt(p[4], p[2])

    def p_import_as_name(self, p):
        """import_as_name : NAME
                          | NAME AS NAME"""
        p[0] = ast.ImportName([p[1]], None if len(p) == 2 else p[2])

    def p_dotted_as_name(self, p):
        """dotted_as_name : dotted_name
                          | dotted_name AS NAME"""
        p[0] = ast.ImportName(p[1], None if len(p) == 2 else p[2])

    def p_import_as_names(self, p):
        """import_as_names : import_as_name_list COMMA
                           | import_as_name_list"""
        p[0] = p[1]

    def p_import_as_name_list(self, p):
        """import_as_name_list : import_as_name
                               | import_as_name_list COMMA import_as_name"""
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

    def p_dotted_as_names(self, p):
        """dotted_as_names : dotted_as_name
                           | dotted_as_names COMMA dotted_as_name"""
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

    def p_dotted_name(self, p):
        """dotted_name : NAME
                       | dotted_name DOT NAME"""
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

    def p_global_stmt(self, p):
        """global_stmt : GLOBAL name_star"""
        p[0] = ast.GlobalStmt(p[2])

    def p_nonlocal_stmt(self, p):
        """nonlocal_stmt : NONLOCAL name_star"""
        p[0] = ast.NonLocalStmt(p[2])

    def p_name_star(self, p):
        """name_star : NAME
                     | name_star COMMA NAME"""
        p[0] = p[1] if len(p) == 2 else p[1] + [p[3]]

    def p_assert_stmt(self, p):
        """assert_stmt : ASSERT test
                       | ASSERT test COMMA test"""
        p[0] = ast.AssertStmt(p[2], None if len(p) < 5 else p[4])

    def p_compound_stmt(self, p):
        # TODO
        # try_stmt
        # with_stmt
        """compound_stmt : if_stmt
                         | while_stmt
                         | for_stmt
                         | funcdef
                         | classdef
                         | decorated"""
        p[0] = p[1]
        p[0].lineno = self.lineno

    def p_if_stmt(self, p):
        """if_stmt : IF test COLON suite elif_list else_opt"""
        p[0] = ast.IfStmt(p[2], p[4], p[5], p[6])

    def p_elif_list(self, p):
        """elif_list : ELIF test COLON suite elif_list
                     |"""
        p[0] = [] if len(p) == 1 else [ast.ElseIf(p[2], p[4])] + p[5]

    def p_else_opt(self, p):
        """else_opt : ELSE COLON suite
                    |"""
        p[0] = None if len(p) == 1 else p[3]

    def p_while_stmt(self, p):
        """while_stmt : WHILE test COLON suite else_opt"""
        p[0] = ast.WhileStmt(p[2], p[4], p[5])

    def p_for_stmt(self, p):
        """for_stmt : FOR exprlist IN testlist COLON suite else_opt"""
        p[0] = ast.ForStmt(p[2], p[4], p[6], p[7])


    def p_suite(self, p):
        """suite : simple_stmt
                 | NEWLINE INDENT stmt_star DEDENT"""
        p[0] = p[1] if len(p) == 2 else p[3]

    def p_stmt_star(self, p):
        """stmt_star : stmt
                     | stmt_star stmt"""
        p[0] = p[1] if len(p) == 2 else p[1] + p[2]

    def p_test(self, p):
        """test : or_test
                | or_test IF or_test ELSE test
                | lambdadef"""
        p[0] = p[1] if len(p) == 2 else ast.IfElseExpr(p[1], p[3], p[5])

    def p_test_nocond(self, p):
        """test_nocond : or_test
                       | lambdadef_nocond"""
        p[0] = p[1]

    def p_varargslist_opt(self, p):
        """varargslist_opt : varargslist
                           |"""
        p[0] = p[1] if len(p) == 2 else None

    def p_lambdadef(self, p):
        """lambdadef : LAMBDA varargslist_opt COLON test"""
        p[0] = ast.Lambda(p[2], p[4])

    def p_lambdadef_nocond(self, p):
        """lambdadef_nocond : LAMBDA varargslist_opt COLON test_nocond"""
        p[0] = ast.Lambda(p[2], p[4])

    def p_or_test(self, p):
        """or_test : and_test_list"""
        p[0] = p[1][0] if len(p[1]) == 1 else ast.LogicExpr('or', p[1])

    def p_and_test_list(self, p):
        """and_test_list : and_test
                         | and_test_list OR and_test"""
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

    def p_and_test(self, p):
        """and_test : not_test_list"""
        p[0] = p[1][0] if len(p[1]) == 1 else ast.LogicExpr('and', p[1])

    def p_not_test_list(self, p):
        """not_test_list : not_test
                         | not_test_list AND not_test"""
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

    def p_not_test(self, p):
        """not_test : NOT not_test
                    | comparison"""
        p[0] = p[1] if len(p) == 2 else ast.UnaryExpr('not', p[2])

    def p_comparison_1(self, p):
        """comparison : expr"""
        p[0] = p[1]

    def p_comparison_2(self, p):
        """comparison : comparison comp_op expr"""
        p[0] = ast.BinaryExpr(p[2], p[1], p[3])

    def p_comp_op(self, p):
        """comp_op : LESS
                   | GREATER
                   | EQEQUAL
                   | GREATEREQUAL
                   | LESSEQUAL
                   | NOTEQUAL
                   | IN
                   | NOT IN
                   | IS
                   | IS NOT"""
        p[0] = p[1]

    def p_star_expr(self, p):
        """star_expr : STAR expr"""
        p[0] = ast.UnaryExpr("*", p[2])

    def p_expr(self, p):
        """expr : xor_expr
                | expr VBAR xor_expr
           xor_expr : and_expr
                    | xor_expr CIRCUMFLEX and_expr
           and_expr : shift_expr
                    | and_expr AMPER shift_expr
           shift_expr : arith_expr
                      | shift_expr LEFTSHIFT arith_expr
                      | shift_expr RIGHTSHIFT arith_expr
           arith_expr : term
                      | arith_expr PLUS term
                      | arith_expr MINUS term
           term : factor
                | term STAR factor
                | term SLASH factor
                | term PERCENT factor
                | term SLASHSLASH factor"""
        p[0] = p[1] if len(p) == 2 else ast.BinaryExpr(p[2], p[1], p[3])

    def p_factor(self, p):
        """factor : PLUS factor
                  | MINUS factor
                  | TILDE factor
                  | power"""
        p[0] = p[1] if len(p) == 2 else ast.UnaryExpr(p[1], p[2])

    def p_power(self, p):
        """power : atom_trailer_star
                 | atom_trailer_star STARSTAR factor"""
        p[0] = p[1] if len(p) == 2 else ast.BinaryExpr(p[2], p[1], p[3])

    def p_atom_1(self, p):
        """atom : LPAR yield_expr RPAR
                | LPAR testlist_comp RPAR"""
        p[0] = p[2]

    def p_atom_1_1(self, p):
        """atom : LPAR RPAR"""
        p[0] = ast.TupleExpr([])

    def p_atom_2(self, p):
        """atom : LSQB testlist_comp RSQB"""
        p[0] = ast.CompListMaker(p[2])

    def p_atom_2_1(self, p):
        """atom : LSQB RSQB"""
        p[0] = ast.CompListMaker(None)

    def p_atom_3(self, p):
        """atom : LBRACE dictorsetmaker RBRACE"""
        p[0] = p[2]

    def p_atom_4(self, p):
        """atom : NAME"""
        p[0] = ast.Name(p[1])

    def p_atom_5(self, p):
        """atom : NUMBER"""
        p[0] = ast.Number(p[1][0])

    def p_atom_6(self, p):
        """atom : TRUE"""
        p[0] = ast.Boolean(True)

    def p_atom_7(self, p):
        """atom : FALSE"""
        p[0] = ast.Boolean(False)

    def p_atom_8(self, p):
        """atom : NONE"""
        p[0] = ast.NoneNode()

    def p_atom_9(self, p):
        """atom : ELLIPSIS"""
        p[0] = ast.EllipsisNode()

    def p_atom_10(self, p):
        """atom : string_list"""
        p[0] = ast.String(p[1])

    def p_string_list(self, p):
        """string_list : STRING
                       | string_list STRING"""
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

    def p_testlist_comp_1(self, p):
        # TODO
        """testlist_comp : test_star_expr comp_for"""
        p[0] = ast.CompForExpr([p[1]], p[2])

    def p_testlist_comp_2(self, p):
        """testlist_comp : testlist_star_expr"""
        p[0] = p[1]

    def p_atom_trailer_star_1(self, p):
        # expand trailer
        """atom_trailer_star : atom"""
        p[0] = p[1]

    def p_atom_trailer_star_2(self, p):
        # expand trailer
        """atom_trailer_star : atom_trailer_star DOT NAME"""
        p[0] = ast.PropertyExpr(p[1], p[3])

    def p_atom_trailer_star_3(self, p):
        # expand trailer
        """atom_trailer_star : atom_trailer_star LPAR arglist RPAR
                             | atom_trailer_star LPAR RPAR"""
        p[0] = ast.ApplyExpr(p[1], p[3] if len(p) == 5 else ast.ArgList([]))

    def p_atom_trailer_star_4(self, p):
        # expand trailer
        """atom_trailer_star : atom_trailer_star LSQB subscriptlist RSQB
                             | atom_trailer_star LSQB RSQB"""
        p[0] = ast.SubscriptExpr(p[1], p[3] if len(p) == 5 else [])

    def p_subscriptlist(self, p):
        """subscriptlist : subscript
                         | subscript COMMA
                         | subscript COMMA subscriptlist"""

        p[0] = [p[1]] if len(p) == 2 or len(p) == 3 else [p[1]] + p[3]

    def p_subscript_1(self, p):
        """subscript : test"""
        p[0] = p[1]

    def p_subscript_2(self, p):
        """subscript : test_opt COLON test_opt sliceop_opt"""
        p[0] = ast.Subscript()

    def p_test_opt(self, p):
        """test_opt : test
                    |"""
        p[0] = p[1] if len(p) == 2 else None

    def p_sliceop_opt(self, p):
        """sliceop_opt : sliceop
                       |"""
        p[0] = p[1] if len(p) == 2 else None

    def p_sliceop(self, p):
        """sliceop : COLON test
                   | COLON"""
        p[0] = p[2] if len(p) == 3 else None

    def p_expr_star_expr(self, p):
        """expr_star_expr : expr
                          | star_expr"""
        p[0] = p[1]

    def p_dictorsetmaker_1(self, p):
        """dictorsetmaker : test COLON test comp_for"""
        p[0] = ast.CompDictMaker(p[1], p[3], p[4])

    def p_dictorsetmaker_2(self, p):
        """dictorsetmaker : test COLON test test_colon_list"""
        p[0] = ast.EnumDictMaker([(p[1], p[3])] + p[4])

    def p_test_colon_list(self, p):
        """test_colon_list : comma_opt
                           | COMMA test COLON test test_colon_list"""
        p[0] = [] if len(p) == 2 else [(p[2], p[4])] + p[5]

    def p_dictorsetmaker_3(self, p):
        """dictorsetmaker : test comp_for"""
        p[0] = ast.CompSetMaker(p[1], p[2])

    def p_dictorsetmaker_4(self, p):
        """dictorsetmaker : test comma_test_list"""
        p[0] = ast.EnumSetMaker([p[1]] + p[2])

    def p_comma_test_list(self, p):
        """comma_test_list : comma_opt
                           | COMMA test comma_test_list"""
        p[0] = [] if len(p) == 2 else [p[2]] + p[3]

    def p_classdef(self, p):
        """classdef : CLASS NAME COLON suite
                    | CLASS NAME LPAR arglist RPAR COLON suite"""
        p[0] = ast.ClassDef(p[2], [], p[4]) if len(p) == 5 else ast.ClassDef(p[2], p[4], p[7])

    def p_comma_opt(self, p):
        """comma_opt : COMMA
                     |"""
        pass

    def p_arglist_1(self, p):
        """arglist : argument comma_argument_star comma_opt"""
        p[0] = ast.ArgList([p[1]] + p[2])

    def p_arglist_2(self, p):
        """arglist : argument_comma_star STAR test comma_argument_star comma_starstar_test_opt"""
        p[0] = ast.ArgList(p[1], p[3], p[4], p[5])

    def p_arglist_3(self, p):
        """ arglist : argument_comma_star STARSTAR test"""
        p[0] = ast.ArgList(p[1], None, [], p[5])

    def p_comma_starstar_test_opt(self, p):
        """comma_starstar_test_opt : COMMA STARSTAR test
                                   |"""
        p[0] = p[3] if len(p) == 4 else None

    def p_argument_comma_star(self, p):
        """argument_comma_star : argument COMMA argument_comma_star
                               |"""
        p[0] = [] if len(p) == 1 else [p[1]] + p[3]

    def p_comma_argument_star(self, p):
        """comma_argument_star : COMMA argument comma_argument_star
                               |"""
        p[0] = [] if len(p) == 1 else [p[2]] + p[3]

    def p_argument_1(self, p):
        """argument : test comp_for_opt"""
        p[0] = ast.Argument(None, p[1] if p[2] is None else ast.CompForExpr([p[1]], p[2]))

    def p_argument_2(self, p):
        """argument : test EQUAL test"""
        if not isinstance(p[1], ast.Name):
            raise ParseError("keyword can't be an expression", self.lineno)
        p[0] = ast.Argument(p[1].name, p[3])

    def p_comp_iter(self, p):
        """comp_iter : comp_for
                     | comp_if"""
        p[0] = p[1]

    def p_comp_iter_opt(self, p):
        """comp_iter_opt : comp_iter
                         |
           comp_for_opt : comp_for
                         |"""
        p[0] = p[1] if len(p) == 2 else None

    def p_comp_for(self, p):
        """comp_for : FOR exprlist IN or_test comp_iter_opt"""
        p[0] = ast.CompFor(p[2], p[4], p[5])

    def p_comp_if(self, p):
        """comp_if : IF test_nocond comp_iter_opt"""
        p[0] = ast.CompIf(p[2], p[3])

    def p_yield_expr(self, p):
        """yield_expr : YIELD
                      | YIELD yield_arg"""
        p[0] = ast.YieldExpr(None if len(p) == 2 else p[2])

    def p_yield_arg(self, p):
        """yield_arg : FROM test
                     | testlist"""
        p[0] = p[1] if len(p) == 2 else ast.YieldFrom(p[2])

    def p_error(self, p):
        if p:
            self._parse_error(
                'before: %s' % p,
                p)
        else:
            self._parse_error('At end of input', '')

    @property
    def lineno(self):
        return self.lexer.lexer.lineno

    def parse(self, source, filename="<string>"):
        # There is a bug in PLY 2.3; it doesn't like the empty string.
        # Bug reported and will be fixed for 2.4.
        # http://groups.google.com/group/ply-hack/msg/cbbfc50837818a29
        if not source:
            source = "\n"
        try:
            parse_tree = self.parser.parse(source, lexer=self.lexer,debug=0)
        except ParseError as err:
            # Insert the missing data and reraise
            assert hasattr(err, "lineno"), "ParseError is missing lineno"
            geek_lineno = err.lineno - 1
            start_of_line = self.lexer.lexer.line_offsets[geek_lineno]
            end_of_line = self.lexer.lexer.line_offsets[geek_lineno+1]-1
            text = source[start_of_line:end_of_line]
            err.filename = filename
            err.text = text
            raise
        return parse_tree
