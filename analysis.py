import copy
from enum import Enum
from functools import reduce

import networkx as nx

from cfg_build import NodeType, exit_node, start_node

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


relation = [
    (Value.Bot, Value.Z),
    (Value.Bot, Value.X),
    (Value.Bot, Value.Y),
    (Value.Bot, Value.EX),
    (Value.Bot, Value.EY),
    (Value.Z, Value.R),
    (Value.Z, Value.D),
    (Value.X, Value.R),
    (Value.X, Value.S),
    (Value.Y, Value.D),
    (Value.Y, Value.S),
    (Value.EX, Value.ES),
    (Value.EY, Value.ES),
    (Value.S, Value.Top),
    (Value.D, Value.Top),
    (Value.R, Value.Top),
    (Value.ES, Value.Top)
]
cpo = nx.DiGraph()
cpo.add_edges_from(relation)


class Ent_Abs_Dom:
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
        if s not in self.sets:
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
        return Ent_Abs_Dom(self.store.copy(), copy.deepcopy(self.sets))

    def get_set(self, var):
        set_v = [s for s in self.sets if var in s]

        if len(set_v) == 0:
            # return {var}
            return set()
        if len(set_v) > 1:
            print(self.sets)
            exit('Get set %s: Partition ill-formed', var)
        return set_v[0]

    def join(self, var1, var2):
        set_v1 = self.get_set(var1)
        set_v2 = self.get_set(var2)

        if set_v1 != set_v2:
            set_v1.update(set_v2)

            if set_v2 in self.sets:
                self.sets.remove(set_v2)

    def remove_from(self, var1, var2):
        """
        Remove var2 from the set of var2
        """
        set_v1 = self.get_set(var1)
        set_v2 = self.get_set(var2)

        if len(set_v1) > 0:
            if set_v1 == set_v2:
                self.sets.remove(set_v1)
                set_v1.discard(var2)
                if len(set_v1) > 0:
                    self.sets.append(set_v1)
                self.sets.append({var2})

    def is_disjoint(self, var1, var2):
        set_v1 = self.get_set(var1)
        set_v2 = self.get_set(var2)

        return not set_v1 == set_v2

    def disentagled_on_value(self, val, var1, var2):
        self.update_value(var2, Value.Z)
        self.remove_from(var1, var2)
        ent_set = self.get_set(var1)
        if len(ent_set) == 1:
            self.update_value(var1, val)

    def measure(self, var):
        if (self.get_store_val(var) == Value.EX or self.get_store_val(var) == Value.EY
                or self.get_store_val(var) == Value.ES):
            ent_with_var = copy.deepcopy(self.get_set(var))
            for vv in ent_with_var:
                if vv != var:
                    # in this case al variables collapse to Value.Z
                    if (self.get_store_val(vv) == Value.EX or self.get_store_val(vv) == Value.EY
                            or self.get_store_val(vv) == Value.ES):
                        self.update_value(vv, Value.Z)
                        self.remove_from(var, vv)

        self.remove_from(var, var)
        self.update_value(var, Value.Z)

    def set_entagled_on_value(self, val, var1, var2):
        self.update_value(var1, val)
        self.update_value(var2, val)
        self.join(var1, var2)

    def __str__(self):
        return "store: %s\n sets:%s\n" % (str(self.store), str(self.sets))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, Ent_Abs_Dom):
            return self.store == other.store and self.sets == other.sets
        return False

    def __lt__(self, other):
        return True

    def __gt__(self, other):
        return False


