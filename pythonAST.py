#!/usr/bin/env python3

class Node:
    def __init__(self,type, children=None, value=None, data_type=None, lineno=-1):
        self.type = type
        self.data_type = data_type
        self.value = value
        self.lineno = lineno
        if children:
            self.children = children
        else:
            self.children = []

def visit(node, offset=0):
    if isinstance(node, list):
      for child in node:
        visit(child, offset)
      return

    if node is None:
        return

    line_start = offset*"\t" + node.type + ":"
    data_type = ""
    if node.data_type and isinstance(node.data_type, str):
        data_type =  offset*"\t"+"Type :" + node.data_type
    if node.value:
        print(line_start,node.value)
        if data_type != "":
            print(data_type)
    else:
        print(line_start)
        if data_type != "":
            print(data_type)
    for child in node.children:
      visit(child, offset + 1)

def generate_table(node: Node, st=None):
    if st is None:
      st = dict()

    if node is None:
        return st

    if new_table_scope(node.type):
        scoped_st = dict()
        for child in node.children:
            scoped_st = generate_table(child, scoped_st)
        st[node.value] = scoped_st
        return st
    elif node.type == "variable_assignment":
        id = node.children[0].value
        if len(node.children[0].children) > 0:
            id += "." + node.children[0].children[0].value
        type = "void"

        for child in node.children:
            type = get_type(child)

        if (id is not None):
            if st.get(id) is not None and st.get(id) != type:
                raise Exception("Re-assigning variable with invalid type")
            st[id] = type

    for child in node.children:
        st = generate_table(child, st)
    return st


def get_type(node: Node):
    if is_primitive(node.type):
        return node.type
    else:
        for child in node.children:
            return get_type(child)

def is_primitive(type):
    primitive_types = ["boolean_types", "float_number", "integer_number", "string_object"]
    return type in primitive_types

def new_table_scope(type):
    return type == "class_decl" or "method_decl" in type
