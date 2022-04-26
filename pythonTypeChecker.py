from pythonAST import Node
from pythonST import is_primitive
from pythonST import is_arithmetic_expr
from pythonST import search_st_stack
from pythonST import has_float


class TypeChecker(object):

    def typecheck(self, node, st=None):
        if node is None:
            return ""

        if isinstance(node, list):
            combined = ""
            for child in node:
                self.typecheck(child, st)

            return combined

        method = 'check_' + node.type
        if node.type == "class_decl" or node.type == "method_decl":
            # combine the st for the class with the global st
            st = compress_symbol_table(node, st, node.value)
        return getattr(self, method, self.generic_typecheck)(node, st)

    def check_program(self, node, st=None):
        combined = ""
        for child in node.children[0]:
            self.typecheck(child, st)

        return combined

    def generic_typecheck(self, node, st=None):
        return "generic_typecheck"

    def check_return_statement(self, node, st=None):
        if (not 'return' in st) or (st['return'] == 'void'):
            raise Exception("void function is returning, or not a function:: line number = ", node.lineno)

        # check if return statement's type matches function type
        if is_primitive(node.children[0].type):
            if node.children[0].type == st['return']:
                return node.type
            else:
                raise Exception("mismatching return type, function returns:"+st['return']+
                                " and method returns: "+node.children[0].type +":: line number = ", node.lineno)
        elif node.children[0].type == "id_":
            if node.children[0].value in st:
                if len(node.children[0].children) > 0 and node.children[0].children[0].type == "list_element":
                    return node.type[0:-2]
                if st[node.children[0].value] == st['return']:
                    return node.type
                else:
                    raise Exception("mismatching return type, function returns:"+st['return']+
                                    " and method returns: "+st[node.children[0].value] + ":: line number = ", node.lineno)
            else:
                Exception(node.children[0].value + " is not in the symbol table:: line number = ", node.lineno)

        elif is_arithmetic_expr(node.children[0].type):
            if has_float(node.children[0]):
                # is float
                if st['return'] == 'float':
                    return node.type
                else:
                    raise Exception("mismatching return type, function returns:"+st['return']+
                                    " and method returns: float:: line number = ", node.lineno)
            else:
                if st['return'] == 'int':
                    return node.type
                else:
                    raise Exception("mismatching return type, function returns:"+st['return']+
                                    " and method returns: int:: line number = ", node.lineno)
                # is int
        elif node.children[0].type == "comparison_expression":
            if check_comparison_expr_types(node.children[0], st):
                # is bool
                if st['return'] == 'bool':
                    return node.type
                else:
                    raise Exception("mismatching return type, function returns:"+st['return']+
                                    " and method returns: bool:: line number = ", node.lineno)
            else:
                raise Exception("return type is bool, but return object isn't:: line number = ", node.lineno)
        elif node.children[0].type == "function_call_expr":
            to_search = node.children[0].children[0].value
            if node.children[0].children[0].value == "self":
                # look for node.children[0].children[0].value in st
                to_search = node.children[0].children[0].children[0].value

            if to_search in st:
                if isinstance(st[to_search], str) and st[to_search] != st['return']:
                    raise Exception("mismatching return type, function returns:"+st['return']+
                                    " and method returns: "+st[to_search] +" :: line number = ", node.lineno)
                elif isinstance(st[to_search], dict) and st[to_search]['return'] != st['return']:
                    raise Exception("mismatching return type, function returns:"+st['return']+
                                    " and method returns: "+ st[to_search]['return']+" :: line number = ", node.lineno)
                else:
                    raise Exception("mismatching return type, function returns:"+st['return']+
                                    " and method does not "+" :: line number = ", node.lineno)
            else:
                raise Exception(to_search + " is not in the symbol table"+" :: line number = ", node.lineno)


        return node.type


    def check_method_decl(self, node, st=None):
        if node is None:
            return ""

        combined = ""
        for child in node.children:
            self.typecheck(child, st)

        return combined

    def check_class_decl(self, node, st=None):
        if node is None:
            return ""

        combined = ""
        # changed this from node.children[0] to node.children
        for child in node.children:
            self.typecheck(child, st)

        return combined


    def check_while_statement(self, node, st=None):
        if not check_comparison_expr_types(node.children[0], st):
            raise Exception("invalid condition in while loop"+" :: line number = ", node.lineno)

        for child in node.children[1]:
            self.typecheck(child, st)

        return node.type

    def check_comparison_expression(self, node, st=None):
        if check_comparison_expr_types(node, st):
            return node.type
        raise Exception("invalid comparison expression"+" :: line number = ", node.lineno)

    def check_arithmetic_expression_plus(self, node, st=None):
        if check_arithmetic_expr_type(node, st):
            return node.type
        raise Exception("invalid arithmetic expression"+" :: line number = ", node.lineno)

    def check_arithmetic_expression_minus(self, node, st=None):
        if check_arithmetic_expr_type(node, st):
            return node.type
        raise Exception("invalid arithmetic expression"+" :: line number = ", node.lineno)

    def check_term_multiply(self, node, st=None):
        if check_arithmetic_expr_type(node, st):
            return node.type
        raise Exception("invalid arithmetic expression"+" :: line number = ", node.lineno)

    def check_term_divide(self, node, st=None):
        if check_arithmetic_expr_type(node, st):
            return node.type
        raise Exception("invalid arithmetic expression"+" :: line number = ", node.lineno)


    def check_if_stmnt(self, node, st=None):
        # if not check_comparison_expr_types(node.children[0], st):
        #     raise Exception("invalid condition in if statement")

        for child in node.children:
            self.typecheck(child, st)
        return node.type

    def check_elif_stmnt(self, node, st=None):
        # if not check_comparison_expr_types(node.children[0], st):
        #     raise Exception("invalid condition in if statement")

        for child in node.children:
            self.typecheck(child, st)
        return node.type

    def check_else_stmnt(self, node, st=None):
        # if not check_comparison_expr_types(node.children[0], st):
        #     raise Exception("invalid condition in if statement")

        for child in node.children:
            self.typecheck(child, st)
        return node.type

    def check_for_statement(self, node, st=None):
        # check to see if every thing in for-loop params is an int
        for param_node in node.children[0].children:
            if param_node.type == 'int':
                continue
            elif param_node.type == 'function_call_expr' and param_node.children[0].value == "len" :
                continue
            elif param_node.type == "id_":
                if param_node.value in st:
                    if st[param_node.value] == 'int' or st[param_node.value] == 'float':
                        continue
                    else:
                        raise Exception("invalid parameter in for statement"+" :: line number = ", node.lineno)
                else:
                    raise Exception("invalid parameter in for statement"+" :: line number = ", node.lineno)
            else:
                raise Exception("invalid parameter in for statement"+" :: line number = ", node.lineno)

        for child in node.children[1]:
            self.typecheck(child, st)
        return node.type



    def check_variable_assignment(self, node, st=None):

        # variable assignement has 2 children
        # variable = object

        if node.children[0].type == "id_" and is_primitive(node.children[1].type):
            if node.data_type == node.children[-1].type or \
                node.data_type == "int" and node.children[-1].type == "float":
                return node.type
            else:
                raise Exception("variable " +node.children[0].value +" type is "+
                                node.data_type+ " but assignment type is "+ node.children[1].type+" :: line number = ", node.lineno)
        elif node.children[0].type == "id_" and is_arithmetic_expr(node.children[1].type):
            if check_arithmetic_expr_type(node.children[1], st):
                return node.type
            else:
                raise Exception("variable " +node.children[0].value +
                        " is an arithemetic expression type but the assignment is not an arithemetic expression"+" :: line number = ", node.lineno)
        elif node.children[0].type == "id_" and node.children[1].type == "comparison_expression":
            if check_comparison_expr_types(node.children[1], st):
                return node.type
            else:
                raise Exception("variable " +node.children[0].value +
                        " is an comparison expression type but the assignment is not a comparison expression"+" :: line number = ", node.lineno)
        elif node.children[1].type == "list_object":
            return self.check_list_object(node.children[1], st)
        return node.type

    def check_list_object(self, node, st=None):
        if node.children == []:
            return node.type
        else:
            type = node.children[0][0].type
            id_val = node.children[0][0].value
            if type == "id_":
                if id_val not in st:
                    raise Exception("id '"+id_val+"' not declared")
                type = st[id_val]
            if check_list(node.children, st, type):
                return node.type
            else:
                raise Exception("list object consists of more than one type :: line number =", node.lineno)

