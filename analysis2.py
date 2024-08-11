import copy
from collections import defaultdict
from enum import Enum
from functools import reduce
from cfg_build import start_node, NodeType, EdgeLabel

import networkx as nx


# To disable debug print in this file
# debug = True
#
#
# def disable_print(*args, **kwargs):
#     pass
#
#
# if not debug:
#     print = disable_print
#

class L(Enum):
    Bot = 1
    Z = 2
    X = 3
    Y = 4
    R = 5
    P = 6
    S = 7
    Top = 8


order_L = [
    (L.Bot, L.X),
    (L.Bot, L.P),
    (L.Bot, L.Y),
    (L.Bot, L.R),
    (L.Bot, L.Z),
    (L.X, L.S),
    (L.P, L.S),
    (L.Y, L.S),
    (L.R, L.S),
    (L.S, L.Top),
    (L.Z, L.Top)
]
lattice = nx.DiGraph()
lattice.add_edges_from(order_L)


class AbsState:
    """
    partitions: list of tuple (set of vars, index)
    labeling: dict of {index: label}
    """

    def __init__(self, partitions=None, labeling=None):
        if partitions is None:
            self.partitions = []
        else:
            self.partitions = partitions
        if labeling is None:
            self.labeling = dict()
        else:
            self.labeling = labeling

    def add_z_var(self, var):
        max_ind = self.get_max_index()
        self.partitions.append(({var}, max_ind + 1))
        self.labeling[max_ind + 1] = L.Z

    def get_level_var(self, var):
        for (partition, index) in self.partitions:
            if var in partition:
                return partition, index

    def get_entangled_with_var(self, var):
        # print(f'p: {self.get_level_var(var)}')
        r = self.get_level_var(var)
        if r is not None:
            _, index = r
            res = set()
            for t in self.partitions:
                if t[-1] == index:
                    res.update(t[0])
            return res
        return set()

    def entangle(self, var1, var2):
        _, index1 = self.get_level_var(var1)
        _, index2 = self.get_level_var(var2)
        parts = []
        for t in self.partitions:
            if t[-1] == index2:
                parts.append(t)
        for part in parts:
            s, i = part
            self.partitions.remove(part)
            self.partitions.append((s, index1))
        self.labeling.pop(index2)

    def put_same_level(self, var1, var2):
        """
        var2 takes the label from var1
        """
        p1 = self.get_level_var(var1)
        p2 = self.get_level_var(var2)
        _, i = p2
        if p1 != p2:
            p1[0].update(p2[0])
            self.partitions.remove(p2)
            self.labeling.pop(i)

    def dislevel(self, var):
        """
        make var not at same level with other variables
        """
        if not self.is_alone_on_level(var):
            part, index = self.get_level_var(var)
            part.remove(var)
            self.partitions.append(({var}, index))

    def disentangle(self, var):
        """
        make var not entangled with other variables
        """
        if not self.is_separable(var):
            self.dislevel(var)
            new_index = self.get_max_index() + 1
            part = None
            for t in self.partitions:
                if var in t[0]:
                    part = t
                    break
            if part is not None:
                s, i = part
                self.partitions.remove(part)
                self.partitions.append((s, new_index))

    def are_on_the_same_level(self, var1, var2):
        p1 = self.get_level_var(var1)
        p2 = self.get_level_var(var2)
        return p1 == p2

    def are_entangled(self, var1, var2):
        _, index1 = self.get_level_var(var1)
        _, index2 = self.get_level_var(var2)
        print(f'p: {index1, index2}')
        return index1 == index2

    def set_value(self, var, value):
        part = None
        for t in self.partitions:
            if var in t[0]:
                part = t
                break
        if part is not None:
            s, i = part
            self.labeling[i] = value

    def is_alone_on_level(self, var):
        return len(self.get_level_var(var)[0]) == 1

    def is_separable(self, var):
        return len(self.get_entangled_with_var(var)) == 1

    def get_value(self, var):
        for t in self.partitions:
            if var in t[0]:
                return self.labeling[t[1]]
        return L.Bot

    def get_all_vars(self):
        res = set()
        for t in self.partitions:
            res.update(t[0])
        return res

    def copy(self):
        return AbsState(copy.deepcopy(self.partitions), copy.deepcopy(self.labeling))

    def get_max_index(self):
        m = 0
        for (partition, index) in self.partitions:
            if m < index:
                m = index
        return m

    def get_all_indexes(self):
        m = []
        for (_, index) in self.partitions:
            m.append(index)
        return m

    def __str__(self):
        return f'\n{str(self.partitions)}\n{str(self.labeling)}\n'

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if self.partitions != other.partitions:
            return False
        indexes_self = self.get_all_indexes()
        indexes_other = other.get_all_indexes()
        if indexes_self != indexes_other:
            return False
        for i in indexes_self:
            if self.labeling[i] != other.labeling[i]:
                return False
        return True


