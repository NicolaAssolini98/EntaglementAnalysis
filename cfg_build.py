import re
from enum import Enum

import networkx as nx
from lark import Tree, Token
from matplotlib import pyplot as plt

pattern_gate_app = r'^\s*([\w\s,]+)\s*=\s*([\w\s,]+\([\w\s,]+\))\s*$'
pattern_init = r'^(\s*\w+\s*(\s*,\s*\w+)*)\s*=\s*qubit\(\s*\)(\s*,\s*qubit\(\s*\))*'
pattern_measure = r'\w'
node_count = 1
exit_node = 'Exit'
start_node = 'Start'

"""
P(q)∣
∣ P(¬q) ∣
∣ skip ∣
∣ h(q)∣
∣ t(q)∣
∣ cx(q, t) 
"""


class NodeType(Enum):
    NonZero = 1
    Zero = 2
    Skip = 3
    H = 4
    T = 5
    CX = 6


class EdgeLabel:
    def __init__(self, type_label, value):
        self.value = value
        self.type = type_label

    def __str__(self):
        return str(self.type).split(".")[1] + ": " + str(self.value)

    def __repr__(self):
        return self.__str__()



def new_node():
    global node_count
    node = str(node_count)
    node_count = node_count + 1
    return node


def get_variables(tree):
    """
    :type tree: Tree
    :return: list of variables
    """
    if isinstance(tree, Tree):
        if tree.data == 'decl':
            return [child for child in tree.children]

    exit('Invalid AST')


def build_graph(trees, cfg, prev_node):
    """
    :return:
    """
    if len(trees) == 0:
        return cfg

    for t in trees:
        print(t.data)

    if isinstance(trees[0], Tree):
        if trees[0].data == 'cx_stmt':
            p_node = new_node()
            cfg.add_node(p_node)
            cfg.add_edge(prev_node, p_node, label=EdgeLabel(NodeType.CX, []))

            return build_graph(trees[1:], cfg, p_node)
        if trees[0].data == 't_stmt':
            pass
        if trees[0].data == 'h_stmt':
            pass

    if isinstance(trees[0], Token):
        if trees[0].value == 'pass_stmt':
            p_node = new_node()
            cfg.add_node(p_node)
            cfg.add_edge(prev_node, p_node, label=EdgeLabel(NodeType.Skip, ''))

            return build_graph(trees[1:], cfg, p_node)
        if trees[0].type == 'NAME':
            return trees[0].value


def init_cfg(ast):
    if isinstance(ast, Tree):
        if ast.data == 'start':
            graph = nx.DiGraph()
            p_vars = get_variables(ast.children[0])
            graph.add_node(start_node)

            return p_vars, build_graph(ast.children[1:], graph, start_node)

    exit('Invalid AST')
