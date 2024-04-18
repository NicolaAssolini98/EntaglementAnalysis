import networkx as nx
import matplotlib.pyplot as plt


from cfg_build import build_cfg, print_cfg
from parser import obtain_function, clean_empty_line_and_comment
from analysis import consumption_analysis, entaglement_analysis, liveness_analysis, check_dupl_over

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


file_path = 'txt_files/test_live'
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
    print('I: ', inter)
    print('U: ', union)
    dup, ovw = check_dupl_over(cfg, inter, union)
    if len(dup) == 0:
        print('overwriting of variable: %s' % ovw)
        print('var to uncompute %s' % union['Exit'])
        live_vars = liveness_analysis(cfg)
        print(live_vars)
        print('---------')
    else:
        print('used of consumed vars: %s' % dup)
    break


# consider_discard = True
# print(entaglement_analysis(g, consider_discard))
