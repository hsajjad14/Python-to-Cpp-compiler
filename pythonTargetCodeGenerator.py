import re
from pythonST import search_st_stack

# compiles into C++ code
class TargetCodeGenerator(object):

    # list to store the cpp code
    cpp_code = []
    IR_lst = []
    symbol_table = {}
    temp_vars = {}
    main_pointer = 0
    global_pointer = 0
    last_label_name = ""
    tabs = 0
    labels_set = []
    function_call_variables = []

    # list of regex tokens to match tacs from the IR list
    TEMP_ASSIGN = r"_t(?P<temp_var>[\d]+) := (?P<expr>.*)"
    TEMP_REGISTER = r"^_t(?P<temp_var>[\d]+)$"
    VAR_ASSIGN = r"(?P<var>[a-zA-Z_][a-zA-Z_0-9]*)((?P<idx>\[[a-zA-Z_]*[a-zA-Z_0-9]*\]))? := (?P<value>.*)"
    LABEL      = r"_L(?P<label_name>[a-zA-Z_][a-zA-Z_0-9]*):"
    LABEL_IF_WHILE_FOR_STMNT = r"_L(?P<label_number>[0-9]*):"
    LIST_ELEMENT = r"(?P<id>[a-zA-Z_][a-zA-Z_0-9]*)\[(?P<expr>.*)]"

    IF_STMNT = r"if (?P<cond>.*) goto _L(?P<label>.*)"
    ELIF_STMNT = r"elif (?P<cond>.*) goto _L(?P<label>.*)"
    ELSE = r"else"
    GOTO = r"goto _L(?P<label>.*)"

    RETURN_STMNT = r"return := (?P<expr>.*)"

    FUNCTION_CALL_STMNT = r"function_call (?P<function>.*)"
    PUSH = r"push (?P<parameter>.*)"
    POP = r"pop (?P<number>[0-9]*)"

    WHILE = r"while (?P<cond>.*) goto _L(?P<label>.*)"
    FOR_LOOP = r"for !\((?P<var>[a-zA-Z_][a-zA-Z_0-9]*) (?P<op>[<|>]) (?P<end>.+)\) goto _L(?P<label>\d+) start, step: (?P<start>\d+), (?P<step>\d+)"

    ARITHMETIC_EXPR = r"(?P<expr_1>.*) (?P<op>[+\-\/*]) (?P<expr_2>.*)"
    NUM_TYPE = r"(^[0-9]+\.[0-9]+$)|([0-9]+$)"

    COMPARISON_EXPR = r"(?P<expr_1>.*)(?P<op>(or|and|>=|<=|>|<|==|!=))(?P<expr_2>.*)"
    BOOL = r"True|False"

    LIST = r"\[(?P<elements>.*)\]"

    METHOD_DECL = r"begin_func"
    METHOD_END  = r"end_func"
    RESERVED_WORDS = r"(?P<reserved_word>pass|continue|break)"
    did_method_end = False

    bool_op_map = {
		'or': '||',
        'and': '&&',
        'True': 'true',
        'False': 'false'
	}

    current_IR_line = 0

    headers = []

    def __init__(self, IR_lst, st, AST):

        self.current_IR_line = 0

        self.tabs = 1
        self.IR_lst = IR_lst
        self.symbol_table = st
        self.st_stack = [st]
        self.AST = AST
        self.main_tabs = 1
        self.var_dict = {}
        self.var_dict_stack = [self.var_dict]

        self.function_call_variables = []

        headers = [
            "#include <stdio.h>",
            "#include <iostream>",
            "#include <string>",
            "#include <vector>",
            "using namespace std;"
        ]

        # ALL THE CODE IN PYTHON GLOBAL LEVEL GOES AFTER main_function_init
        # AND BEFORE main_function_return
        main_function_init = "int main() {"
        main_function_return = "\t"*self.tabs+"return 0;"
        main_function_close = "}"

        for header in headers:
            self.cpp_code.append(header)
        self.cpp_code.append("")
        self.cpp_code.append(main_function_init)
        self.cpp_code.append(main_function_return)
        self.cpp_code.append(main_function_close)

        self.main_pointer = len(headers) + 2
        self.global_pointer = len(headers) + 1
        self.generating_function = False


    def printTargetCode(self):
        print("\n\n---")
        for line in self.cpp_code:
            print(line)

    def generate(self):
        for line in self.IR_lst:
            self.ir_matcher(line)
            self.current_IR_line+=1

    def update_cpp_code(self, line):
        pointer = self.global_pointer if self.generating_function else self.main_pointer
        self.cpp_code.insert(pointer,"\t"*self.tabs + line)

        if self.generating_function:
            self.global_pointer += 1
            self.main_pointer += 1
        else:
            self.main_pointer += 1

    def ir_matcher(self, line):
        if (self.check_match(self.TEMP_ASSIGN, line.value)):
            return self.temp_assign(line.value)
        elif (self.check_match(self.VAR_ASSIGN, line.value) and
                not self.check_match(self.RETURN_STMNT, line.value)):
            return self.var_assign(line.value)
        elif (self.check_match(self.IF_STMNT, line.value)):
            return self.if_stmnt(line.value, True)
        elif(self.check_match(self.LABEL, line.value)):
            return self.label(line.value)
        elif(self.check_match(self.LABEL_IF_WHILE_FOR_STMNT, line.value)):
            return self.label_end(line.value)
        elif(self.check_match(self.ELIF_STMNT, line.value)):
            return self.if_stmnt(line.value, False)
        elif(self.check_match(self.ELSE, line.value)):
            return self.else_stmnt(line.value)
        elif(self.check_match(self.WHILE, line.value)):
            return self.while_stmnt(line.value)
        elif(self.check_match(self.GOTO, line.value)):
            return self.goto_end_label(line.value)
        elif(self.check_match(self.METHOD_DECL, line.value)):
            return self.method_decl(line.value)
        elif(self.check_match(self.METHOD_END, line.value)):
            return self.method_decl_end(line.value)
        elif(self.check_match(self.RETURN_STMNT, line.value)):
            return self.return_stmnt(line.value)
        elif(self.check_match(self.FOR_LOOP, line.value)):
            return self.for_loop(line.value)
        elif(self.check_match(self.FUNCTION_CALL_STMNT, line.value)):
            return self.function_call_stmnt(line.value)
        elif(self.check_match(self.PUSH, line.value)):
            return self.push_parameter(line.value)
        elif(self.check_match(self.POP, line.value)):
            return self.pop_function_call(line.value)
        elif(self.check_match(self.RESERVED_WORDS, line.value)):
            return self.reserved_words(line.value)

    def check_match(self, pattern, str):
        return re.match(pattern, str) is not None

    def var_assign(self, str):
        groups = re.match(self.VAR_ASSIGN, str)
        var = groups.group("var")
        value = groups.group("value")
        list_idx = groups.group("idx")
        is_list = False

        if (self.check_match(self.LIST, value)):
            value = self.list(value)
            is_list = True
        else:
            value = self.expr(value)

        type = search_st_stack(var, self.st_stack).strip("\[\]")
        # print(self.var_dict_stack)
        if search_st_stack(var, self.var_dict_stack):
            if list_idx is not None:
                var = var + list_idx
            self.update_cpp_code( "{} = {};".format(var, value))
        else:
            if is_list:
                self.update_cpp_code( "vector<{}> {}{};".format(type, var, value))
                self.var_dict_stack[-1][var] = type
            else:
                type_to_write = type
                if type == "str":
                    type_to_write = "string"
                self.update_cpp_code( "{} {} = {};".format(type_to_write, var, value))
                self.var_dict_stack[-1][var] = type
        self.did_method_end = False

    def temp_assign(self, str):
        groups = re.match(self.TEMP_ASSIGN, str)
        label = "_t" + groups.group("temp_var")

        # print("do we get here?")

        var_assign = groups.group("expr")
        # print("hmm", var_assign)
        if var_assign == "ret" and "ret" in self.temp_vars:
            expr = self.temp_vars[var_assign]
            self.temp_vars[label] = expr

            # print("HHHAAAA", expr)

            # look ahead to see if the next line is _tn being assigned to a variable
            # if not it is a lone function call
            isLoneFuncCall = False
            if self.current_IR_line < len(self.IR_lst) - 1:
                next_line = self.IR_lst[self.current_IR_line+1]

                check_for_list_funcs = expr.split(".")
                # print("ASDSD", check_for_list_funcs[1][:len("push_back")])

                if (not self.check_match(self.VAR_ASSIGN, next_line.value)) \
                    or (len(check_for_list_funcs) > 1 and check_for_list_funcs[1][:len("push_back")] == "push_back") \
                    or (len(check_for_list_funcs) > 1 and check_for_list_funcs[1][:len("insert")] == "insert"):
                    isLoneFuncCall = True


            else:
                # there is no next line so it is a lone function call
                isLoneFuncCall = True


            if isLoneFuncCall:
                func_call_to_write = ""

                # check if its a print
                print_list_check = expr.split("(")
                if print_list_check[0] == "print":
                    index_of_last_parenthese = -1

                    to_print = ""

                    for i in range(len(expr[1]), -1, -1):
                        if expr[i] == ")":
                            index_of_last_parenthese = i
                            break

                    temp = expr[len("print")+1:index_of_last_parenthese]
                    if temp != "\"" and temp != '\'':
                        temp = self.expr(temp)
                    to_print = temp

                    # replace with cout
                    func_call_to_write = "cout << " + to_print + " << endl;"

                else:
                    func_call_to_write = expr+";"

                self.update_cpp_code(func_call_to_write)



        else:
            self.temp_vars[label] = groups.group("expr")

    def expr(self,str):
        expr = self.arithmetic_expr(str)
        if expr is not "":
            return expr

        expr = self.comparison_expr(str)
        if expr is not "":
            return expr

        expr = self.list_element(str)
        if expr is not "":
            return expr

        if (self.check_match(self.TEMP_REGISTER, str)):
            return self.expr(self.temp_vars[str])

        # str is a variable if it reaches this line
        return str

    def arithmetic_expr(self, str):
        if (self.check_match(self.ARITHMETIC_EXPR, str)):
            groups = re.match(self.ARITHMETIC_EXPR, str)
            expr_1 = self.expr(groups.group("expr_1"))
            op = groups.group("op")
            expr_2 = self.expr(groups.group("expr_2"))
            return "({} {} {})".format(expr_1,op,expr_2)
        elif (self.check_match(self.NUM_TYPE, str)):
            return str
        else:
            return ""

    def comparison_expr(self, str):
        if (self.check_match(self.COMPARISON_EXPR, str)):
            groups = re.match(self.COMPARISON_EXPR, str)
            expr_1 = self.expr(groups.group("expr_1"))

            op = groups.group("op")
            if op in self.bool_op_map:
                op = self.bool_op_map[op]

            expr_2 = self.expr(groups.group("expr_2"))
            return "({} {} {})".format(expr_1,op,expr_2)
        elif (self.check_match(self.BOOL, str)):
            return self.bool_op_map[str]
        else:
            return ""

    def list_element(self, str):
        if (self.check_match(self.LIST_ELEMENT, str)):
            groups = re.match(self.LIST_ELEMENT, str)
            list_id = groups.group("id")
            expr = self.expr(groups.group("expr"))
            return "{}[{}]".format(list_id, expr)
        return ""

    def label(self, str):
        groups = re.match(self.LABEL, str)
        self.last_label_name = groups.group("label_name")

        self.did_method_end = False

    def label_end(self, str):
        groups = re.match(self.LABEL_IF_WHILE_FOR_STMNT, str)

        label = groups.group("label_number")
        if label not in self.labels_set:
            self.labels_set.append(label)
        elif self.did_method_end == False:
            self.tabs -= 1
            self.update_cpp_code("}")

        self.did_method_end = False


    def goto_end_label(self, str):
        groups = re.match(self.GOTO, str)
        label = groups.group("label")
        if label not in self.labels_set:
            self.labels_set.append(label)
        self.did_method_end = False

    def fetch_params(self, node, func_name, last_seen_func_name):

        if isinstance(node, list):
            for child in node:
                params = self.fetch_params(child, func_name, last_seen_func_name)
                if params != "":
                    return params
            return ""

        if node.type == "method_decl":
            last_seen_func_name = node.value
        elif node.type == "ids_one_or_more_in_commas_with_types_wrapper" and last_seen_func_name == func_name:
            params = ""
            for i in range(0, len(node.children[0]), 2):
                param = node.children[0][i].value
                type = node.children[0][i+1].value
                if type == "str": type = "string"
                params = params + type  + " " + param + ", "
            params = params[0:len(params)-2]
            return params

        for child in node.children:
                params = self.fetch_params(child, func_name, last_seen_func_name)
                if params != "":
                    return params

        return ""

    def method_decl(self, str):
        self.generating_function = True
        self.main_tabs = self.tabs
        self.tabs = 0
        func_name = self.last_label_name
        ret_type  = self.st_stack[-1][func_name]["return"]


        self.st_stack.append(self.st_stack[-1][func_name])
        self.var_dict_stack[-1][func_name] = {}
        self.var_dict_stack.append(self.var_dict_stack[-1][func_name])

        params = self.fetch_params(self.AST, func_name, "")
        function_def = ret_type + " " + func_name + "(" + params + ") {"
        self.update_cpp_code(function_def)
        self.tabs += 1

    def method_decl_end(self, str):
        self.tabs -= 1
        self.update_cpp_code("}")
        self.st_stack.pop()
        self.var_dict_stack.pop()
        self.generating_function = False
        self.tabs = self.main_tabs
        self.did_method_end = True

    def if_stmnt(self, str, is_ifstmnt):
        pattern = self.IF_STMNT
        if is_ifstmnt == False:
            # is elif
            pattern = self.ELIF_STMNT

        groups = re.match(pattern, str)
        types = ["cond", "label"]
        label = groups.group(types[1])
        if label not in self.labels_set:
            self.labels_set.append(label)

        # get condition
        condition = groups.group(types[0])[2:-1]
        converted_comparison = self.expr(condition)
        line = "if (" + converted_comparison + ") {"
        if is_ifstmnt == False:
            line = "else if (" + converted_comparison + ") {"
        self.update_cpp_code(line)
        self.tabs += 1
        self.did_method_end = False

    def else_stmnt(self, str):
        line = "else {"
        self.update_cpp_code(line)
        self.tabs += 1
        self.did_method_end = False

    def while_stmnt(self, str):
        groups = re.match(self.WHILE, str)
        types = ["cond", "label"]

        label = groups.group(types[1])
        if label not in self.labels_set:
            self.labels_set.append(label)

        condition = groups.group(types[0])[2:-1]
        converted_comparison = self.expr(condition)

        line = "while (" + converted_comparison + ") {"
        self.update_cpp_code(line)
        self.tabs += 1
        self.did_method_end = False

    def return_stmnt(self, str):
        groups = re.match(self.RETURN_STMNT, str)
        to_return = groups.group("expr")

        if to_return[0] != "\"" and to_return[0] != '\'':
            # check if it's a string
            to_return = self.expr(to_return)

        line = "return "+to_return+";"
        self.update_cpp_code(line)
        self.did_method_end = False

    def for_loop(self, str):
        groups = re.match(self.FOR_LOOP, str)
        start = groups.group("start")
        end = groups.group("end")
        step = groups.group("step")
        op = groups.group("op")
        label = groups.group("label")
        var = groups.group("var")

        end_list = end.split("(")
        if end_list[0] == "len":
            params = end_list[1].split(")")[0]
            end = params + ".size()"

        var_type = search_st_stack(var, self.var_dict_stack)
        if not var_type:
            var_type = "int "
            self.var_dict_stack[-1][var] = "int"
        else:
            var_type = ""

        step_type = "+="
        if (op == ">"):
            step_type = "-="

        first_for_line = "for ({}{} = {}; {} {} {}; {} {} {})".format(var_type, var, start, var, op, end, var, step_type, step)
        self.update_cpp_code(first_for_line + " {")

        if label not in self.labels_set:
            self.labels_set.append(label)

        self.tabs += 1
        self.did_method_end = False


    def function_call_stmnt(self, str):
        groups = re.match(self.FUNCTION_CALL_STMNT, str)

        function_call_name = groups.group("function")
        to_store_in_ret = ""
        # print("\t",function_call_name)

        if function_call_name == "len":
            pass
        elif "." in function_call_name:
            func_segments = function_call_name.split(".")
            id = func_segments[0]
            func = func_segments[1]
            # print("\tAAAAAAAAAAAAAAAAA", func)
            if func == "append":
                function_call_name = "{}.{}".format(id, "push_back")
            elif func == "pop":
                func = "back"
                self.update_cpp_code("{}.{}();".format(id, "back"))
                self.update_cpp_code("{}.{}();".format(id, "pop_back"))
                return

        if len(self.function_call_variables) == 0:
            # no parameters for call
            to_store_in_ret = function_call_name+"()"
        elif function_call_name == "len":
            function_call_name = "size()"
            vector = self.function_call_variables[0]
            to_store_in_ret = vector + "." + function_call_name

        else:
            param_list = ""
            for p in range(len(self.function_call_variables)-1):
                param_list += self.function_call_variables[p] + ","
            param_list+=self.function_call_variables[-1]

            to_store_in_ret = function_call_name + "(" + param_list+ ")"

        key = "ret"
        self.temp_vars[key] = to_store_in_ret
        self.did_method_end = False

    def push_parameter(self, str):
        groups = re.match(self.PUSH, str)
        parameter = groups.group("parameter")

        expr = self.expr(parameter)

        self.function_call_variables.append(expr)

        self.did_method_end = False

    def pop_function_call(self, str):
        self.function_call_variables = []
        self.did_method_end = False

    def reserved_words(self, str):
        groups = re.match(self.RESERVED_WORDS, str)
        reserved_word = groups.group("reserved_word")
        if reserved_word == "pass":
            self.update_cpp_code(";")
        else:
            self.update_cpp_code("{};".format(reserved_word))

        self.did_method_end = False

    def list(self, str):
        groups = re.match(self.LIST, str)
        elements = groups.group("elements").split(",")
        cpp_list_str = "{"
        for element in elements:
            cpp_list_str += " " + element.strip() + ","
        cpp_list_str += " }"
        return cpp_list_str