def abs_t(abs_dom, var):
    """
    :type var: str
    :type abs_dom: AbsState
    """
    abs_dom_1 = abs_dom.copy()
    in_val = abs_dom_1.get_value(var)

    if in_val == L.Bot or in_val == L.Z or in_val == L.S or in_val == L.Top:
        pass  # abs_dom.update_value(in_vars[0], val1)
    elif in_val == L.X:
        abs_dom_1.set_value(var, L.P)
    elif in_val == L.P:
        abs_dom_1.set_value(var, L.Y)
    elif in_val == L.Y:
        abs_dom_1.set_value(var, L.R)
    elif in_val == L.R:
        abs_dom_1.set_value(var, L.X)

    return abs_dom_1


def abs_h(abs_dom, var):
    """
    :type var: str
    :type abs_dom: AbsState
    """
    abs_dom_1 = abs_dom.copy()
    in_val = abs_dom_1.get_value(var)
    # print(f'p: {abs_dom.get_entangled_with_var(var)}')
    if in_val == L.Bot:
        pass  # abs_dom.update_value(in_vars[0], val1)
    elif len(abs_dom_1.get_entangled_with_var(var)) == 1:
        if in_val == L.Y or in_val == L.Top:
            pass  # abs_dom.update_value(in_vars[0], val1)
        elif in_val == L.Z:
            abs_dom_1.set_value(var, L.X)
        elif in_val == L.X:
            abs_dom_1.set_value(var, L.Z)
        elif in_val == L.P or in_val == L.R:
            abs_dom_1.set_value(var, L.S)
        elif in_val == L.S:
            abs_dom_1.set_value(var, L.Top)
    else:
        if in_val != L.Bot:
            abs_dom_1.dislevel(var)
            abs_dom_1.set_value(var, L.S)

    return abs_dom_1


def abs_cx(abs_dom, ctrl, trg):
    """
    :type trg: str
    :type ctrl: str
    :type abs_dom: AbsState
    """
    abs_dom_1 = abs_dom.copy()
    trg_val = abs_dom_1.get_value(trg)
    ctrl_val = abs_dom_1.get_value(ctrl)
    if trg_val == L.Bot or ctrl_val == L.Bot:
        pass
    elif len(abs_dom_1.get_entangled_with_var(trg)) == 1:
        if ctrl_val == L.Z or trg_val == L.X:
            pass  # abs_dom.update_value(in_vars[0], val1)
        elif ctrl_val != L.Top and trg_val == L.Z:
            abs_dom_1.put_same_level(ctrl, trg)
            # abs_dom.set_value(trg, V.S)
        else:
            abs_dom_1.entangle(ctrl, trg)
            abs_dom_1.set_value(trg, L.Top)
    elif abs_dom_1.are_entangled(ctrl, trg):
        print('qua')
        if abs_dom_1.are_on_the_same_level(ctrl, trg):
            abs_dom_1.disentangle(trg)
            abs_dom_1.set_value(trg, L.Z)
    else:
        abs_dom_1.dislevel(trg)
        abs_dom_1.entangle(ctrl, trg)
        abs_dom_1.set_value(trg, L.Top)

    return abs_dom_1


