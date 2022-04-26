import argparse
from pythonLexer import IndentLexer, tokens
from ply import yacc
from pythonAST import Node, visit
from pythonST import first_pass, second_pass
from pythonTypeChecker import TypeChecker
from pythonTAC import IRGen

class pythonParser:
    precedence = (
        ('left', 'OR', 'NOT'),
        ('left', 'AND'),
        ('left', 'EQUALS', 'NOT_EQUALS'),
        ('left', 'LESS_THAN', 'LESS_THAN_OR_EQ', 'GREATER_THAN', 'GREATER_THAN_OR_EQ'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'MULTIPLY', 'DIVIDE'),
        ('left', 'UNARY')
    )

    ################################
    ### GENERAL STATEMENTS
    ################################
    def p_program(self, p):
        '''
        program : statements
        '''
        p[0] = Node("program", [p[1]], "program")
        p[0].lineno = p.lineno(1)


    def p_statements(self, p):
        '''
        statements : statement
                   | statement statements
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[2]
        # children = [p[1]]
        # if len(p) > 2:
        #   children.append(p[2])
        # p[0] = Node("statements", children)

    def p_statement(self, p):
        '''
        statement : simple_statements
                  | statement_with_block
                  | NEWLINE
        '''
        if (p[1] == '\n'):
            p[0] = Node("statement_newline", [], "NEWLINE")
            p[0].lineno = p.lineno(1)
        else:
            p[0] = p[1]
        # if (p[1] == '\n'):
        #   p[0] = Node("statement", [], "NEWLINE")
        #   return
        # p[0] = Node("statement", [p[1]])

    # def p_multiple_simple_statements(self, p):
    #     '''
    #     multiple_simple_statements : simple_statements
    #                                | simple_statements NEWLINE multiple_simple_statements
    #     '''
    #     p[0] = p[1]

    def p_simple_statements(self, p):
        '''
        simple_statements : simple_statement NEWLINE
        '''
        p[0] = p[1]
        # p[0] = Node("simple_statements", [p[1]])

    def p_statement_with_block(self, p):
        '''
        statement_with_block : class_decl
                             | method_decl
                             | if_stmnt
                             | elif_stmnt
                             | else_statement
                             | for_statement
                             | while_statement
        '''
        p[0] = p[1]
        # p[0] = Node("statement_with_block", [p[1]])

    def p_simple_statement_reserved(self, p):
        '''
        simple_statement : reserved_words_statement
        '''
        p[0] = p[1]
        # p[0] = Node("simple_statement", [], p[1])

    def p_simple_statement(self, p):
        '''
        simple_statement : variable_assignment
                         | expressions_wrapper
                         | import_statement
                         | return_statement
                         | id_
        '''
        # print("hmm1")
        p[0] = p[1]
        # p[0] = Node("simple_statement", [p[1]])

    ################################
    ### CLASS
    ################################
    def p_class_decl(self, p):
        '''
         class_decl : CLASS ID COLON block
                    | CLASS ID L_PARENTHESE id_ R_PARENTHESE COLON block
        '''
        children = [p[4]]
        if (len(p) > 5):
          children.append(p[7])
        p[0] = Node("class_decl", children, p[2])
        p[0].lineno = p.lineno(1)

    ################################
    ### METHOD
    ################################

    def p_method_decl_no_params(self, p):
        '''
        method_decl : METHOD_DEF ID L_PARENTHESE R_PARENTHESE COLON block
                    | METHOD_DEF ID L_PARENTHESE SELF R_PARENTHESE COLON block
        '''
        if p[4] == "self":
            p[0] = Node("method_decl", [p[7]], p[2])
        else:
            p[0] = Node("method_decl", [p[6]], p[2])


        p[0].lineno = p.lineno(1)

    def p_method_decl_no_params_return_type(self, p):
        '''
        method_decl : METHOD_DEF ID L_PARENTHESE R_PARENTHESE RIGHT_ARROW TYPE COLON block
                    | METHOD_DEF ID L_PARENTHESE SELF R_PARENTHESE RIGHT_ARROW TYPE COLON block
        '''
        if p[4] == "self":
            p[0] = Node("method_decl", [p[9]], p[2])
            p[0].data_type = p[7]
        else:
            p[0] = Node("method_decl", [p[8]], p[2])
            p[0].data_type = p[6]

        p[0].lineno = p.lineno(1)


    def p_method_decl_params_no_types_no_return_type(self, p):
        '''
        method_decl : METHOD_DEF ID L_PARENTHESE ids_one_or_more_in_commas_wrapper R_PARENTHESE COLON block
                    | METHOD_DEF ID L_PARENTHESE SELF COMMA ids_one_or_more_in_commas_wrapper R_PARENTHESE COLON block
        '''
        if p[4] == "self":
            p[0] = Node("method_decl", [p[6], p[9]], p[2])
        else:
            p[0] = Node("method_decl", [p[4], p[7]], p[2])

        p[0].lineno = p.lineno(1)

    def p_method_decl_params_no_types_return_type(self, p):
        '''
        method_decl : METHOD_DEF ID L_PARENTHESE ids_one_or_more_in_commas_wrapper R_PARENTHESE RIGHT_ARROW TYPE COLON block
                    | METHOD_DEF ID L_PARENTHESE SELF COMMA ids_one_or_more_in_commas_wrapper R_PARENTHESE RIGHT_ARROW TYPE COLON block
        '''
        if p[4] == "self":
            p[0] = Node("method_decl", [p[6], p[11]], p[2])
            p[0].data_type = p[9]
        else:
            p[0] = Node("method_decl", [p[4], p[9]], p[2])
            p[0].data_type = p[7]

        p[0].lineno = p.lineno(1)

    def p_method_decl_params_types_return_type(self, p):
        '''
        method_decl : METHOD_DEF ID L_PARENTHESE ids_one_or_more_in_commas_with_types_wrapper R_PARENTHESE RIGHT_ARROW TYPE COLON block
                    | METHOD_DEF ID L_PARENTHESE SELF COMMA ids_one_or_more_in_commas_with_types_wrapper R_PARENTHESE RIGHT_ARROW TYPE COLON block
        '''
        if p[4] == "self":
            p[0] = Node("method_decl", [p[6], p[11]], p[2])
            p[0].data_type = p[9]
        else:
            p[0] = Node("method_decl", [p[4], p[9]], p[2])
            p[0].data_type = p[7]

        p[0].lineno = p.lineno(1)


    def p_method_decl_params_types_no_return_type(self, p):
        '''
        method_decl : METHOD_DEF ID L_PARENTHESE ids_one_or_more_in_commas_with_types_wrapper R_PARENTHESE COLON block
                    | METHOD_DEF ID L_PARENTHESE SELF COMMA ids_one_or_more_in_commas_with_types_wrapper R_PARENTHESE COLON block
        '''
        if p[4] == "self":
            p[0] = Node("method_decl", [p[6], p[9]], p[2])
        else:
            p[0] = Node("method_decl", [p[4], p[7]], p[2])

        p[0].lineno = p.lineno(1)


    def p_ids_one_or_more_in_commas_with_types_wrapper(self, p):
        '''
        ids_one_or_more_in_commas_with_types_wrapper : ids_one_or_more_in_commas_with_types
        '''
        p[0] = Node("ids_one_or_more_in_commas_with_types_wrapper", [p[1]])
        p[0].lineno = p.lineno(1)

    def p_ids_one_or_more_in_commas_with_types(self, p):
        '''
        ids_one_or_more_in_commas_with_types : id_ COLON TYPE
                                             | id_ COLON TYPE COMMA ids_one_or_more_in_commas_with_types
        '''
        # children = [p[1], p[3]]
        # if (len(p) > 4):
        #   children.append(p[5])
        # p[0] = Node("ids_one_or_more_in_commas_with_types", children)
        if len(p) == 4:
            p[0] = [p[1], p[3]]
        else:
            p[0] = [p[1], p[3]] + p[5]



    ################################
    ### IF
    ################################
    def p_if_stmnt(self, p):
        '''
        if_stmnt : IF expression COLON block
        '''
        p[0] = Node("if_stmnt", [p[2], p[4]])
        p[0].lineno = p.lineno(1)

    def p_if_stmnt_continued(self, p):
        '''
        if_stmnt : IF expression COLON block elif_stmnt
                 | IF expression COLON block else_statement
        '''
        p[0] = Node("if_stmnt", [p[2], p[4], p[5]])
        p[0].lineno = p.lineno(1)


    def p_elif_stmnt(self,p):
        '''
        elif_stmnt : ELSE_IF expression COLON block
        '''
        p[0] = Node("elif_stmnt", [p[2], p[4]])
        p[0].lineno = p.lineno(1)

    def p_elif_stmnt_continued(self,p):
        '''
        elif_stmnt : ELSE_IF expression COLON block elif_stmnt
                   | ELSE_IF expression COLON block else_statement
        '''
        p[0] = Node("elif_stmnt", [p[2], p[4], p[5]])
        p[0].lineno = p.lineno(1)


    def p_else_stmnt(self,p):
        '''
        else_statement : ELSE COLON block
        '''
        p[0] = Node("else_stmnt", [p[3]])
        p[0].lineno = p.lineno(1)

    ################################
    ### FOR
    ################################
    def p_for_statement(self, p):
        '''
        for_statement : FOR for_stmnt_parameter_wrapper COLON block
        '''
        p[0] = Node("for_statement", [p[2], p[4]])
        p[0].lineno = p.lineno(1)


    def p_for_statement_parameter_wrapper(self, p):
        '''
        for_stmnt_parameter_wrapper : id_ IN RANGE L_PARENTHESE expression R_PARENTHESE
                                    | id_ IN RANGE L_PARENTHESE integer_number R_PARENTHESE
                                    | id_ IN RANGE L_PARENTHESE integer_number COMMA integer_number R_PARENTHESE
                                    | id_ IN RANGE L_PARENTHESE integer_number COMMA integer_number COMMA integer_number R_PARENTHESE
        '''
        if len(p) == 7:
            p[0] = Node("for_statement_paramteres", [p[5]], p[1])
        elif len(p) == 9:
            p[0] = Node("for_statement_paramteres", [p[5], p[7]], p[1])
        else:
            p[0] = Node("for_statement_paramteres", [p[5], p[7], p[9]], p[1])

        p[0].lineno = p.lineno(1)


    ################################
    ### WHILE
    ################################
    def p_while_statement(self, p):
        '''
        while_statement : WHILE expression COLON block
        '''
        p[0] = Node("while_statement", [p[2], p[4]])
        p[0].lineno = p.lineno(1)

    ################################
    ### IMPORTS
    ################################
    def p_import_statement(self, p):
        '''
        import_statement : IMPORT id_
        '''
        p[0] = Node("import_statement", [p[2]])
        p[0].lineno = p.lineno(1)

    def p_import_from_statement(self, p):
        '''
        import_statement : FROM id_ IMPORT id_
        '''
        p[0] = Node("import_statement", [p[2], p[4]])
        p[0].lineno = p.lineno(1)

    ################################
    ### RETURN
    ################################
    def p_return_statement(self, p):
        '''
        return_statement : RETURN expression
        '''
        p[0] = Node("return_statement", [p[2]])
        p[0].lineno = p.lineno(1)

    ################################
    ### BLOCKS
    ################################
    def p_block_dedent(self, p):
        '''
        block : NEWLINE INDENT statements DEDENT
        '''
        p[0] = p[3]
        # p[0] = Node("block", [p[3]])

    def p_block_statements(self, p):
        '''
        block : statements
        '''
        p[0] = p[1]
        # p[0] = Node("block", [p[1]])

    ################################
    ### GENERAL EXPRESSIONS
    ################################
    def p_expressions_in_sequence_of_commas_wrapper(self, p):
        '''
        expressions_wrapper : expressions
        '''
        # print("hmm2")
        p[0] = Node("expressions_wrapper", [p[1]])
        p[0].lineno = p.lineno(1)

    def p_expressions_in_sequence_of_commas(self, p):
        '''
        expressions : expression
                    | expression COMMA expressions
        '''
        # children = [p[1]]
        # if len(p) > 2:
        #   children.append(p[3])
        # p[0] = Node("expressions", children)
        # print("hmm3", p.stack)
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[3]

    def p_expression_len(self, p):
        '''
        expression : LEN L_PARENTHESE expressions_wrapper R_PARENTHESE
        '''
        temp = Node("id_", [], "len")
        p[0] = Node("function_call_expr", [temp, p[3]], "length_function")
        p[0].lineno = p.lineno(1)

    def p_expressions_all(self, p):
        '''
        expression : comparison_expressions
                   | arithmetic_expression
                   | function_call_expression
        '''
        # print("hmm4", p.stack)
        p[0] = p[1]
        # p[0] = Node("expression", [p[1]])

    def p_expression(self, p):
        '''
        expression :  L_PARENTHESE expression R_PARENTHESE
        '''
        p[0] = p[2]
        # p[0] = Node("expression",[p[2]])

    ################################
    ### FUNCTION CALL EXPRESSIONS
    ################################
    def p_function_call_expr_in_parantheses(self, p):
        '''
        function_call_expression : id_ L_PARENTHESE expressions_wrapper R_PARENTHESE
        '''
        p[0] = Node("function_call_expr", [p[1], p[3]])
        p[0].lineno = p.lineno(1)

    def p_function_call_no_expr(self, p):
        '''
        function_call_expression : id_ L_PARENTHESE R_PARENTHESE
        '''
        p[0] = Node("function_call_expr", [p[1]])
        p[0].lineno = p.lineno(1)

    def p_function_call_no_expr_with_dot(self, p):
        '''
        function_call_expression : id_ DOT function_call_expression
        '''
        p[0] = Node("function_call_expr", [p[1],p[3]])
        p[0].lineno = p.lineno(1)

    # def p_function_call_list_len_expr(self, p):
    #     '''
    #     function_call_expression : LEN L_PARENTHESE id_ R_PARENTHESE
    #     '''
    #     p[0] = Node("function_call_expr", [p[3]], "length_function")
    #     p[0].lineno = p.lineno(1)


    ################################
    ### COMPARISON EXPRESSIONS
    ################################


    def p_comparison_expr_top(self, p):
        '''
        comparison_expressions : comparison_expr_OR
        '''
        p[0] = p[1]

    def p_comparison_expr_OR(self,p):
        '''
        comparison_expr_OR : comparison_expr_OR OR comparison_expr_AND
                           | comparison_expr_AND
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Node("comparison_expression", [p[1], p[3]], p[2])
            p[0].lineno = p.lineno(1)

    def p_comparison_expr_AND(self, p):
        '''
        comparison_expr_AND : comparison_expr_AND AND comparison_expr_high_prec
                            | comparison_expr_high_prec
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Node("comparison_expression", [p[1], p[3]], p[2])
            p[0].lineno = p.lineno(1)

    def p_comparison_expr_high_prec(self, p):
        '''
        comparison_expr_high_prec : comparison_expr_high_prec EQUALS comparison_expr_base
                                  | comparison_expr_high_prec NOT_EQUALS comparison_expr_base
                                  | comparison_expr_high_prec LESS_THAN comparison_expr_base
                                  | comparison_expr_high_prec LESS_THAN_OR_EQ comparison_expr_base
                                  | comparison_expr_high_prec GREATER_THAN comparison_expr_base
                                  | comparison_expr_high_prec GREATER_THAN_OR_EQ comparison_expr_base
                                  | comparison_expr_base
                                  | NOT comparison_expr_base
        '''
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = Node("comparison_expression", [p[2]], p[1])
            p[0].lineno = p.lineno(1)
        else:
            p[0] = Node("comparison_expression", [p[1], p[3]], p[2])
            p[0].lineno = p.lineno(1)


    def p_comparison_expr_base(self, p):
        '''
        comparison_expr_base : all_types
             | id_
             | arithmetic_expression
             | function_call_expression
        '''
        p[0] = p[1]

    def p_comparison_expr_base_paranthesese(self, p):
        '''
        comparison_expr_base : L_PARENTHESE comparison_expressions R_PARENTHESE
        '''
        p[0] = p[2]


    def p_all_types(self, p):
        '''
        all_types : boolean_types
                  | id_
                  | integer_number
                  | float_number
                  | string_object
                  | list_object
        '''
        p[0] = p[1]
        # p[0] = Node("all_types", [p[1]])

    ################################
    ### ARITHMETIC EXPRESSIONS
    ################################

    def p_arith_expr_unary_minus(self, p):
        '''
        arithmetic_expression : MINUS arithmetic_expression %prec UNARY
        '''
        # Use Node's 'value' property to store the MINUS
        p[0] = Node("arithmetic_expression", [p[2]], p[1])
        p[0].lineno = p.lineno(1)

    def p_arith_expr_plus(self, p):
        '''arithmetic_expression : arithmetic_expression PLUS term'''
        p[0] = Node("arithmetic_expression_plus", [p[1], p[3]])
        p[0].lineno = p.lineno(1)

    def p_arith_expr_minus(self, p):
        '''arithmetic_expression : arithmetic_expression MINUS term'''
        p[0] = Node("arithmetic_expression_minus", [p[1], p[3]])
        p[0].lineno = p.lineno(1)

    def p_arith_expr_term(self, p):
        '''arithmetic_expression : term'''
        p[0] = p[1]
        # p[0] = Node("arithmetic_expression_term", [p[1]])

    def p_arith_term_multiply(self, p):
        '''term : term MULTIPLY factor'''
        p[0] = Node("term_multiply", [p[1], p[3]])
        p[0].lineno = p.lineno(1)

    def p_arith_term_div(self, p):
        '''term : term DIVIDE factor'''
        p[0] = Node("term_divide", [p[1], p[3]])
        p[0].lineno = p.lineno(1)

    def p_arith_term_factor(self, p):
        '''term : factor
                | function_call_expression
        '''
        p[0] = p[1]
        # p[0] = Node("term_factor", [p[1]])

    def p_arith_factor_num(self, p):
        '''factor : integer_number
                  | float_number
                  | id_'''
        p[0] = p[1]
        # p[0] = Node("factor_num", [p[1]])

    def p_arith_factor_expr(self, p):
        '''factor : L_PARENTHESE arithmetic_expression R_PARENTHESE'''
        p[0] = p[2]
        # p[0] = Node("factor_expr", [p[2]])

    ################################
    ### VARIABLE ASSIGNMENT
    ################################
    def p_variable_assignment(self, p):
        '''
        variable_assignment : id_ EQUAL_ASSIGN expression
        '''
        p[0] = Node("variable_assignment", [p[1], p[3]])
        p[0].lineno = p.lineno(1)

    def p_variable_operation_assignment(self, p):
        '''
        variable_assignment : id_ arithmetic_op EQUAL_ASSIGN arithmetic_expression
        '''
        p[0] = Node("variable_assignment", [p[1], p[2], p[4]])
        p[0].lineno = p.lineno(1)

    ################################
    ### LISTS
    ################################
    def p_list_object_empty(self, p):
        '''
        list_object : L_BRACKET R_BRACKET
        '''
        p[0] = Node("list_object")
        p[0].lineno = p.lineno(1)

    def p_list_filled(self, p):
        '''
        list_object : L_BRACKET types_one_or_more_in_commas R_BRACKET
                    | L_BRACKET ids_one_or_more_in_commas R_BRACKET
        '''
        p[0] = Node("list_object", [p[2]])
        p[0].lineno = p.lineno(1)

    def p_list_element(self, p):
        '''
        list_element : id_ L_BRACKET arithmetic_expression R_BRACKET
        '''
        p[0] = Node("list_element", [p[1], p[3]], p[1].value+"["+str(p[3].value)+"]")
        p[0].lineno = p.lineno(1)

    ################################
    ### TYPES IN A SEQUENCE OF COMMAS
    ################################
    def p_ids_one_or_more_in_commas_wrapper(self, p):
        '''
        ids_one_or_more_in_commas_wrapper : ids_one_or_more_in_commas
        '''
        p[0] = Node("ids_one_or_more_in_commas_wrapper", [p[1]])
        p[0].lineno = p.lineno(1)

    def p_ids_one_or_more_in_commas(self, p):
        '''
        ids_one_or_more_in_commas : id_
                                  | id_ COMMA types_one_or_more_in_commas
        '''
        # children = [p[1]]
        # if (len(p) > 2):
        #   children.append(p[3])
        # p[0] = Node("ids_one_or_more_in_commas", children)
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[3]


    def p_types_one_or_more_in_commas(self, p):
        '''
        types_one_or_more_in_commas : all_types
                                    | all_types COMMA integer_number_one_or_more_in_commas
                                    | all_types COMMA boolean_types_one_or_more_in_commas
                                    | all_types COMMA float_number_one_or_more_in_commas
                                    | all_types COMMA string_object_one_or_more_in_commas
                                    | all_types COMMA ids_one_or_more_in_commas
        '''
        # children = [p[1]]
        # if (len(p) > 2):
        #   children.append(p[3])
        # p[0] = Node("types_one_or_more_in_commas", children)
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[3]

    def p_boolean_one_or_more_in_commas(self, p):
        '''
        boolean_types_one_or_more_in_commas : boolean_types
                                            | boolean_types COMMA types_one_or_more_in_commas
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[3]

    def p_integer_one_or_more_in_commas(self, p):
        '''
        integer_number_one_or_more_in_commas : integer_number
                                             | integer_number COMMA types_one_or_more_in_commas
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[3]

    def p_float_one_or_more_in_commas(self, p):
        '''
        float_number_one_or_more_in_commas : float_number
                                           | float_number COMMA types_one_or_more_in_commas
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[3]

    def p_string_one_or_more_in_commas(self, p):
        '''
        string_object_one_or_more_in_commas : string_object
                                            | string_object COMMA types_one_or_more_in_commas
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[3]

    ################################
    ### OPERATORS
    ################################
    def p_arithmetic_op(self, p):
        '''
        arithmetic_op : PLUS
                       | MINUS
                       | MULTIPLY
                       | DIVIDE
                       | POWER
        '''
        p[0] = Node("arithmetic_op", [], p[1])
        p[0].lineno = p.lineno(1)

    def p_comparison_ops(self, p):
        '''
        comparison_ops : AND
                       | OR
                       | NOT
                       | EQUALS
                       | NOT_EQUALS
                       | LESS_THAN
                       | LESS_THAN_OR_EQ
                       | GREATER_THAN
                       | GREATER_THAN_OR_EQ

        '''
        p[0] = Node("comparison_ops",[],p[1])
        p[0].lineno = p.lineno(1)

    ################################
    ### IDS
    ################################
    def p_parser_id_only_ID(self, p):
        '''
        id_ : ID
        '''
        p[0] = Node("id_", [], p[1])
        p[0].lineno = p.lineno(1)

    def p_parser_ID_dot_ID(self, p):
        '''
        id_ : id_ DOT id_
        '''
        p[0] = Node("id_", [p[1],p[3]])
        p[0].lineno = p.lineno(1)

    def p_parser_self_ID_dot_ID(self, p):
        '''
        id_ : SELF DOT id_
        '''
        # Use Node's 'value' property to store the SELF
        p[0] = Node("_id", [p[3]], p[1])
        p[0].lineno = p.lineno(1)

    def p_parser_list_element(self, p):
        '''
        id_ : list_element
        '''
        p[0] = Node("id_", [p[1]], p[1].children[0].value)

    def p_types(self, p):
        '''
        TYPE : BOOLEAN
             | FLOAT
             | STRING
             | INT
             | LIST
        '''
        p[0] = Node("Type", [], p[1])
        p[0].lineno = p.lineno(1)


    ################################
    ### STRING
    ################################
    def p_string_object(self, p):
        '''
        string_object : STRING_LITERAL
        '''
        p[0] = Node("str", [], p[1].strip("\"\'"))
        p[0].lineno = p.lineno(1)

    ################################
    ### BOOLEAN
    ################################
    def p_boolean_type(self, p):
        '''boolean_types : TRUE
                         | FALSE'''
        p[0] = Node("bool", [], p[1])
        p[0].lineno = p.lineno(1)

    ################################
    ### NUMBERS
    ################################
    def p_float_number_dot(self, p):
        '''float_number : number DOT number'''
        strFloat = str(p[1].value) + "." + str(p[3].value)
        p[0] = Node("float", [], float(strFloat))
        p[0].lineno = p.lineno(1)

    def p_integer_number(self, p):
        '''integer_number : number'''
        p[0] = Node("int", [], p[1].value)
        p[0].lineno = p.lineno(1)

    def p_number(self, p):
        '''number : DIGIT'''
        p[0] = Node("number", [], p[1])
        p[0].lineno = p.lineno(1)


    ################################
    ### MISC
    ################################
    def p_reserved_words_statement(self, p):
        '''
        reserved_words_statement : PASS
                                 | RETURN
                                 | CONTINUE
                                 | BREAK
                                 | SELF
        '''
        p[0] = Node("reserved_words_statement", [], p[1])
        p[0].lineno = p.lineno(1)

    def p_empty(self, p):
        'empty :'
        pass

    def p_error(self, p):
        print("Syntax error at", p)

    # Build the parser
    def build(self, **kwargs):
        self.tokens = tokens
        self.lexer = IndentLexer()
        self.lexer.build()
        self.parser = yacc.yacc(module=self, **kwargs)

    # Show the prompt for user input
    def prompt(self):
        while True:
            try:
                s = input('python code > ')
            except EOFError:
                break
            if not s:
                continue
            result = self.parser.parse(s)
            print(result)

    def test(self, data):
        result = self.parser.parse(data)
        print(result)

    def parse(self, data):
        self.lexer.input(data)
        result = self.parser.parse(lexer = self.lexer)

        return result




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Takes python source code and performs lexical analysis')
    parser.add_argument('FILE', help="Input file with python source code")
    args = parser.parse_args()

    f = open(args.FILE, 'r')
    data = f.read()
    f.close()

    m = pythonParser()
    m.build()
    result = m.parse(data)

    print("======= IN PARSER AST START =======")
    visit(result)
    print("======= IN PARSER AST END =======")
