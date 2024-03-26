import copy
from enum import Enum
from functools import reduce

from cfg_build import NodeType

one_qubit_gate = ['x', 'y', 'z', 's', 'h', 't', 'tdg', 'rz', 'rx']


class Value(Enum):
    Bot = 1
    Z = 2
    X = 3
    Y = 4
    S = 5
    D = 6
    R = 7
    EX = 8
    EY = 9
    ES = 10
    Top = 11


class Pair:
    def __init__(self, store=None, sets=None):
        if store is None:
            self.store = dict()
        else:
            self.store = store

        if sets is None:
            self.sets = []
        else:
            self.sets = sets

    def get_store_val(self, key):
        return self.store.get(key, Value.Bot)

    def add(self, key, value):
        self.store[key] = value
        s = set()
        s.add(key)
        self.sets.append(s)

    def update_value(self, key, value):
        self.store[key] = value

        # self.part.add(key)

    def rename(self, old_name, new_name):
        self.store[new_name] = self.store.pop(old_name)
        for s in self.sets:
            if old_name in s:
                s.remove(old_name)
                s.add(new_name)

    def copy(self):
        return Pair(self.store.copy(), copy.deepcopy(self.sets))

    def get_set(self, var):
        set_v = [s for s in self.sets if var in s]

        if len(set_v) == 0:
            # return {var}
            return set()
        if len(set_v) > 1:
            exit('Partition ill-formed')
        return set_v[0]

    def join(self, var1, var2):
        set_v1 = self.get_set(var1)
        set_v2 = self.get_set(var2)

        if set_v1 != set_v2:
            set_v1.update(set_v2)

            if set_v2 in self.sets:
                self.sets.remove(set_v2)

    def remove_from(self, var1, var2):
        set_v1 = self.get_set(var1)
        set_v2 = self.get_set(var2)

        if len(set_v1) > 0:
            if set_v1 != set_v2:
                exit('Partition ill-formed')

            self.sets.remove(set_v1)
            set_v1.discard(var2)
            self.sets.append(set_v1)
            self.sets.append({var2})

    def is_disjoint(self, var1, var2):
        set_v1 = self.get_set(var1)
        set_v2 = self.get_set(var2)

        return not set_v1 == set_v2

    def __str__(self):
        return "store: %s\n sets:%s\n" % (str(self.store), str(self.sets))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, Pair):
            return self.store == other.store and self.sets == other.sets
        return False

    def __lt__(self, other):
        return True

    def __gt__(self, other):
        return False


def copy_sets(sets):
    """
    :type sets: dict
    :return:
    """
    new_live_vars = {node: sets[node].copy() for node in sets.keys()}

    return new_live_vars