def consumption_analysis(cfg):
    # used for checking consumption
    avs_vars = {node: set() for node in cfg.nodes()}
    # used for checking overwriting
    ovs_vars = {node: set() for node in cfg.nodes()}

    fixpoint = False
    while not fixpoint:
        old_avs = {node: avs_vars[node].copy() for node in avs_vars.keys()}
        old_ovs = {node: ovs_vars[node].copy() for node in ovs_vars.keys()}
        for node in cfg.nodes():
            temps_avs, temps_ovs = [], []
            predecessors = list(cfg.predecessors(node))
            for pred in predecessors:
                added_vars = set()
                removed_vars = set()
                label = cfg[pred][node]["label"]
                inst_type = label.type
                instr = label.value
                if inst_type == NodeType.Args or inst_type == NodeType.Init:
                    # ['arg1', 'arg2']
                    added_vars.update(instr)
                elif inst_type == NodeType.Ret or inst_type == NodeType.Discard or inst_type == NodeType.Measure:
                    # ['arg1', 'arg2']
                    removed_vars.update(instr)
                elif inst_type == NodeType.GateCall:
                    # [['out1', 'out2'], 'cx', ['in1', 'in2']]
                    added_vars.update(instr[0])
                    removed_vars.update(instr[2])
                temp_avs = old_avs[pred] - removed_vars
                temp_ovs = old_avs[pred] - removed_vars
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

        fixpoint = (old_avs == avs_vars) and (old_ovs == ovs_vars)

    for edge in cfg.edges:
        label = cfg[edge[0]][edge[1]]["label"]
        inst_type = label.type
        instr = label.value
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


def lub_2_pairs(pair1, pair2):
    safe_intersection = pair1[0] & pair2[0]
    unsafe_union = pair1[1] | pair2[1] | (pair1[0] ^ pair2[0])

    return safe_intersection, unsafe_union


def liveness_analysis(cfg):
    pairs = {node: None for node in cfg.nodes()}
    pairs[exit_node] = (set(), set())

    fixpoint = False
    while not fixpoint:
        print(pairs)
        old_pairs = {node: copy.deepcopy(pairs[node]) if pairs[node] is not None else None for node in pairs.keys()}
        for node in list(cfg.nodes()):
            temps_pairs = []
            successors = list(cfg.successors(node))
            for suc in successors:
                added_vars = set()
                removed_vars = set()
                label = cfg[node][suc]["label"]
                inst_type = label.type
                instr = label.value
                if inst_type == NodeType.Args or inst_type == NodeType.Init:
                    # ['arg1', 'arg2']
                    removed_vars.update(instr)
                elif inst_type == NodeType.Ret or inst_type == NodeType.Discard or inst_type == NodeType.Measure:
                    # ['arg1', 'arg2']
                    added_vars.update(instr)
                elif inst_type == NodeType.GateCall:
                    # [['out1', 'out2'], 'cx', ['in1', 'in2']]
                    added_vars.update(instr[2])
                    removed_vars.update(instr[0])

                if old_pairs[suc] is not None:
                    temp_safe = old_pairs[suc][0] - removed_vars
                    temp_unsafe = old_pairs[suc][1] - removed_vars
                    temp_safe.update(added_vars)
                    temps_pairs.append((temp_safe, temp_unsafe))

            if len(temps_pairs) > 0:
                lub = reduce(lambda x, y: lub_2_pairs(x, y), temps_pairs)
            elif len(successors) == 0:
                lub = old_pairs[node]
            else:
                lub = None
            pairs[node] = lub

        fixpoint = (old_pairs == pairs)

    return pairs


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
    elif fun == 'rx':
        if val1 == Value.X or val1 == Value.Bot:
            return val1
        else:
            return Value.Top
    elif fun == 'rz':
        if val1 == Value.Z or val1 == Value.Bot:
            return val1
        else:
            return Value.Top

    return Value.Top


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
            pass
        elif (v_c == Value.X or v_c == Value.EX) and v_t == Value.Z and abs_dom.is_disjoint(ctrl, targ):
            abs_dom.set_entagled_on_value(Value.EX, ctrl, targ)
        elif (v_c == Value.Y or v_c == Value.EY) and v_t == Value.Z and abs_dom.is_disjoint(ctrl, targ):
            abs_dom.set_entagled_on_value(Value.EY, ctrl, targ)
        elif (v_c == Value.S or v_c == Value.ES) and v_t == Value.Z and abs_dom.is_disjoint(ctrl, targ):
            abs_dom.set_entagled_on_value(Value.ES, ctrl, targ)
        elif v_c == Value.EX and v_t == v_c and not abs_dom.is_disjoint(ctrl, targ):
            abs_dom.disentagled_on_value(Value.X, ctrl, targ)
        elif v_c == Value.EY and v_t == v_c and not abs_dom.is_disjoint(ctrl, targ):
            abs_dom.disentagled_on_value(Value.Y, ctrl, targ)
        elif v_c == Value.ES and v_t == v_c and not abs_dom.is_disjoint(ctrl, targ):
            abs_dom.disentagled_on_value(Value.S, ctrl, targ)
        elif v_t == Value.Top and not abs_dom.is_disjoint(ctrl, targ):
            pass
        else:
            abs_dom.set_entagled_on_value(Value.Top, ctrl, targ)

        return abs_dom

    if fun == 'cz':
        abs_dom = abs_semantics('h', abs_dom, in_vars[1:])
        abs_dom = abs_semantics('cx', abs_dom, in_vars)
        return abs_semantics('h', abs_dom, in_vars[1:])


