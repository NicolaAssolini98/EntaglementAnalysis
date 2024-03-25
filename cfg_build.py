import re
from enum import Enum

import networkx as nx

pattern = r'^\s*([\w\s,]+)\s*=\s*([\w\s,]+\([\w\s,]+\))\s*$'
node_count = 1
exit_node = 'Exit'

class EdgeLabel:
    def __init__(self, type_label, value):
        self.value = value
        self.type = type_label

    def __str__(self):
        return str(self.type).split(".")[1] + ": " + str(self.value)

    def __repr__(self):
        return self.__str__()


class NodeType(Enum):
    Args = 1
    GateCall = 2
    Measure = 3
    NonZero = 4
    Zero = 5
    Skip = 6
    Ret = 7


def not_only_space(s):
    for char in s:
        if not char.isspace():
            return True
    return False


def count_tab(string):
    count = 0
    for char in string:
        if char == ' ':
            count += 1
        else:
            break  # Esci dal ciclo quando trovi il primo carattere non di spaziatura
    return count


def reset_count():
    global node_count
    node_count = 1


def new_node():
    global node_count
    node = str(node_count)
    node_count = node_count + 1
    return node


def extract_variables(declaration):
    pat = r'\b(\w+)\s*:'
    matches = re.findall(pat, declaration)
    return matches


def cfg_build(fun):
    for line in fun:
        if not not_only_space(line) or 'def' in line:
            continue

        graph = nx.DiGraph()
        start_node = 'Start'
        graph.add_node(start_node)
        print(count_tab(line))
        if re.match(pattern, line):
            print(line)
        elif 'for' in line:
            print('for loop')
        elif 'while' in line:
            print('while loop')
        elif 'if' in line:
            print('if branch')
        elif 'else' in line:
            print('else branch')


def build_cfg(lines, cfg=None, prev_node=None):
    global exit_node
    if len(lines) == 0:
        return cfg
    l = lines[0]

    if not not_only_space(lines[0]) or lines[0].replace(" ", "").startswith('#'):
        return build_cfg(lines[1:], cfg, prev_node)

    if 'def' in lines[0]:
        graph = nx.DiGraph()
        start_node = 'Start'
        reset_count()
        graph.add_node(start_node)
        graph.add_node(exit_node)
        args = extract_variables(lines[0])
        p_node = new_node()
        graph.add_edge(start_node, p_node, label=EdgeLabel(NodeType.Args, args))

        return build_cfg(lines[1:], graph, p_node)

    if re.match(pattern, lines[0]):
        p_node = new_node()
        cfg.add_node(p_node)
        cfg.add_edge(prev_node, p_node, label=EdgeLabel(NodeType.GateCall, lines[0].replace(" ", "").split('=')))

        return build_cfg(lines[1:], cfg, p_node)

    if 'return' in lines[0]:
        cfg.add_edge(prev_node, exit_node, label=EdgeLabel(NodeType.Ret, lines[0].replace(" ", "")[6:].split(',')))
        return cfg

    if 'if' in lines[0]:
        # if end_node is None:
        #     end_node = new_node()
        #     cfg.add_node(end_node)
        tabs = count_tab(lines[0])

        if_node = new_node()
        cfg.add_node(if_node)
        cfg.add_edge(prev_node, if_node, label=EdgeLabel(NodeType.NonZero, lines[0].replace(" ", "")[2:-1]))

        if_branch_lines = []
        if_branch_size = 1
        while count_tab(lines[if_branch_size]) > tabs:
            if_branch_lines.append(lines[if_branch_size])
            if_branch_size += 1

        if_cfg = nx.DiGraph()
        if_cfg.add_node(if_node)
        if_cfg = build_cfg(if_branch_lines, if_cfg, if_node)
        if_end_nodes = [node for node in if_cfg.nodes if if_cfg.out_degree(node) == 0]
        # end_node = end_nodes[0]
        # if len(end_nodes) > 1:
        cfg = nx.compose(cfg, if_cfg)
        end_node = new_node()
        cfg.add_node(end_node)
        for if_end_node in if_end_nodes:
            if if_end_node != exit_node:
                cfg = nx.relabel_nodes(cfg, {if_end_node: end_node})

            # cfg.add_edge(if_end_node, end_node, label=EdgeLabel(NodeType.Skip, ""))

        else_branch_size = if_branch_size + 1
        if 'else' in lines[if_branch_size]:
            else_node = new_node()
            cfg.add_node(else_node)
            cfg.add_edge(prev_node, else_node, label=EdgeLabel(NodeType.Zero, lines[0].replace(" ", "")[2:-1]))
            else_branch_lines = []
            while count_tab(lines[else_branch_size]) > tabs:
                else_branch_lines.append(lines[else_branch_size])
                else_branch_size += 1

            else_cfg = nx.DiGraph()
            else_cfg.add_node(else_node)
            else_cfg = build_cfg(else_branch_lines, else_cfg, else_node)
            else_end_nodes = [node for node in else_cfg.nodes if else_cfg.out_degree(node) == 0]
            cfg = nx.compose(cfg, else_cfg)
            for else_end_node in else_end_nodes:
                if else_end_node != exit_node:
                    cfg = nx.relabel_nodes(cfg, {else_end_node: end_node})
                # cfg.add_edge(else_end_node, end_node, label=EdgeLabel(NodeType.Skip, ""))
        else:
            cfg.add_edge(prev_node, end_node, label=EdgeLabel(NodeType.Zero, lines[0].replace(" ", "")[2:-1]))

        return build_cfg(lines[else_branch_size:], cfg, end_node)

    if 'while' in lines[0]:
        # if end_node is None:
        #     end_node = new_node()
        #     cfg.add_node(end_node)
        tabs = count_tab(lines[0])

        while_node = new_node()
        cfg.add_node(while_node)
        cfg.add_edge(prev_node, while_node, label=EdgeLabel(NodeType.NonZero, lines[0].replace(" ", "")[5:-1]))

        while_branch_lines = []
        while_branch_size = 1
        while count_tab(lines[while_branch_size]) > tabs:
            while_branch_lines.append(lines[while_branch_size])
            while_branch_size += 1

        w_cfg = nx.DiGraph()
        w_cfg.add_node(while_node)
        w_cfg = build_cfg(while_branch_lines, w_cfg, while_node)
        w_end_nodes = [node for node in w_cfg.nodes if w_cfg.out_degree(node) == 0]
        cfg = nx.compose(cfg, w_cfg)
        for w_end_node in w_end_nodes:
            if w_end_node != exit_node:
                cfg = nx.relabel_nodes(cfg, {w_end_node: prev_node})

            # cfg.add_edge(if_end_node, end_node, label=EdgeLabel(NodeType.Skip, ""))

        end_node = new_node()
        cfg.add_node(end_node)
        cfg.add_edge(prev_node, end_node, label=EdgeLabel(NodeType.Zero, lines[0].replace(" ", "")[5:-1]))

        return build_cfg(lines[while_branch_size:], cfg, end_node)

        # TODO for loop

    exit('error parsing: ' + str(lines))
