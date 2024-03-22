import re
from enum import Enum

import networkx as nx

pattern = r'^\s*([\w\s,]+)\s*=\s*([\w\s,]+\([\w\s,]+\))\s*$'
node_count = 1


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
    Guard = 4


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


def build_cfg(lines, cfg=None, prev_node=None, end_node=None):

    if len(lines) == 0:
        return cfg

    if not not_only_space(lines[0]) or lines[0].replace(" ", "").startswith('#'):
        print(lines[0])
        return build_cfg(lines[1:], cfg, prev_node, end_node)

    if 'def' in lines[0]:
        graph = nx.DiGraph()
        start_node = 'Start'
        reset_count()
        graph.add_node(start_node)
        args = extract_variables(lines[0])
        p_node = new_node()
        graph.add_edge(start_node, p_node, label=EdgeLabel(NodeType.Args, args))

        return build_cfg(lines[1:], graph, p_node)

    if re.match(pattern, lines[0]):
        p_node = new_node()
        cfg.add_edge(prev_node, p_node, label=EdgeLabel(NodeType.GateCall, lines[0].replace(" ", "").split('=')))

        return build_cfg(lines[1:], cfg, p_node)

    exit('error parsing: ' + lines)
    # if root.type == NodeType.IfRoot:
    #     if end_node is None:
    #         end_node = new_node()
    #         cfg.add_node(end_node)
    #
    #     gard_val = [True, False]
    #     for i in range(1, len(root.children)):
    #         child = root.children[i]
    #         # As gard branch we use
    #         gard_node = ASTNode(NodeType.Gard, gard_val[i-1])
    #         gard_node.children.append(root.children[0])
    #         if len(child.children) > 0:
    #             b_node = new_node()
    #             cfg.add_node(b_node)
    #             cfg.add_edge(prev_node, b_node, label=EdgeLabel(gard_node))
    #             for nephew in child.children[:-1]:
    #                 # print(nephew)
    #                 b_node = build_cfg(nephew, cfg, b_node)
    #             build_cfg(child.children[-1], cfg, b_node, end_node)
    #         else:
    #             cfg.add_edge(prev_node, end_node, label=EdgeLabel(gard_node))
    #
    #     return end_node
    #
    # # TODO da decidere se ha senso tenere i while o risolverli in if nestati all'inizio
    # if root.type == NodeType.WhileRoot:
    #     if end_node is None:
    #         end_node = new_node()
    #         cfg.add_node(end_node)
    #
    #     end_loop_node = new_node()
    #     cfg.add_node(end_loop_node)
    #     gard_node_true = ASTNode(NodeType.Gard, True)
    #     gard_node_true.children.append(root.children[0])
    #     gard_node_false = ASTNode(NodeType.Gard, False)
    #     gard_node_false.children.append(root.children[0])
    #     max_iter_node = ASTNode(NodeType.MaxIt, root.children[1])
    #
    #     child = root.children[2]
    #     if len(child.children) > 0:
    #         b_node = new_node()
    #         cfg.add_node(b_node)
    #         cfg.add_edge(prev_node, b_node, label=EdgeLabel(gard_node_true))
    #         for nephew in child.children[:-1]:
    #             # print(nephew)
    #             b_node = build_cfg(nephew, cfg, b_node)
    #         build_cfg(child.children[-1], cfg, b_node, end_loop_node)
    #     else:
    #         cfg.add_edge(prev_node, end_loop_node, label=EdgeLabel(gard_node_true))
    #
    #     cfg.add_edge(end_loop_node, prev_node, label=EdgeLabel(max_iter_node))
    #     cfg.add_edge(prev_node, end_node, label=EdgeLabel(gard_node_false))
    #
    #     return end_node
    #
    # if root.type == NodeType.Assign:
    #     if end_node is None:
    #         end_node = new_node()
    #         cfg.add_node(end_node)
    #     # cfg.add_edge(prev_node, end_node, label=str(root))
    #     cfg.add_edge(prev_node, end_node, label=EdgeLabel(root))
    #     return end_node
