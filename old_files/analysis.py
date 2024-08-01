import copy
from enum import Enum
from functools import reduce

import networkx as nx

from cfg_build_old import NodeType, exit_node

# To disable debug print in this file
debug = True


def disable_print(*args, **kwargs):
    pass


if not debug:
    print = disable_print


class Value(Enum):
    Bot = 1
    Z = 2
    X = 3
    Y = 4
    XY = 5
    YZ = 6
    XZ = 7
    S = 8
    Top = 9


relation = [
    (Value.Bot, Value.Z),
    (Value.Bot, Value.X),
    (Value.Bot, Value.Y),
    (Value.Z, Value.XZ),
    (Value.Z, Value.YZ),
    (Value.X, Value.XY),
    (Value.X, Value.XZ),
    (Value.Y, Value.XY),
    (Value.Y, Value.YZ),
    (Value.XY, Value.S),
    (Value.S, Value.Top),
    (Value.XZ, Value.Top),
    (Value.YZ, Value.Top)
]
cpo = nx.DiGraph()
cpo.add_edges_from(relation)


class EntAbsDom:
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

    def update_value_set(self, key, value):
        for v in self.get_set(key):
            if self.store[v] != Value.Top:
                self.store[v] = value
        # self.part.add(key)

    def rename(self, old_name, new_name):
        if old_name in self.store:
            self.store[new_name] = self.store.pop(old_name)
        for s in self.sets:
            if old_name in s:
                s.remove(old_name)
                s.add(new_name)

    def copy(self):
        return EntAbsDom(self.store.copy(), copy.deepcopy(self.sets))

    def get_set(self, var):
        set_v = [s for s in self.sets if var in s]

        if len(set_v) == 0:
            # return {var}
            return set()
        if len(set_v) > 1:
            print(self.sets)
            exit('Get set from \'%s\': Partition ill-formed' % var)
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
        Remove var2 from the set of var1
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

    def delete_var(self, var):
        """
        Delete var from the set of sets
        """
        if var in self.store:
            del self.store[var]

        set_v = self.get_set(var)

        if len(set_v) > 0:
            self.sets.remove(set_v)
            set_v.discard(var)
            if len(set_v) > 0:
                self.sets.append(set_v)

    def is_disjoint(self, var1, var2):
        set_v1 = self.get_set(var1)
        set_v2 = self.get_set(var2)

        return not set_v1 == set_v2

    def disentagled(self, var1, var2):
        self.update_value(var2, Value.Z)
        self.remove_from(var1, var2)

    def set_entagled_on_value(self, val, var1, var2):
        # self.update_value(var1, val)
        self.update_value(var2, val)
        self.join(var1, var2)

    def __str__(self):
        return "\n\t store: %s\n\t sets:%s\n" % (str(self.store), str(self.sets))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, EntAbsDom):
            return self.store == other.store and self.sets == other.sets
        return False

    def __lt__(self, other):
        return True

    def __gt__(self, other):
        return False


def get_all_vars(cfg):
    # used for checking consumption
    all_vars = set()
    # Iterazione su tutti gli archi del grafo e stampa delle etichette
    for _, _, data in cfg.edges(data=True):
        label = data['label']
        inst_type = label.type
        instr = label.value
        if (inst_type == NodeType.Args or inst_type == NodeType.Init or inst_type == NodeType.Ret or
                inst_type == NodeType.Discard or inst_type == NodeType.Measure):
            # ['arg1', 'arg2']
            all_vars.update(instr)
        elif inst_type == NodeType.GateCall:
            # [['out1', 'out2'], 'cx', ['in1', 'in2']]
            all_vars.update(instr[0])
            all_vars.update(instr[2])

    return all_vars


def consumption_analysis(cfg):
    # used for checking consumption
    all_vars = get_all_vars(cfg)
    avs_inter = {node: all_vars for node in cfg.nodes()}
    # used for checking overwriting
    avs_union = {node: set() for node in cfg.nodes()}

    get_all_vars(cfg)
    fixpoint = False
    while not fixpoint:
        old_int = {node: avs_inter[node].copy() for node in avs_inter.keys()}
        old_unn = {node: avs_union[node].copy() for node in avs_union.keys()}
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
                temp_avs = old_int[pred] - removed_vars
                temp_ovs = old_unn[pred] - removed_vars
                temp_avs.update(added_vars)
                temp_ovs.update(added_vars)
                temps_avs.append(temp_avs)
                temps_ovs.append(temp_ovs)

            if len(temps_avs) > 0:
                intersection = reduce(lambda x, y: x & y, temps_avs)
            else:
                intersection = set()
            if len(temps_ovs) > 0:
                union = reduce(lambda x, y: x | y, temps_ovs)
            else:
                union = set()
            avs_inter[node] = intersection
            avs_union[node] = union

        fixpoint = (old_int == avs_inter) and (old_unn == avs_union)

    return avs_inter, avs_union


