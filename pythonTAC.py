class TAC:
    def __init__(self, value, name=None):
        self.value = value
        self.name = name

class IRGen(object):
    def __init__(self):
        self.IR_lst = []
        self.register_count = 0
        self.label_count = 0

    def generate(self, node):
        if isinstance(node, list):
            for child in node:
                self.generate(child)
            return
        method = 'gen_' + node.type
        try:
            return getattr(self, method)(node)
        except AttributeError:
            if len(node.children) == 0:
                return node.value
            return self.generate(node.children[0])

    ################################
    ## Helper functions
    ################################

    def add_code(self, code):
        self.IR_lst.append(TAC(code, "code"))

    def inc_register(self):
        self.register_count += 1
        return self.register_count

    def reset_register(self):
        self.register_count = 0

    def inc_label(self):
        self.label_count += 1
        return self.label_count

    def mark_label(self, label):
        self.IR_lst.append(TAC("_L{}:".format(label), "label"))

    def print_ir(self):
        for ir in self.IR_lst:
            print(ir.value)

    def extract_for_loop_cond_start_step(self, node):
        id = node.value.value
        if len(node.children) == 1:
            start = 0
            stop = node.children[0].value
        else:
            start = node.children[0].value
            stop = node.children[1].value

        if len(node.children) == 3:
            step = str(node.children[2].value)
        else:
            step = "1"
        # print("asdfasdfasfdasfd\t",node.children[0].children[0].value, node.children[0].type, start, stop)

        if node.children[0].type == "id_":
            op = "<"
        elif node.children[0].type == "function_call_expr" and node.children[0].children[0].value == "len":
            op = "<"
            temp = node.children[0].children[0].value
            len_parameter = node.children[0].children[1].children[0][0].value
            temp += "(" + len_parameter + ")"
            stop = temp

        elif start < stop:
            op = "<"
        else:
            op = ">"


        cond = "{} {} {}".format(id, op, str(stop))
        return cond, start, step

    def gen_int(self, node):
        return str(node.value)

    def gen_str(self, node):
        return "\""+node.value+"\""

    def gen_variable_assignment(self, node):
        for child in node.children:
            if (child.type == "arithmetic_op"):
                self.handle_operator_assignment(node, child.value)
                return


        expr = self.generate(node.children[-1])
        if len(node.children[0].children) > 0 and node.children[0].children[0].type == "list_element":
            var = node.children[0].children[0].value
        else:
            var = node.children[0].value
        self.add_code("{} := {}".format(var, expr))
        self.register_count = 0

    def handle_operator_assignment(self, node, op):
        expr = self.generate(node.children[-1])
        reg = self.inc_register()
        self.add_code("{} := {} {} {}".format('_t%d' % reg, node.children[0].value, op, expr))
        self.add_code("{} := _t{}".format(node.children[0].value, reg))
        self.register_count = 0


    def gen_arithmetic_expression_plus(self, node):
        left = self.generate(node.children[0])
        right = self.generate(node.children[1])

        reg = self.inc_register()
        self.add_code("{} := {} {} {}".format('_t%d' % reg, left, "+", right))

        return '_t%d' % reg

    def gen_arithmetic_expression_minus(self, node):
        left = self.generate(node.children[0])
        right = self.generate(node.children[1])

        reg = self.inc_register()
        self.add_code("{} := {} {} {}".format('_t%d' % reg, left, "-", right))

        return '_t%d' % reg

    def gen_term_multiply(self, node):
        left = self.generate(node.children[0])
        right = self.generate(node.children[1])

        reg = self.inc_register()
        self.add_code("{} := {} {} {}".format('_t%d' % reg, left, "*", right))

        return '_t%d' % reg

    def gen_term_divide(self, node):
        left = self.generate(node.children[0])
        right = self.generate(node.children[1])

        reg = self.inc_register()
        self.add_code("{} := {} {} {}".format('_t%d' % reg, left, "/", right))

        return '_t%d' % reg

    def gen_id_(self, node):
        if len(node.children) > 0 and node.children[0].type == "list_element":
            return node.children[0].children[0].value+"["+self.generate(node.children[0].children[1])+"]"
        return node.value

    def gen_function_call_expr(self, node):

        # set the call to the lower most function call
        func_node = node
        func = func_node.children[0].value
        while len(func_node.children) > 1 and func_node.children[1].type == "function_call_expr":
            func_node = node.children[1]
            func += "." + func_node.children[0].value

        # fetch args from the expressions wrapper
        if len(func_node.children) == 1:
            args = []
        else:
            args = func_node.children[1].children[0]

        for arg in args:
            self.add_code("push %s" % self.generate(arg))

        # Once all of the parameter has been pushed, actually call the function
        self.add_code("function_call %s" % func)

        # After we're done with the function, remove the spaces reserved
        # for the arguments
        self.add_code("pop %d" % len(args))

        reg = self.inc_register()
        self.add_code("{} := ret".format('_t%d' % reg))

        return '_t%d' % reg

    def gen_if_stmnt(self, node):
        exit_branch_label = self.inc_label()
        self.handle_if_chain(node, exit_branch_label)
        self.mark_label(exit_branch_label)

    def handle_if_chain(self, node, exit_branch_label, prev_false_branch_label=None):
        if (prev_false_branch_label is not None):
            self.mark_label(prev_false_branch_label)

        if len(node.children) == 3:
            # case for if-elif with a remaining chain
            cond = self.generate(node.children[0])
            false_branch_label = self.inc_label()
            formatted_type = node.type[:-6]
            self.add_code("{} !({}) goto {}".format(formatted_type, cond, '_L%d' % false_branch_label))
            self.generate(node.children[1])
            self.add_code("goto _L%d" % exit_branch_label)
            self.handle_if_chain(node.children[2], exit_branch_label, false_branch_label)
        elif node.type != "else_stmnt":
            # case for if-elif without a remaining chain
            cond = self.generate(node.children[0])
            formatted_type = node.type[:-6]
            self.add_code("{} !({}) goto {}".format(formatted_type, cond, '_L%d' % exit_branch_label))
            self.generate(node.children[1])
        else:
            self.add_code("else")
            self.generate(node.children[0])


    def gen_while_statement(self, node):
        cond = self.generate(node.children[0])

        loop_label = self.inc_label()
        fbranch_label = self.inc_label()

        self.mark_label(loop_label)
        self.add_code("while !({}) goto {}".format(cond, '_L%d' % fbranch_label))
        self.generate(node.children[1])
        self.add_code("goto _L%d" % loop_label)
        self.mark_label(fbranch_label)

    def gen_for_statement(self, node):
        cond, start, step = self.extract_for_loop_cond_start_step(node.children[0])

        loop_label = self.inc_label()
        fbranch_label = self.inc_label()

        self.mark_label(loop_label)
        self.add_code("for !({}) goto {} start, step: {}, {}".format(cond, '_L%d' % fbranch_label, start, step))
        self.generate(node.children[1])
        self.add_code("goto _L%d" % loop_label)
        self.mark_label(fbranch_label)

    def gen_comparison_expression(self, node):
        return self.generate(node.children[0]) + node.value + self.generate(node.children[1])

    def gen_method_decl(self, node):

        skip_decl = self.inc_label()

        # We want to skip the function code until it is called
        self.add_code("goto _L%d" % skip_decl)

        # Function label
        self.mark_label(node.value)

        # Allocate room for function local variables
        self.add_code("begin_func")

        # Actually generate the main body
        if len(node.children) == 1:
            self.generate(node.children[0])
        else:
            self.generate(node.children[1])

        # Do any cleanup before jumping back
        self.add_code("end_func")

        self.mark_label(skip_decl)

    def gen_program(self, node):
        for child in node.children:
            self.generate(child)

    def gen_return_statement(self, node):
        expr = self.generate(node.children[0])
        self.add_code("return := {}".format(expr))

    def gen_reserved_words_statement(self, node):
        reserved_word = node.value
        self.add_code("{}".format(reserved_word))

    def gen_list_object(self, node):
        if node.children == []:
            return []
        s = self.generate_list_string(node.children[0])
        return "["+s+"]"

    def generate_list_string(self, nodes):
        s = ""
        for node in nodes:
            s = s+str(node.value)+", "
        return s[:len(s)-2]