def consumption_analysis(cfg):
    avs_vars = {node: set() for node in cfg.nodes()}
    ovs_vars = {node: set() for node in cfg.nodes()}

    fixpoint = False
    while not fixpoint:
        old_avls = copy_sets(avs_vars)
        old_ovs = copy_sets(ovs_vars)
        for node in cfg.nodes():
            temps_avs, temps_ovs = [], []
            predecessors = list(cfg.predecessors(node))
            for prec in predecessors:
                added_vars = set()
                removed_vars = set()
                label = cfg[prec][node]["label"]
                inst_type = label.type
                instr = label.value
                if inst_type == NodeType.Args or inst_type == NodeType.Init:
                    # ['arg1', 'arg2']
                    added_vars.update(instr)
                elif inst_type == NodeType.Ret or inst_type == NodeType.Discard:
                    # ['arg1', 'arg2']
                    removed_vars.update(instr)
                elif inst_type == NodeType.GateCall:
                    # [['out1', 'out2'], 'cx', ['in1', 'in2']]
                    added_vars.update(instr[0])
                    removed_vars.update(instr[2])
                temp_avs = old_avls[prec] - removed_vars
                temp_ovs = old_avls[prec] - removed_vars
                temp_avs.update(added_vars)
                temp_ovs.update(added_vars)
                temps_avs.append(temp_avs)
                temps_ovs.append(temp_avs)

            if len(temps_avs) > 0:
                intersection = reduce(lambda x, y: x & y, temps_avs)
            else:
                intersection = set()
            if len(temps_ovs) > 0:
                union = reduce(lambda x, y: x | y, temps_avs)
            else:
                union = set()
            avs_vars[node] = intersection
            ovs_vars[node] = union

        fixpoint = (old_avls == avs_vars) and (old_ovs == ovs_vars)

    # TODO test overwriting
    for edge in cfg.edges:
        # print(edge)
        label = cfg[edge[0]][edge[1]]["label"]
        inst_type = label.type
        instr = label.value
        # print(label)
        # if inst_type == NodeType.Args or inst_type == NodeType.Init:
        #     # ['arg1', 'arg2']
        if inst_type == NodeType.Ret or inst_type == NodeType.Discard:
            # ['arg1', 'arg2']
            if not (set(instr) <= avs_vars[edge[0]]):
                exit('Instr %s at node %s used consumed variable' % (instr, edge[0]))
        elif inst_type == NodeType.GateCall:
            # [['out1', 'out2'], 'cx', ['in1', 'in2']]
            if not (set(instr[2]) <= avs_vars[edge[0]]):
                exit('Instr %s at node %s used consumed variable' % (instr, edge[0]))
            v = ovs_vars[edge[0]] - set(instr[2])
            if not set(instr[0]).isdisjoint(v):
                exit('Instr %s at node %s overwrite variable' % (instr, edge[0]))
        elif inst_type == NodeType.Init:
            # ['arg1', 'arg2']
            if not set(instr).isdisjoint(ovs_vars[edge[0]]):
                exit('Instr %s at node %s overwrite variable' % (instr, edge[0]))
    return avs_vars, ovs_vars


def compute_one_qubit_gate(fun, val1):
    if fun == 'x' or fun == 'y' or fun == 'z':
        return val1
    elif fun == 'h':
        if val1 == Value.Y or val1 == Value.R or val1 == Value.Bot:
            return val1
        elif val1 == Value.Z:
            return Value.X
        elif val1 == Value.X:
            return Value.Z
        elif val1 == Value.D:
            return Value.S
        elif val1 == Value.S:
            return Value.D
        else:
            return Value.Top
    elif fun == 't' or fun == 'tdg':
        if val1 == Value.Z or val1 == Value.S or val1 == Value.Bot:
            return val1
        elif val1 == Value.X or val1 == Value.Y:
            return Value.S
        else:
            return Value.Top
    elif fun == 's':
        if val1 == Value.Z or val1 == Value.S or val1 == Value.Bot:
            return val1
        elif val1 == Value.Y:
            return Value.X
        elif val1 == Value.X:
            return Value.Y
        elif val1 == Value.D:
            return Value.R
        elif val1 == Value.R:
            return Value.D
        else:
            return Value.Top

    return Value.Top


def disentagled_on_value(abs_dom, val, var1, var2):
    abs_dom.update_value(var2, Value.Z)
    abs_dom.remove_from(var1, var2)
    ent_set = abs_dom.get_set(var1)
    if len(ent_set) == 1:
        abs_dom.update_value(var1, val)

    return abs_dom


def set_entagled_on_value(abs_dom, val, var1, var2):
    abs_dom.update_value(var1, val)
    abs_dom.update_value(var2, val)
    abs_dom.join(var1, var2)

    return abs_dom