def check_dupl_over(cfg, avs_vars, ovs_vars):
    '''
    returns two list of triple:
    (node, edge, variable) thats indicates the node in which we find the error, the edge (i.e. the instruction) that
    generates it, and the variables that are overwritted/used after consumpion
    '''
    duplication = []
    overwriting = []
    for edge in cfg.edges:
        label = cfg[edge[0]][edge[1]]["label"]
        inst_type = label.type
        instr = label.value
        if inst_type == NodeType.Ret or inst_type == NodeType.Discard:
            # ['arg1', 'arg2']
            if not (set(instr) <= avs_vars[edge[0]]):
                cons_vars = set(instr).difference(avs_vars[edge[0]])
                duplication.append((edge[0], edge, cons_vars))
                print('Instr %s at node %s used %s after consumption' % (instr, edge[0], cons_vars))
        elif inst_type == NodeType.GateCall:
            # [['out1', 'out2'], 'g', ['in1', 'in2']]
            if not (set(instr[2]) <= avs_vars[edge[0]]):
                cons_vars = set(instr[2]).difference(avs_vars[edge[0]])
                duplication.append((edge[0], edge, cons_vars))
                print('Instr %s at node %s used %s after consumption' % (instr, edge[0], cons_vars))
            # if a variable is in instr[2] and in instr[0] is ok (we consume and then redefine it)

            not_cons = set(instr[0]) - set(instr[2])
            if not not_cons.isdisjoint(ovs_vars[edge[0]]):
                ovw_vars = ovs_vars[edge[0]] & not_cons
                overwriting.append((edge[0], edge, ovw_vars))
                print('Instr %s at node %s overwrite these %s variables' % (instr, edge[0], ovw_vars))
        elif inst_type == NodeType.Init:
            # ['arg1', 'arg2']
            if not set(instr).isdisjoint(ovs_vars[edge[0]]):
                ovw_vars = ovs_vars[edge[0]] & set(instr)
                overwriting.append((edge[0], edge, ovw_vars))
                print('Instr %s at node %s overwrite these %s variables' % (instr, edge[0], ovw_vars))

    return duplication, overwriting


def lub_2_pairs(pair1, pair2):
    safe_intersection = pair1[0] & pair2[0]
    unsafe_union = pair1[1] | pair2[1] | (pair1[0] ^ pair2[0])

    return safe_intersection, unsafe_union


def liveness_analysis(cfg):
    # (safe, unsafe)
    pairs = {node: None for node in cfg.nodes()}
    pairs[exit_node] = (set(), set())

    fixpoint = False
    while not fixpoint:
        #print(pairs)
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


def get_all_definition(cfg, var):
    # used for checking consumption
    def_edges = set()
    for u, v, data in cfg.edges(data=True):
        label = data['label']
        inst_type = label.type
        instr = label.value
        if inst_type == NodeType.Init or inst_type == NodeType.Args:
            # ['arg1', 'arg2']
            if var in instr:
                def_edges.add((u, v))
        elif inst_type == NodeType.GateCall:
            # [['out1', 'out2'], 'cx', ['in1', 'in2']]
            if var in instr[0]:
                def_edges.add((u, v))

    return def_edges


def insert_uncomputation(cfg, pairs):
    """
    :param cfg:
    :param pairs: (S,U) for each node
    :param vars_to_uncompute: list of variable to uncompute

    return a list couples, containing the edges in which we have to uncompute variables,
     and the variable that we need to uncompute
    """
    uncompute_position = []
    all_unsafe = set()
    for node in cfg.nodes():
        all_unsafe.update(pairs[node][1])

    for var in get_all_vars(cfg):
        for u, v in get_all_definition(cfg, var):
            if var not in pairs[v][0] and var not in pairs[v][1]:
                uncompute_position.append(((u, v), var))



    for var in all_unsafe:
        for node in cfg.nodes():
            # we consider the node only where var in unsafe
            if var in pairs[node][1]:
                for v in cfg.successors(node):
                    if var not in pairs[v][0] and var not in pairs[v][1]:
                        uncompute_position.append(((node, v), var))

    return uncompute_position