def merge_sets_with_common_elements(list_of_sets):
    # Set to store the merged sets
    fixpoint = False
    while not fixpoint:
        old_sets = copy.deepcopy(list_of_sets)
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


        fixpoint = (merged_sets == old_sets)
        list_of_sets = merged_sets
    return list_of_sets


def elements_from_sets(list_of_sets):
    # Initialize an empty set to store unique elements
    unique_elements = set()

    # Iterate through each set in the list
    for s in list_of_sets:
        # Add the elements of the current set to the set of unique elements
        unique_elements.update(s)

    # Convert the set of unique elements to a list and return it
    return unique_elements


def lub_store_values(val1, val2):
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
            neighbors1 = list(cpo.neighbors(current_node1))
            for neighbor in neighbors1:
                if neighbor not in visited1:
                    queue1.append(neighbor)
        if queue2:
            current_node2 = queue2.pop(0)
            visited2.add(current_node2)
            neighbors2 = list(cpo.neighbors(current_node2))
            for neighbor in neighbors2:
                if neighbor not in visited2:
                    queue2.append(neighbor)

        intersection = visited1 & visited2
        if intersection:
            return intersection.pop()

    return None


def join_2_abs_doms(abs1, abs2):
    """
    :type abs1: Ent_Abs_Dom
    :type abs2: Ent_Abs_Dom
    :return:  Pair()
    """
    if abs1 == abs2:
        return abs1

    join_sets = merge_sets_with_common_elements(copy.deepcopy(abs1.sets) + copy.deepcopy(abs2.sets))

    all_vars = elements_from_sets(join_sets)
    join_store = dict()
    for var in all_vars:
        if (abs1.get_set(var) == abs2.get_set(var) or abs1.get_store_val(var) == Value.Bot
                or abs2.get_store_val(var) == Value.Bot):
            join_store[var] = lub_store_values(abs1.get_store_val(var), abs2.get_store_val(var))
        else:
            join_store[var] = Value.Top

    join_pair = Ent_Abs_Dom(join_store, join_sets)

    return join_pair


def entaglement_analysis(cfg, consider_discard=False):
    abs_doms = {node: Ent_Abs_Dom() for node in cfg.nodes()}

    fixpoint = False
    while not fixpoint:
        old_doms = {node: abs_doms[node].copy() for node in abs_doms.keys()}
        for node in cfg.nodes():
            temps_pairs = []
            predecessors = list(cfg.predecessors(node))
            for prec in predecessors:
                label = cfg[prec][node]["label"]
                temp = abs_doms[prec].copy()
                inst_type = label.type
                instr = label.value
                if inst_type == NodeType.Init:
                    # ['arg1', 'arg2']
                    for v in instr:
                        temp.add(v, Value.Z)
                elif inst_type == NodeType.Measure:
                    # ['arg1', 'arg2']
                    for v in instr:
                        temp.measure(v)
                elif inst_type == NodeType.GateCall:
                    # [['out1', 'out2'], 'cx', ['in1', 'in2']]
                    temp = abs_semantics(instr[1], temp, instr[2])
                    for i in range(len(instr[2])):
                        temp.rename(instr[2][i], instr[0][i])
                elif inst_type == NodeType.Discard:
                    # ['arg1', 'arg2']
                    # TODO serve o non serve analizzarla???
                    if consider_discard:
                        for v in instr:
                            temp.update_value(v, Value.Bot)
                            temp.remove_from(v, v)
                temps_pairs.append(temp)

            if len(temps_pairs) > 0:
                join = reduce(lambda x, y: join_2_abs_doms(x, y), temps_pairs)
            else:
                join = Ent_Abs_Dom()

            abs_doms[node] = join
        print(str(abs_doms) + '\n-----')

        fixpoint = (old_doms == abs_doms)

    return abs_doms
