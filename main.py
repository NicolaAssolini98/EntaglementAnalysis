import networkx as nx
import matplotlib.pyplot as plt

from cfg_build import build_cfg, print_cfg
from parser import obtain_function, clean_empty_line_and_comment
from analysis import (consumption_analysis, entaglement_analysis, liveness_analysis, check_dupl_over,
                      insert_uncomputation, insert_discard)

debug = True
"""
Assunzioni:
non posso scrivere:
    if measure(bla):
ma devo usare:
    r = measure(bla)
    if r:
    

niente funzioni in line
non posso scrivere:
    q = h(qubit())
o
    p = h(x(q))
    
invece devo scrivere:
    t = qubit()
    q = h(t)
o
    t = x(q)    
    p = h(t)    
    
   
    
devo sempre assegnare quando uso funzioni quantum, a parte discard
tutte le variabili classiche devono essere segnate come '_', così da essere ignorate dall'analisi
considero un cfg semplificato, quindi niente break o continue
"""

file_path = 'txt_files/test_2'
# file_path = 'txt_files/test_entangled'
tag = '@guppy'
groups = obtain_function(file_path)
# for group in groups:
#     print('----')
#     print(group)


for group in groups:
    code = clean_empty_line_and_comment(group)
    # print(code)
    name, cfg = build_cfg(code)
    print_cfg(cfg)
    inter, union = consumption_analysis(cfg)
    print(name, ':')
    # print('I: ', inter)
    # print('U: ', union)
    dup_tuples, over_tuples = check_dupl_over(cfg, inter, union)
    if len(dup_tuples) == 0:
        pairs = liveness_analysis(cfg)
        # if len(over_tuples) == 0:
        # var_to_unc = union['Exit']
        # print('var to uncompute %s' % var_to_unc)
        print(pairs)
        uncomputation = insert_uncomputation(cfg, pairs)
        print(uncomputation)
        # print('---------')
        # else:
        #     print('Variable overwriting')
        #     print('overwritten variables: %s' % over_tuples)
        #     overwritten_vars = set()
        #     for over_tuple in over_tuples:
        #         overwritten_vars.update(over_tuple[2])
        #     print(insert_discard(cfg, pairs, overwritten_vars))
    else:
        print('ERROR, used not defined/consumed variable')
        print('not defined/consumed used vars: %s' % dup_tuples)

    print('----------------')
    break



# consider_discard = True
# print(entaglement_analysis(g, consider_discard))