def insert_discard(cfg, pairs, vars_overwritten):
    """
    :param cfg:
    :param pairs: (S,U) for each node
    :param vars_overwritten: list of variable that are overwritten

    """
    discard_position = []
    for var in vars_overwritten:
        print(var)
        for u, v in get_all_definition(cfg, var):
            if var in pairs[v][0]:
                pass
            elif var in pairs[v][1]:
                for n in cfg.successors(v):
                    if var not in pairs[n][0] and var not in pairs[n][1]:
                        discard_position.append(((v, n), var))
            else:
                discard_position.append(((u, v), var))

    return discard_position


def abs_semantics(fun, abs_dom, in_vars):
    val1 = abs_dom.get_store_val(in_vars[0])

    if fun == 'x' or fun == 'y' or fun == 'z':
        pass  # abs_dom.update_value(in_vars[0], val1)

    elif fun == 'h':
        if len(abs_dom.get_set(in_vars[0])) == 1:
            if val1 == Value.Bot or val1 == Value.Y or val1 == Value.XZ:
                pass  # abs_dom.update_value(in_vars[0], val1)
            elif val1 == Value.Z:
                abs_dom.update_value(in_vars[0], Value.X)
            elif val1 == Value.X:
                abs_dom.update_value(in_vars[0], Value.Z)
            elif val1 == Value.XY:
                abs_dom.update_value(in_vars[0], Value.YZ)
            elif val1 == Value.YZ:
                abs_dom.update_value(in_vars[0], Value.XY)
            else:
                abs_dom.update_value(in_vars[0], Value.Top)
        else:
            if val1 == Value.Bot:
                pass  # abs_dom.update_value(in_vars[0], val1)
            else:
                abs_dom.update_value(in_vars[0], Value.Top)

    elif fun == 's' or fun == 'sdg':
        if val1 == Value.Z or val1 == Value.XY or val1 == Value.S or val1 == Value.Bot:
            pass  # abs_dom.update_value(in_vars[0], val1)
        elif val1 == Value.Y:
            abs_dom.update_value_set(in_vars[0], Value.X)
        elif val1 == Value.X:
            abs_dom.update_value_set(in_vars[0], Value.Y)
        elif val1 == Value.YZ:
            abs_dom.update_value_set(in_vars[0], Value.XZ)
        elif val1 == Value.XZ:
            abs_dom.update_value_set(in_vars[0], Value.YZ)
        else:
            abs_dom.update_value(in_vars[0], Value.Top)

    elif fun == 't' or fun == 'tdg':
        if val1 == Value.Z or val1 == Value.S or val1 == Value.Bot:
            pass  # abs_dom.update_value(in_vars[0], val1)
        elif val1 == Value.X or val1 == Value.Y:
            abs_dom.update_value_set(in_vars[0], Value.S)
        else:
            abs_dom.update_value(in_vars[0], Value.Top)

    elif fun == 'rx':
        if len(abs_dom.get_set(in_vars[0])) == 1 and (val1 == Value.X or val1 == Value.Bot):
            pass  # abs_dom.update_value(in_vars[0], val1)
        else:
            abs_dom.update_value(in_vars[0], Value.Top)

    elif fun == 'rz':
        if val1 == Value.Z or val1 == Value.Bot or val1 == Value.S:
            pass  # abs_dom.update_value(in_vars[0], val1)
        if val1 == Value.X or val1 == Value.Y or val1 == Value.XY:
            abs_dom.update_value(in_vars[0], Value.S)
        else:
            abs_dom.update_value(in_vars[0], Value.Top)

    elif fun == 'cx':
        ctrl = in_vars[0]
        targ = in_vars[1]
        v_c = abs_dom.get_store_val(ctrl)
        v_t = abs_dom.get_store_val(targ)
        if len(abs_dom.get_set(targ)) == 1:
            if v_c == Value.Z or v_t == Value.X or v_c == Value.Bot or v_t == Value.Bot:
                pass
            elif (v_c == Value.X or v_c == Value.Y or v_c == Value.S) and v_t == Value.Z:
                abs_dom.set_entagled_on_value(v_c, ctrl, targ)
            else:
                abs_dom.set_entagled_on_value(Value.Top, ctrl, targ)

        elif len(abs_dom.get_set(targ)) > 1:
            if (v_c == Value.Z or v_c == Value.Bot or v_t == Value.Bot) and abs_dom.is_disjoint(ctrl, targ):
                pass
            elif abs_dom.is_disjoint(ctrl, targ):
                abs_dom.set_entagled_on_value(Value.Top, ctrl, targ)
                abs_dom.update_value_set(ctrl, Value.Top)
            elif not abs_dom.is_disjoint(ctrl, targ):
                if ((v_c == Value.X or v_c == Value.Y or v_c == Value.S) and
                        (v_t == Value.X or v_t == Value.Y or v_t == Value.S)):
                    abs_dom.disentagled(ctrl, targ)
                else:
                    abs_dom.update_value(ctrl, Value.Top)
                    abs_dom.update_value(targ, Value.Top)

    elif fun == 'cz':
        ctrl = in_vars[0]
        targ = in_vars[1]
        v_c = abs_dom.get_store_val(ctrl)
        v_t = abs_dom.get_store_val(targ)
        if v_c == Value.Z or v_c == Value.Z or v_c == Value.Bot or v_t == Value.Bot:
            # redundant, if value(q) = Z then len(abs_dom.get_set(q) = 1
            # and (len(abs_dom.get_set(targ)) == 1 or len(abs_dom.get_set(ctrl)) == 1)):
            pass
        else:
            abs_dom = abs_semantics('h', abs_dom, in_vars[1:])
            abs_dom = abs_semantics('cx', abs_dom, in_vars)
            abs_dom = abs_semantics('h', abs_dom, in_vars[1:])


    elif fun == 'measure':
        for var in in_vars:
            var_val = abs_dom.get_store_val(var)
            if var_val == Value.X or var_val == Value.Y or var_val == Value.XY or var_val == Value.S:
                ent_with_var = copy.deepcopy(abs_dom.get_set(var))
                for vv in ent_with_var:
                    if vv != var:
                        # in this case al variables collapse to Value.Z
                        if abs_dom.get_store_val(vv) == var_val:
                            abs_dom.update_value(vv, Value.Z)
                            abs_dom.remove_from(var, vv)
            if var_val == Value.Top:
                ent_with_var = copy.deepcopy(abs_dom.get_set(var))
                for vv in ent_with_var:
                    if vv != var:
                        abs_dom.update_value(vv, Value.Top)

            abs_dom.delete_var(var)

    return abs_dom


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
    :type abs1: EntAbsDom
    :type abs2: EntAbsDom
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

    join_pair = EntAbsDom(join_store, join_sets)

    return join_pair