def check_list(node, st, type):
    if isinstance(node, list):
        for child in node:
            ret = check_list(child, st, type)
            if ret == False:
                return False
        return True

    if node.type == "id_":
        if node.value not in st:
            raise Exception("id '"+str(node.value)+"' not declared")
        if st[node.value] != type:
            raise Exception("id '"+str(node.value)+"' is of type "+st[node.value]+" and not of list's type "+ type)
    else:
        if node.type != type:
            raise Exception("'"+str(node.value)+"' is of type "+node.type+" and not of list's type "+ type)
        for child in node.children:
            ret = check_list(child, st, type)
            if ret == False:
                return False
        return True


def compress_symbol_table(node, st, class_or_mthd):
    # for a given class or method combine global st with its
    if 'return' in st:
        if st['return'] == class_or_mthd:
            return st

    if class_or_mthd not in st:
        raise Exception("Error: " + class_or_mthd + " is not defined"+" :: line number = ", node.lineno)

    st_to_return = {}
    for k,v in st[class_or_mthd].items():
        st_to_return[k] = v

    for k,v in st.items():
        if k not in st_to_return:
            if isinstance(v, dict):
                st_to_return[k] = v['return']
            else:
                st_to_return[k] = v

    return st_to_return


def check_comparison_expr_types(node, st):
    # TODO do something here
    # can only compare same types
    # really no typechecking in comparison expressions
    return True



