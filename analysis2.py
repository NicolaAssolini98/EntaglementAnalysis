import copy
from enum import Enum
from functools import reduce

import networkx as nx

from cfg_build import NodeType, exit_node


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

class Label(Enum):
    Bot = 1
    Z = 2
    X = 3
    Y = 4
    R = 5
    P = 6
    U = 7
    S = 8
    Top = 9


class bValue:
    def __init__(self, values=None):
        if values is None:
            self.values = set()
        else:
            self.values = values

    def __str__(self):
        s = ''
        for v in self.values:
            s += f'{v}'
        return f'{s[:-1]}):{self.values}'

    def __repr__(self):
        return self.__str__()

    def compress(self):
        if Label.Bot in self.values and len(self.values) > 1:
            self.values.discard(Label.Bot)

        if (Label.Top in self.values or (Label.U in self.values and Label.Z in self.values)
                or (Label.S in self.values and Label.Z in self.values)):
            self.values = {Label.Top}


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
        self.labeling[max_ind + 1] = Label.Z

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
        return Label.Bot

    def get_all_variables(self):
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

    if in_val == Label.Bot or in_val == Label.Z or in_val == Label.U or in_val == Label.S or in_val == Label.Top:
        pass  # abs_dom.update_value(in_vars[0], val1)
    elif in_val == Label.X:
        abs_dom.set_value(var, Label.P)
    elif in_val == Label.P:
        abs_dom.set_value(var, Label.Y)
    elif in_val == Label.Y:
        abs_dom.set_value(var, Label.R)
    elif in_val == Label.R:
        abs_dom.set_value(var, Label.X)


def abs_h(abs_dom, var):
    """
    :type var: str
    :type abs_dom: AbsDomain
    """
    in_val = abs_dom.get_value(var)
    if len(abs_dom.get_entangled_with_var(var)) == 1:
        if in_val == Label.Bot or in_val == Label.Y or in_val == Label.Top:
            pass  # abs_dom.update_value(in_vars[0], val1)
        elif in_val == Label.P or in_val == Label.R:
            abs_dom.set_value(var, Label.S)
        elif in_val == Label.S or in_val == Label.U:
            abs_dom.set_value(var, Label.Top)
    else:
        if in_val != Label.Bot:
            abs_dom.dislevel(var)
            abs_dom.set_value(var, Label.S)


def abs_cx(abs_dom, ctrl, trg):
    """
    :type trg: str
    :type ctrl: str
    :type abs_dom: AbsDomain
    """
    trg_val = abs_dom.get_value(trg)
    ctrl_val = abs_dom.get_value(ctrl)
    if trg_val == Label.Bot or ctrl_val == Label.Bot:
        pass
    elif len(abs_dom.get_entangled_with_var(trg)) == 1:
        if ctrl_val == Label.Z or trg_val == Label.X:
            pass  # abs_dom.update_value(in_vars[0], val1)
        elif ctrl_val != Label.Top and trg_val == Label.Z:
            abs_dom.put_same_level(ctrl, trg)
            # abs_dom.set_value(trg, V.S)
        else:
            abs_dom.entangle(ctrl, trg)
            abs_dom.set_value(trg, Label.Top)
    elif abs_dom.are_entangled(ctrl, trg):
        if abs_dom.are_on_the_same_level(ctrl, trg):
            abs_dom.disentangle(trg)
            abs_dom.set_value(trg, Label.Z)
    else:
        abs_dom.dislevel(trg)
        abs_dom.set_value(trg, Label.Top)


def abs_measure(abs_dom, var):
    """
    :type var: str
    :type abs_dom: AbsDomain
    """
    in_val = abs_dom.get_value(var)
    if in_val == Label.Bot:
        pass
    elif len(abs_dom.get_entangled_with_var(var)) == 1:
        abs_dom.set_value(var, Label.Z)
    else:
        ent_vars = set.union(*(item[0] for item in abs_dom.get_entangled_with_var(var)))
        same_level_vars = abs_dom.get_level_var(var)[0]
        ent_vars.remove(var)
        same_level_vars.remove(var)
        for v in same_level_vars:
            abs_dom.disentangle(v)
            abs_dom.set_value(v, Label.Z)
        for v in ent_vars.difference(same_level_vars):
            abs_dom.set_value(v, Label.Top)



def lub_abs_dom(abs_dom1, abs_dom2):



    pass
