from collections import defaultdict
from enum import Enum
from functools import reduce

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
    U = 7
    S = 8
    Top = 9


order_L = [
    (L.Bot, L.X),
    (L.Bot, L.P),
    (L.Bot, L.Y),
    (L.Bot, L.R),
    (L.Bot, L.Z),
    (L.X, L.U),
    (L.P, L.U),
    (L.Y, L.U),
    (L.R, L.U),
    (L.U, L.S),
    (L.S, L.Top),
    (L.Z, L.Top)
]
lattice = nx.DiGraph()
lattice.add_edges_from(order_L)


class AbsDomain:
    """
    partitions: list of tuple (set of vars, index)
    labeling: dict of {index: label}
    """

    def __init__(self, partitions, labeling):
        if partitions is None:
            self.partitions = []
        else:
            self.partitions = partitions
        if labeling is None:
            self.labeling = dict()
        else:
            self.labeling = labeling

    def add_z_var(self, var):
        max_ind = self.__get_max_index()
        self.partitions.append(({var}, max_ind + 1))
        self.labeling[max_ind + 1] = L.Z

    def get_level_var(self, var):
        for (partition, index) in self.partitions:
            if var in partition:
                return partition, index

    def get_entangled_with_var(self, var):
        _, index = self.get_level_var(var)
        return [t for t in self.partitions if t[-1] == index]

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

    def put_same_level(self, var1, var2):
        """
        var2 takes the label from var1
        """
        p1 = self.get_level_var(var1)
        p2 = self.get_level_var(var2)
        if p1 != p2:
            p1[0].update(p2[0])
            self.partitions.remove(p2)

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
            new_index = self.__get_max_index() + 1
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

    def __get_max_index(self):
        return max(self.partitions, key=lambda x: x[2])[2]

    def __str__(self):
        return str(self.partitions)

    # s = '{'
    # if len(self.partitions) > 0:
    #     i = self.partitions[0][2]
    #
    # for v in self.partitions:
    #     s += f'{v}, '

    def __repr__(self):
        return self.__str__()


def abs_t(abs_dom, var):
    """
    :type var: str
    :type abs_dom: AbsDomain
    """
    in_val = abs_dom.get_value(var)

    if in_val == L.Bot or in_val == L.Z or in_val == L.U or in_val == L.S or in_val == L.Top:
        pass  # abs_dom.update_value(in_vars[0], val1)
    elif in_val == L.X:
        abs_dom.set_value(var, L.P)
    elif in_val == L.P:
        abs_dom.set_value(var, L.Y)
    elif in_val == L.Y:
        abs_dom.set_value(var, L.R)
    elif in_val == L.R:
        abs_dom.set_value(var, L.X)


def abs_h(abs_dom, var):
    """
    :type var: str
    :type abs_dom: AbsDomain
    """
    in_val = abs_dom.get_value(var)
    if len(abs_dom.get_entangled_with_var(var)) == 1:
        if in_val == L.Bot or in_val == L.Y or in_val == L.Top:
            pass  # abs_dom.update_value(in_vars[0], val1)
        elif in_val == L.P or in_val == L.R:
            abs_dom.set_value(var, L.S)
        elif in_val == L.S or in_val == L.U:
            abs_dom.set_value(var, L.Top)
    else:
        if in_val != L.Bot:
            abs_dom.dislevel(var)
            abs_dom.set_value(var, L.S)


def abs_cx(abs_dom, ctrl, trg):
    """
    :type trg: str
    :type ctrl: str
    :type abs_dom: AbsDomain
    """
    trg_val = abs_dom.get_value(trg)
    ctrl_val = abs_dom.get_value(ctrl)
    if trg_val == L.Bot or ctrl_val == L.Bot:
        pass
    elif len(abs_dom.get_entangled_with_var(trg)) == 1:
        if ctrl_val == L.Z or trg_val == L.X:
            pass  # abs_dom.update_value(in_vars[0], val1)
        elif ctrl_val != L.Top and trg_val == L.Z:
            abs_dom.put_same_level(ctrl, trg)
            # abs_dom.set_value(trg, V.S)
        else:
            abs_dom.entangle(ctrl, trg)
            abs_dom.set_value(trg, L.Top)
    elif abs_dom.are_entangled(ctrl, trg):
        if abs_dom.are_on_the_same_level(ctrl, trg):
            abs_dom.disentangle(trg)
            abs_dom.set_value(trg, L.Z)
    else:
        abs_dom.dislevel(trg)
        abs_dom.entangle(ctrl, trg)
        abs_dom.set_value(trg, L.Top)


def abs_measure(abs_dom, var):
    """
    :type var: str
    :type abs_dom: AbsDomain
    """
    in_val = abs_dom.get_value(var)
    if in_val == L.Bot:
        pass
    elif len(abs_dom.get_entangled_with_var(var)) == 1:
        abs_dom.set_value(var, L.Z)
    else:
        ent_vars = set.union(*(item[0] for item in abs_dom.get_entangled_with_var(var)))
        same_level_vars = abs_dom.get_level_var(var)[0]
        ent_vars.remove(var)
        same_level_vars.remove(var)
        for v in same_level_vars:
            abs_dom.disentangle(v)
            abs_dom.set_value(v, L.Z)
        for v in ent_vars.difference(same_level_vars):
            abs_dom.set_value(v, L.Top)


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
    :type abs_dom1: AbsDomain
    :type abs_dom2: AbsDomain
    """
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
                labels.add(abs_dom1.get_value(v))
        for v in abs_dom2.get_all_vars():
            if v in s:
                labels.add(abs_dom2.get_value(v))
        # TODO lub tra le labels
        store[i] = reduce(lambda x, y: lub_labels(x, y), labels)

    return res, store
    pass