def check_arithmetic_expr_type(node, st):

    if len(node.children) == 0:
        return True

    if node.children[0].type == "id_":
        # check st for its type
        cur_node = node.children[0]
        if len(cur_node.children) > 0 and cur_node.children[0].type == "list_element":
            if cur_node.children[0].children[0].value in st and \
                st[cur_node.children[0].children[0].value] == "int" or "float":
                pass
            else:
                return False
        elif node.children[0].value in st:
            if st[node.children[0].value] == "int" or st[node.children[0].value] == "float":
                pass
            else:
                return False
        else:
            Exception(node.children[0].value + " is not in the symbol table"+" :: line number = ", node.lineno)
            return False

    elif is_arithmetic_expr(node.children[0].type):
        if check_arithmetic_expr_type(node.children[0], st):
            pass
        else:
            return False
    elif is_primitive(node.children[0].type):
        if node.children[0].type == "int" or node.children[0].type == "float":
            pass
        else:
            return False
    elif node.children[0].type == "function_call_expr":
        # function call
        to_search = node.children[0].children[0].value
        if node.children[0].children[0].value == "self":
            # look for node.children[0].children[0].value in st
            to_search = node.children[0].children[0].children[0].value

        if to_search in st:
            if isinstance(st[to_search], str) and st[to_search] == 'int' or st[to_search] == 'float':
                pass
            elif isinstance(st[to_search], dict) and st[to_search]['return'] == 'int' or st[to_search]['return'] == 'float':
                pass
            else:
                return False
        else:
            raise Exception(to_search + " is not in the symbol table"+" :: line number = ", node.lineno)
            return False

    if len(node.children) == 1:
        return True
    # print("------------HERE_------------------")

    if node.children[1].type == "id_":
        cur_node = node.children[1]
        if len(cur_node.children) > 0 and cur_node.children[0].type == "list_element":
            if cur_node.children[0].children[0].value in st and \
                st[cur_node.children[0].children[0].value] == "int" or "float":
                pass
            else:
                return False
        # check st for its type
        elif node.children[1].value in st:
            if st[node.children[1].value] == "int" or st[node.children[1].value] == "float":
                pass
            else:
                return False
        else:
            raise Exception(node.children[1].value + " is not in the symbol table"+" :: line number = ", node.lineno)
            return False

    elif is_arithmetic_expr(node.children[1].type):
        if check_arithmetic_expr_type(node.children[1], st):
            pass
        else:
            return False
    elif is_primitive(node.children[1].type):
        if node.children[1].type == "int" or node.children[1].type == "float":
            pass
        else:
            return False
    elif node.children[1].type == "function_call_expr":
        # function call
        to_search = node.children[1].children[0].value
        if node.children[1].value == "self":
            # look for node.children[0].children[0].value in st
            to_search = node.children[1].children[0].value

        if to_search in st:
            if isinstance(st[to_search], str) and st[to_search] == 'int' or st[to_search] == 'float':
                pass
            elif isinstance(st[to_search], dict) and st[to_search]['return'] == 'int' or st[to_search]['return'] == 'float':
                pass
            else:
                return False
        else:
            raise Exception(to_search + " is not in the symbol table :: line number = ", node.lineno)
            return False


    return True