def abs_measure(abs_dom, var):
    """
    :type var: str
    :type abs_dom: AbsState
    """
    abs_dom_1 = abs_dom.copy()
    in_val = abs_dom_1.get_value(var)
    if in_val == L.Bot:
        pass
    elif len(abs_dom_1.get_entangled_with_var(var)) == 1:
        abs_dom_1.set_value(var, L.Z)
    else:
        ent_vars = abs_dom_1.get_entangled_with_var(var)
        same_level_vars = abs_dom_1.get_level_var(var)[0].copy()
        ent_vars.remove(var)
        same_level_vars.remove(var)
        for v in same_level_vars:
            abs_dom_1.disentangle(v)
            abs_dom_1.set_value(v, L.Z)
        for v in ent_vars.difference(same_level_vars):
            abs_dom_1.set_value(v, L.Top)

        abs_dom_1.disentangle(var)
        abs_dom_1.set_value(var, L.Z)

    return abs_dom_1


def merge_sets_by_index(list_of_tuples):
    # Create a dictionary to hold sets by index
    index_to_sets = defaultdict(set)

    # Iterate over each tuple in the list
    for s, index in list_of_tuples:
        # Union the set to the corresponding index in the dictionary
        index_to_sets[index].update(s)

    # Convert the dictionary values to a list of sets
    merged_sets = list(index_to_sets.values())

    return merged_sets


def merge_sets_with_common_elements(list_of_sets):
    # Set to store the merged sets
    fixpoint = False
    while not fixpoint:
        # old_sets = copy.deepcopy(list_of_sets)
        # old_sets = copy.deepcopy(list_of_sets)
        merged_sets = []
        # Loop through each set in the list
        for s in list_of_sets:
            # Check if the set has elements in common with any other merged set
            for m in merged_sets:
                if s & m:
                    # Merge the set with the other set
                    m |= s
                    break
            else:
                # If the set has no elements in common with any other merged set, add it to the merged sets
                merged_sets.append(s)

        fixpoint = (merged_sets == list_of_sets)
        list_of_sets = merged_sets
    return list_of_sets


def lub_labels(val1, val2):
    queue1 = [val1]
    queue2 = [val2]

    # Inizializza un insieme per tenere traccia dei nodi visitati
    visited1 = set()
    visited2 = set()

    # Continua la BFS finché ci sono nodi nella coda
    while queue1 or queue2:
        if queue1:
            current_node1 = queue1.pop(0)
            visited1.add(current_node1)
            neighbors1 = list(lattice.neighbors(current_node1))
            for neighbor in neighbors1:
                if neighbor not in visited1:
                    queue1.append(neighbor)
        if queue2:
            current_node2 = queue2.pop(0)
            visited2.add(current_node2)
            neighbors2 = list(lattice.neighbors(current_node2))
            for neighbor in neighbors2:
                if neighbor not in visited2:
                    queue2.append(neighbor)

        intersection = visited1 & visited2
        if intersection:
            return intersection.pop()

    return L.Bot


