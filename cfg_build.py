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
        """
        :type type_label: NodeType
        :type value: list of Token
        """
        self.value = value
        self.type = type_label

    def __str__(self):
        return str(self.type).split(".")[1] + ": " + str(self.value)

    def __repr__(self):
        return self.__str__()


def print_cfg(cfg):
    pos = nx.spring_layout(cfg)
    labels = nx.get_edge_attributes(cfg, 'label')
    nx.draw(cfg, pos, with_labels=True, node_size=300, node_color="lightblue", font_size=8, font_color="black",
            font_weight="bold", arrows=True)
    nx.draw_networkx_edge_labels(cfg, pos, edge_labels=labels, font_size=7)
    plt.title("Control Flow Graph with Edge Labels")
    plt.show()


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


def extract_sub_graph(cfg, sub_tree, head_node, end_node):
    if sub_tree is None:
        cfg = nx.relabel_nodes(cfg, {head_node: end_node})

        return cfg
    if isinstance(sub_tree, Tree):
        if sub_tree.data == 'body':
            branch_cfg = nx.DiGraph()
            branch_cfg.add_node(head_node)
            branch_cfg = build_graph(sub_tree.children, branch_cfg, head_node)
            branch_end_nodes = [node for node in branch_cfg.nodes if branch_cfg.out_degree(node) == 0]
            cfg = nx.compose(cfg, branch_cfg)
            for branch_end_node in branch_end_nodes:
                cfg = nx.relabel_nodes(cfg, {branch_end_node: end_node})

            return cfg

    exit('Invalid AST')


def build_graph(trees, cfg, prev_node):
    """
    :return:
    """
    if len(trees) == 0:
        return cfg

    tree = trees[0]
    end_node = new_node()
    cfg.add_node(end_node)
    if isinstance(tree, Tree):
        if tree.data == 'cx_stmt' or tree.data == 't_stmt' or tree.data == 'h_stmt' or tree.data == 'pass_stmt':
            node_type = {'cx_stmt': NodeType.CX, 't_stmt': NodeType.T, 'h_stmt': NodeType.H,
                         'pass_stmt': NodeType.Skip}.get(tree.data)
            cfg.add_edge(prev_node, end_node, label=EdgeLabel(node_type, [child.value for child in tree.children]))

        elif tree.data == 'if_stmt':
            cond = tree.children[0].value
            types = [NodeType.NonZero, NodeType.Zero]

            for i in range(len(types)):
                branch_node = new_node()
                cfg.add_node(branch_node)
                cfg.add_edge(prev_node, branch_node, label=EdgeLabel(types[i], [cond]))
                cfg = extract_sub_graph(cfg, tree.children[i + 1], branch_node, end_node)

        elif tree.data == 'while_stmt':
            cond = tree.children[0].value
            branch_node = new_node()
            cfg.add_node(branch_node)
            cfg.add_edge(prev_node, branch_node, label=EdgeLabel(NodeType.NonZero, [cond]))
            cfg = extract_sub_graph(cfg, tree.children[1], branch_node, prev_node)
            cfg.add_edge(prev_node, end_node, label=EdgeLabel(NodeType.Zero, [cond]))

    return build_graph(trees[1:], cfg, end_node)


def init_cfg(ast):
    if isinstance(ast, Tree):
        if ast.data == 'start':
            graph = nx.DiGraph()
            p_vars = get_variables(ast.children[0])
            graph.add_node(start_node)
            graph = build_graph(ast.children[1:], graph, start_node)

            end_node = [node for node in graph.nodes if graph.out_degree(node) == 0]
            if len(end_node) != 1:
                exit('Bad shaped CFG')
            graph = nx.relabel_nodes(graph, {end_node[0]: exit_node})

            return p_vars, graph
    exit('Invalid AST')
