import re
from pythonTAC import TAC 
from pythonST import search_st_stack

class ConstantFolding(object):

    TEMP_ASSIGN = r"_t(?P<temp_var>[\d]+) := (?P<expr>.*)"
    TEMP_VAR = r"_t([\d]+)"
    VAR_ASSIGN = r"(?P<var>[a-zA-Z_][a-zA-Z_0-9]*) := (?P<expr>.*)"
    ARITHMETIC_EXPR = r"(?P<expr_1>.*) (?P<op>[+\-\/*]) (?P<expr_2>.*)"
    FLOAT = r"(^[0-9]+\.[0-9]+$)"
    INT = r"([0-9]+$)"
    OPERATOR = r"\+|-|\/|\*"

    vars = {}
    new_IR_lst = []

    def __init__(self, IR_lst, st):
        self.IR_lst = IR_lst
        self.st = st

    def do_constant_folding(self):
        for line in self.IR_lst:
            self.ir_matcher(line)
        
        return self.new_IR_lst

    def check_match(self, pattern, str):
        return re.match(pattern, str) is not None

    def ir_matcher(self, line):
        if (self.check_match(self.TEMP_ASSIGN, line.value)):
            self.temp_assign(line)
            self.new_IR_lst.append(line)
        elif (self.check_match(self.VAR_ASSIGN, line.value)):
           self.var_assign(line)
        else:
            self.new_IR_lst.append(line)
    
    def var_assign(self, line):
        new_line = line
        groups = re.match(self.VAR_ASSIGN, line.value)
        var = groups.group("var")
        expr = groups.group("expr")
        if expr in self.vars:
            val = self.vars[expr]
            del self.vars[expr]
            var_type = search_st_stack(var, [self.st])
            val = self.convert_to_num_type(val, var_type)
            new_line = TAC("{} := {}".format(var, val), line.name)
        self.vars[var] = expr        
        self.new_IR_lst.append(new_line)

    def temp_assign(self, line):
        groups = re.match(self.TEMP_ASSIGN, line.value)
        var = "_t" + groups.group("temp_var")
        expr = groups.group("expr")

        if self.check_match(self.FLOAT, expr):
            self.vars[var] = float(expr)
            return

        if self.check_match(self.INT, expr):
            self.vars[var] = int(expr)
            return

        if not self.check_match(self.ARITHMETIC_EXPR, expr):
            return
        
        groups = re.match(self.ARITHMETIC_EXPR, expr)
        expr_1 = groups.group("expr_1")
        op = groups.group("op")
        expr_2 = groups.group("expr_2")

        if not (not search_st_stack(expr_1, [self.st]) and not search_st_stack(expr_2, [self.st])):
            self.vars[var] = "({})".format(expr)
            return

        if expr_1 in self.vars:
            key = expr_1
            expr_1 = self.vars[expr_1]
            del self.vars[key]
        if expr_2 in self.vars:
            key = expr_2
            expr_2 = self.vars[expr_2]
            del self.vars[key]

        can_compute = True
        ops = ["+", "/", "-", "*"]
        full_expr = "{} {} {}".format(expr_1,op, expr_2)
        op_count = 0
        for op_type in ops:
            op_count += full_expr.count(op_type)
        
        if op_count > 1:
            can_compute = False

        expr_1 = self.convert_to_num_type(expr_1)
        if type(expr_1) != float and type(expr_1) != int:
            can_compute = False
    
        expr_2 = self.convert_to_num_type(expr_2)
        if type(expr_2) != float and type(expr_2) != int:
            can_compute = False
        
        if can_compute:
            if op == "+":
                self.vars[var] = expr_1 + expr_2
            elif op == "-":
                self.vars[var] = expr_1 - expr_2
            elif op == "*":
                self.vars[var] = expr_1 * expr_2
            else:
                self.vars[var] = expr_1 / expr_2
        else:
            self.vars[var] = "({} {} {})".format(expr_1, op, expr_2)

    def convert_to_num_type(self, num, type = "float"):
        final_num = num
        if type == "int":
            try:
                final_num = int(num)
            except:
                pass
        else:
            try:
                final_num = float(num)
            except:
                pass
        
        return final_num