def lub_abs_dom(abs_dom1, abs_dom2):
    """
    :type abs_dom1: AbsState
    :type abs_dom2: AbsState
    """
    # if len(abs_dom1.partitions) == 0:
    #     print('èèèèè')
    #     return abs_dom2.copy()
    # if len(abs_dom2.partitions) == 0:
    #     print('èèèèè')
    #     return abs_dom1.copy()

    # Intersect same level vars
    tuples1 = abs_dom1.partitions
    list1 = [t[0] for t in tuples1]
    tuples2 = abs_dom2.partitions
    list2 = [t[0] for t in tuples2]

    # Initialize a list to hold the intersections
    intersections = []
    # Initialize a set to track elements in intersections
    intersected_elements = set()

    # Iterate over each set in the first list
    for set1 in list1:
        # Iterate over each set in the second list
        for set2 in list2:
            # Compute the intersection
            intersection = set1 & set2
            # If the intersection is not empty, add it to the result list
            if intersection:
                intersections.append(intersection)
                intersected_elements.update(intersection)

    # Collect singletons for elements not in any intersection
    all_vars = set().union(*list1, *list2)
    non_intersected_elements = all_vars - intersected_elements
    singletons = [{e} for e in non_intersected_elements]

    # Combine the intersections and singletons
    part = intersections + singletons

    # Create a dictionary to hold sets by index
    e_1 = merge_sets_by_index(tuples1)
    e_2 = merge_sets_by_index(tuples2)
    e_merged = merge_sets_with_common_elements(e_1 + e_2)

    # Create the set correspondig to non-separable variables
    e_with_index = [(s, i) for i, s in enumerate(e_merged, start=0)]

    res = []
    for p in part:
        v = next(iter(p))
        for s, i in e_with_index:
            if v in s:
                res.append((p, i))
                break

    # Computes the lub between labels
    store = {}

    for s, i in e_with_index:
        labels = set()
        for v in abs_dom1.get_all_vars():
            if v in s:
                if s == abs_dom1.get_entangled_with_var(v):
                    labels.add(abs_dom1.get_value(v))
                else:
                    labels.add(L.Top)
        for v in abs_dom2.get_all_vars():
            if v in s:
                if s == abs_dom2.get_entangled_with_var(v):
                    labels.add(abs_dom2.get_value(v))
                else:
                    labels.add(L.Top)
        store[i] = reduce(lambda x, y: lub_labels(x, y), labels)

    return AbsState(res, store)


def entanglement_analysis(all_vars, cfg):
    abs_states = {node: AbsState() for node in cfg.nodes()}
    initial_state = AbsState()
    for v in all_vars:
        initial_state.add_z_var(str(v))
    abs_states[start_node] = initial_state
    # print(initial_state)

    fixpoint = False
    # i = 0
    while not fixpoint:
        #         i += 1
        old_states = {node: abs_states[node].copy() for node in abs_states.keys()}
        for node in cfg.nodes():
            n = node
            temp_abs_states = []
            predecessors = list(cfg.predecessors(node))
            for pred in predecessors:
                label = cfg[pred][node]["label"]
                """
                :type label: EdgeLabel
                """
                # print(f'l: {label}')
                pass
                if label.type == NodeType.H:
                    temp_abs_states.append(abs_h(old_states[pred], label.value[0]))
                elif label.type == NodeType.T:
                    temp_abs_states.append(abs_t(old_states[pred], label.value[0]))
                elif label.type == NodeType.CX:
                    temp_abs_states.append(abs_cx(old_states[pred], label.value[0], label.value[1]))
                elif label.type == NodeType.NonZero or label.type == NodeType.Zero:
                    temp_abs_states.append(abs_measure(old_states[pred], label.value[0]))
                elif label.type == NodeType.Skip:
                    temp_abs_states.append(old_states[pred])

            if len(temp_abs_states) > 0:
                abs_states[node] = reduce(lambda x, y: lub_abs_dom(x, y), temp_abs_states)
            elif node == start_node:
                abs_states[node] = initial_state
            else:
                abs_states[node] = AbsState()
        # print('§§§§§§§§§')
        # print(i)
        # print(old_states)
        # print('--------')
        # print(abs_states)
        # print(old_states == abs_states)
        fixpoint = (old_states == abs_states)
        # print('§§§§§§§§§')
        # print()
        # for node in cfg.nodes():
        #     print(f'node: {node}')
        #     print(f'part: {old_states[node].partitions == abs_states[node].partitions}')
        #     print(f'lab: {old_states[node].labeling == abs_states[node].labeling}')

    return abs_states