def entaglement_analysis(cfg):
    abs_doms = {node: EntAbsDom() for node in cfg.nodes()}

    fixpoint = False
    while not fixpoint:
        old_doms = {node: abs_doms[node].copy() for node in abs_doms.keys()}
        for node in cfg.nodes():
            print('-------')
            print(str(node), '\n')
            temps_pairs = []
            predecessors = list(cfg.predecessors(node))
            for pred in predecessors:
                label = cfg[pred][node]["label"]
                temp = abs_doms[pred].copy()
                inst_type = label.type
                instr = label.value
                if inst_type == NodeType.Init:
                    # ['arg1', 'arg2']
                    for v in instr:
                        temp.add(v, Value.Z)
                elif inst_type == NodeType.Measure:
                    # ['arg1', 'arg2']
                    temp = abs_semantics('measure', temp, instr)
                elif inst_type == NodeType.GateCall:
                    # [['out1', 'out2'], 'g', ['in1', 'in2']]
                    temp = abs_semantics(instr[1], temp, instr[2])
                    for i in range(len(instr[2])):
                        temp.rename(instr[2][i], instr[0][i])
                elif inst_type == NodeType.Discard:
                    # ['arg1', 'arg2']
                    for v in instr:
                        temp.delete_var(v)

                temps_pairs.append(temp)

            if len(temps_pairs) > 0:
                join = reduce(lambda x, y: join_2_abs_doms(x, y), temps_pairs)
            else:
                join = EntAbsDom()
            print(join)
            print('-------')
            abs_doms[node] = join
        print(str(abs_doms) + '\n@@@@')

        fixpoint = (old_doms == abs_doms)

    return abs_doms
