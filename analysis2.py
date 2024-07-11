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

class V(Enum):
    Bot = 1
    Z = 2
    X = 3
    Y = 4
    R = 5
    P = 6
    U = 7
    S = 8
    Top = 9


class Value:
    def __init__(self, values=None):
        if values is None:
            self.values = set()
        else:
            self.values = values

    def __str__(self):
        s = ''
        for v in self.vars:
            s += f'{v}'
        return f'{s[:-1]}):{self.value}'

    def __repr__(self):
        return self.__str__()

    def compress(self):
        if V.Bot in self.values and len(self.values) > 1:
            self.values.discard(V.Bot)

        if (V.Top in self.values or (V.U in self.values and V.Z in self.values)
                or (V.S in self.values and V.Z in self.values)):
            self.values = {V.Top}


class AbsDomain:
    """
    partitions: list of tuple (set of vars, label, index)
    """

    def __init__(self, partitions):
        if partitions is None:
            self.partitions = []
        else:
            self.partitions = partitions

    def add_z_var(self, var):
        max_ind = self.__get_max_index()
        self.partitions.append(({var}, V.Z, max_ind + 1))

    def get_level_var(self, var):
        for (partition, label, index) in self.partitions:
            if var in partition:
                return partition, label, index

    def get_entangled_with_var(self, var):
        _, _, index = self.get_level_var(var)
        return [t for t in self.partitions if t[-1] == index]

    def entangle(self, var1, var2):
        _, _, index1 = self.get_level_var(var1)
        _, _, index2 = self.get_level_var(var2)
        for t in self.partitions:
            if t[-1] == index2:
                t[-1] = index1

    def put_same_level(self, var1, var2):
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
            part, label, index = self.get_level_var(var)
            part.remove(var)
            self.partitions.append(({var}, V.Bot, index))

    def disentangle(self, var):
        """
        make var not entangled with other variables
        """
        if not self.is_separable(var):
            self.dislevel(var)
            new_index = self.__get_max_index() + 1
            for t in self.partitions:
                if var in t[0]:
                    t[-1] = new_index
                    return

    def are_on_the_same_level(self, var1, var2):
        p1 = self.get_level_var(var1)
        p2 = self.get_level_var(var2)
        return p1 == p2

    def are_entangled(self, var1, var2):
        _, _, index1 = self.get_level_var(var1)
        _, _, index2 = self.get_level_var(var2)
        return index1 == index2

    def set_value(self, var, value):
        for t in self.partitions:
            if var in t[0]:
                t[1] = value
                return

    def is_alone_on_level(self, var):
        return len(self.get_level_var(var)[0]) == 1

    def is_separable(self, var):
        return len(self.get_entangled_with_var(var)) == 1

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


class old_AbsDomain:
    def __init__(self):
        self.partitions = []
    def add_z_var(self, var):
        self.partitions.append([FirstPartition(var, V.Z)])
    def add_part(self, partition):
        self.partitions.append(partition)
    def get_second_part_from_var(self, var):
        for partition in self.partitions:
            for p in partition:
                if p.is_in(var):
                    return partition
            # print()
    def get_first_part_from_var(self, var):
        for partition in self.partitions:
            for p in partition:
                if p.is_in(var):
                    return p
    def entangle(self, var1, var2):
        p1 = self.get_second_part_from_var(var1)
        p2 = self.get_second_part_from_var(var2)
        if p1 != p2:
            p1.extend(p2)
            self.partitions.remove(p2)
    def put_same_level(self, var1, var2):
        self.entangle(var1, var2)
        e = self.get_second_part_from_var(var2)
        p1 = self.get_first_part_from_var(var1)
        p2 = self.get_first_part_from_var(var2)
        if p1 != p2:
            p1.extend(p2)
            e.remove(p2)
    def dislevel(self, var):
        if not self.is_alone_lv1(var):
            p2 = self.get_second_part_from_var(var)
            p1 = self.get_first_part_from_var(var)
            p1.remove(var)
            p2.append(FirstPartition(var, V.Bot))
    def disentangle(self, var):
        if not self.is_alone(var):
            self.dislevel(var)
            p2 = self.get_second_part_from_var(var)
            p1 = self.get_first_part_from_var(var)
            p2.remove(p1)
            self.partitions.append([FirstPartition(var, V.Bot)])
    def are_on_the_same_level(self, var1, var2):
        p1 = self.get_first_part_from_var(var1)
        p2 = self.get_first_part_from_var(var2)
        return p1 == p2
    def are_entangled(self, var1, var2):
        p1 = self.get_second_part_from_var(var1)
        p2 = self.get_second_part_from_var(var2)
        return p1 == p2
    def set_value(self, var, value):
        p1 = self.get_first_part_from_var(var)
        print(p1)
        p1.value = value
    def is_alone_lv2(self, var):
        return len(self.get_second_part_from_var(var)) == 1
    def is_alone_lv1(self, var):
        return len(self.get_first_part_from_var(var)) == 1
    def is_alone(self, var):
        return len(self.get_second_part_from_var(var)) == 1 and len(self.get_first_part_from_var(var)) == 1


    def __str__(self):
        s = '{'
        for v in self.partitions:
            s += f'{v}, '

        return f'{s[:-2]}}}'

    def __repr__(self):
        return self.__str__()


class FirstPartition:
    def __init__(self, keys, value):
        self.vars = keys
        self.value = value

    def is_in(self, var):
        return var in self.vars

    def extend(self, p):
        self.vars.extend(p.vars)

    def remove(self, var):
        self.vars.remove(var)

    def __len__(self):
        return len(self.vars)

    def __str__(self):
        s = '('
        for v in self.vars:
            s += f'{v}-'
        return f'{s[:-1]}):{self.value}'

    def __repr__(self):
        return self.__str__()


# E[¬q2] disentangle q2
# E[∼q2] dislevel q2
# E[q1 + q2] put on the same level

# E[q1 ⊎ q2] ∪ e + K
# E[q1 ∪ q2] entangled K
# E(q) = {q, p} and E{q} = {q p, t}. K


e1 = FirstPartition(['x', 'y'], V.X)
e2 = FirstPartition(['t'], V.Y)

E = AbsDomain()
# E.add_part([e1])
E.add_part([e1, e2])
print(E)
E.add_z_var('z')
print(E)
# E.dislevel('y')
# E.dislevel('t')

# E.disentangle('y')
E.disentangle('t')
E.set_value('t', V.Z)

# print(E.is_alone_lv1('z'))
# print(E.is_alone_lv2('z'))
# print(E.is_alone('z'))
# print(E.is_alone_lv1('t'))
# print(E.is_alone_lv2('t'))
# print(E.is_alone('x'))
# print(E.get_second_part_from_var('x'))
# print(E.get_second_part_from_var('z'))
# print(E.get_first_part_from_var('x'))
# print(E.get_first_part_from_var('x') == E.get_first_part_from_var('y'))
# print(E.get_first_part_from_var('z'))
# print(E.are_entangled('t', 'z'))
print(E)
# print(E.are_entangled('x', 'y'))
# print(E.are_entangled('x', 't'))
# print(E)