def abs_semantics(fun, abs_dom, in_vars):
    if fun in one_qubit_gate:
        v0 = abs_dom.get_store_val(in_vars[0])
        v1 = compute_one_qubit_gate(fun, v0)
        abs_dom.update_value(in_vars[0], v1)
        return abs_dom
    if fun == 'cx':
        ctrl = in_vars[0]
        targ = in_vars[1]
        v_c = abs_dom.get_store_val(ctrl)
        v_t = abs_dom.get_store_val(targ)
        if (v_c == Value.Z or v_t == Value.X or v_c == Value.Bot or v_t == Value.Bot) and abs_dom.is_disjoint(ctrl,
                                                                                                              targ):
            return abs_dom
        if (v_c == Value.X or v_c == Value.EX) and v_t == Value.Z and abs_dom.is_disjoint(ctrl, targ):
            return set_entagled_on_value(abs_dom, Value.EX, ctrl, targ)
        if (v_c == Value.Y or v_c == Value.EY) and v_t == Value.Z and abs_dom.is_disjoint(ctrl, targ):
            return set_entagled_on_value(abs_dom, Value.EY, ctrl, targ)
        if (v_c == Value.S or v_c == Value.ES) and v_t == Value.Z and abs_dom.is_disjoint(ctrl, targ):
            return set_entagled_on_value(abs_dom, Value.ES, ctrl, targ)
        if v_c == Value.EX and v_t == v_c and not abs_dom.is_disjoint(ctrl, targ):
            return disentagled_on_value(abs_dom, Value.X, ctrl, targ)
        if v_c == Value.EY and v_t == v_c and not abs_dom.is_disjoint(ctrl, targ):
            return disentagled_on_value(abs_dom, Value.Y, ctrl, targ)
        if v_c == Value.ES and v_t == v_c and not abs_dom.is_disjoint(ctrl, targ):
            return disentagled_on_value(abs_dom, Value.S, ctrl, targ)
        if v_t == Value.Top and not abs_dom.is_disjoint(ctrl, targ):
            return abs_dom

        return set_entagled_on_value(abs_dom, Value.Top, ctrl, targ)

    if fun == 'cz':
        abs_dom = abs_semantics('h',abs_dom, in_vars[1:])
        abs_dom = abs_semantics('cx', abs_dom, in_vars)
        return abs_semantics('h', abs_dom, in_vars[1:])



def entaglement_analysis(cfg):
    pairs = {node: Pair() for node in cfg.nodes()}

    fixpoint = False
    while not fixpoint:
        old_pairs = copy_sets(pairs)
        for node in cfg.nodes():
            temps_pairs = []
            predecessors = list(cfg.predecessors(node))
            for prec in predecessors:
                label = cfg[prec][node]["label"]
                temp = pairs[prec].copy()
                inst_type = label.type
                instr = label.value
                if inst_type == NodeType.Init:
                    # ['arg1', 'arg2']
                    for v in instr:
                        temp.add(v, Value.Z)
                elif inst_type == NodeType.GateCall:
                    # [['out1', 'out2'], 'cx', ['in1', 'in2']]
                    temp = abs_semantics(instr[1], temp, instr[2])
                    for i in range(len(instr[2])):
                        temp.rename(instr[2][i], instr[0][i])
                temps_pairs.append(temp)

            if len(temps_pairs) > 0:
                join = temps_pairs[0]
            else:
                join = Pair()
            # TODO join
            pairs[node] = join
        # print(pairs[])
        b = old_pairs == pairs
        fixpoint = (old_pairs == pairs)

    return pairs

    #     for prec in predecessors:
    #         added_vars = set()
    #         removed_vars = set()

    #         if inst_type == NodeType.Args or inst_type == NodeType.Init:
    #             # ['arg1', 'arg2']
    #             added_vars.update(instr)
    #         elif inst_type == NodeType.Ret or inst_type == NodeType.Discard:
    #             # ['arg1', 'arg2']
    #             removed_vars.update(instr)
    #         elif inst_type == NodeType.GateCall:
    #             # [['out1', 'out2'], 'cx', ['in1', 'in2']]
    #             added_vars.update(instr[0])
    #             removed_vars.update(instr[2])
    #         temp_avs = old_avls[prec] - removed_vars
    #         temp_ovs = old_avls[prec] - removed_vars
    #         temp_avs.update(added_vars)
    #         temp_ovs.update(added_vars)
    #         temps_avs.append(temp_avs)
    #         temps_ovs.append(temp_avs)
    #
    #     if len(temps_avs) > 0:
    #         intersection = reduce(lambda x, y: x & y, temps_avs)
    #     else:
    #         intersection = set()
    #     if len(temps_ovs) > 0:
    #         union = reduce(lambda x, y: x | y, temps_avs)
    #     else:
    #         union = set()
    #     avs_vars[node] = intersection
    #     ovs_vars[node] = union
    #
