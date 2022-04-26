from pythonAST import Node

# TODO: make constants for all the strings we need to match
RETURN_TYPE_KEY = 'return'
FUNCTION_KEYWORDS = ['print', 'append', 'insert', 'pop', 'self']

# FIRST PASS - check regular function calls exist in the symbol table
def first_pass(node: Node, st_stack=None):

    if st_stack is None:
        st_stack = [dict()]

    if node is None:
        return st_stack[0]

    if isinstance(node, list):
        for child in node:
            first_pass(child, st_stack)
        return

    st = st_stack[-1]

    if node.type == "for_statement":
        if isinstance(node.children[0], Node) and isinstance(node.children[0].value, Node) \
            and isinstance(node.children[0].value.value, str):
            st[node.children[0].value.value] = 'int'


    if node.type == "function_call_expr":
        if node.children[0].value and \
            node.children[0].value in FUNCTION_KEYWORDS or \
            node.children[-1].type == "function_call_expr" or node.value == "length_function":
            pass
        elif search_st_stack(node.children[0].value, st_stack) == False:
            raise Exception("Function " + node.children[0].value + " not defined in scope")

    if new_table_scope(node.type):
        scoped_st = {}
        if (node.type == "method_decl"):
            if search_st_stack(node.value, st_stack):
                raise Exception("Function " + node.value + " has already been declared")
            if (node.data_type):
                scoped_st[RETURN_TYPE_KEY] = node.data_type.value
            else:
                scoped_st[RETURN_TYPE_KEY] = "void"
            # add functions with parameter types to scoped_st
            func_params = get_paramter_types_from_function_def(node.children[0])
            for fp in func_params:
                scoped_st[fp[0]] = fp[1]

        else:
            scoped_st[RETURN_TYPE_KEY] = node.value

        new_stack = st_stack.copy()
        new_stack.append(scoped_st)

        for child in node.children:
            first_pass(child, new_stack)
        st[node.value] = scoped_st
        return st_stack[0]


    for child in node.children:
        first_pass(child, st_stack)

    return st_stack[0]

def new_table_scope(type):
    return type == "class_decl" or "method_decl" in type

def search_st_stack(key, st_stack):
    for i in range(len(st_stack)-1, -1, -1):
        if key in st_stack[i]:
            return st_stack[i][key]

    return False

# SECOND PASS - populate variable assignments in the symbol table
def second_pass(node: Node, st_stack):
    if node is None:
        return st_stack[0]

    if isinstance(node, list):
        for child in node:
            second_pass(child, st_stack)
        return

    st = st_stack[-1]

    # Ensure only list variables can make function calls
    if node.type == "function_call_expr" and node.children[-1].type == "function_call_expr":
        id = node.children[0].value
        if "[]" not in search_st_stack(id, st_stack):
            raise Exception("Variable {} cannot make a function call".format(id))

    if node.type ==  "variable_assignment":
        var = get_var_name(node)
        type = get_expr_type(node.children[-1], st_stack)

        existing_type = search_st_stack(var, st_stack)
        if node.children[0].value in st and existing_type == None:
            # edge case, just assign it the type it got
            st[node.children[0].value] = type
            existing_type = type

        if existing_type != False and existing_type != type:
            if type in ["string", "bool"] or existing_type in ["string", "bool"]:
                raise Exception("Cannot re-assign variable with different type! Line number = " +str(node.lineno))
            elif existing_type == "int":
                type = "int"

        node.data_type = type

        st[var] = type
    else:
        new_stack = st_stack.copy()
        if new_table_scope(node.type):
            new_stack.append(st[node.value])
        for child in node.children:
            second_pass(child, new_stack)

def get_var_name(node):
    if node.type == "id_" and node.value != "self":
        return node.value

    # first child contains id of node
    return get_var_name(node.children[0])

def get_lst_type(node_list, st_stack):
    node = node_list[0]
    if node.type == "id_":
        existing_type = search_st_stack(node.value, st_stack)
        if not type:
            raise Exception("'"+node.value+"' not declared")
        return existing_type
    return "{}[]".format(node_list[0].type)

def get_expr_type(node, st_stack):
    if node is None:
        return None

    if isinstance(node, list):
        for child in node:
            type = get_expr_type(child, st_stack)
            if type != None:
                return type
        return None

    if node.type == "comparison_expression":
        return "bool"

    if node.type == "function_call_expr":
        if node.value == "length_function":
            return "int"

        if node.children[0].value and node.children[0].value == "self":
            return get_return_type(node.children[0].children[0].value, st_stack)

        return get_return_type(node.children[0].value, st_stack)

    if is_primitive(node.type):
        return node.type

    if is_arithmetic_expr(node.type):
        if has_float(node):
            return "float"
        else:
            return "int"

    if node.type == "list_object":
        if node.children == []:
            return "void"
        return get_lst_type(node.children[0], st_stack)

    if node.type == "id_":
        if len(node.children) > 0 and node.children[0].type == "list_element":
            type = search_st_stack(node.children[0].children[0].value, st_stack)[:-2]
        else:
            type = search_st_stack(node.value, st_stack)
        if not type:
            raise Exception("'"+node.value+"' not yet declared!")
        return type

    for child in node.children:
        type = get_expr_type(child, st_stack)
        if type != None:
            return type

    return None

def get_return_type(id, st_stack):
    for i in range(len(st_stack)-1, -1, -1):
        if id in st_stack[i]:
            return st_stack[i][id][RETURN_TYPE_KEY]
    return False

def is_primitive(type):
    return type in ["bool", "float", "int", "str"]

def is_arithmetic_expr(type):
    return "arithmetic" in type or "term" in type

def has_float(node: Node):
    if node is None:
        return False

    if isinstance(node, list):
        for child in node:
            if (has_float(child)):
                return True
    if node.type == "float":
        return True
    else:
        for child in node.children:
            if(has_float(child)):
                return True

# return list of (paramter-names, types) for a function
def get_paramter_types_from_function_def(node: Node):
    if isinstance(node, list):
        for child in node:
            ret = get_paramter_types_from_function_def(child)
            if (ret != []):
                return ret
        return []

    if node.type == "ids_one_or_more_in_commas_with_types_wrapper":
        params_and_types_children = node.children[0]
        counter = 0
        pair = []
        params_and_types_to_return = []
        for param_or_type in params_and_types_children:
            if counter % 2 == 0:
                if pair != []:
                    params_and_types_to_return.append(pair)
                pair = []
                pair.append(param_or_type.value)
            else:
                pair.append(param_or_type.value)

            counter+=1

        if pair not in params_and_types_to_return:
            params_and_types_to_return.append(pair)

        return params_and_types_to_return

    return []
