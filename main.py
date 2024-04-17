import networkx as nx
import matplotlib.pyplot as plt


from cfg_build import build_cfg, print_cfg
from parser import obtain_function, clean_empty_line_and_comment
from analysis import consumption_analysis, entaglement_analysis, liveness_analysis, check_dupl_over

debug = True
"""
Assunzioni:
non posso scrivere:
    if measure(bla)
ma devo usare:
    r = measure(bla)
    if r
    
devo sempre assegnare quando uso funzioni quantum, a parte discard
tutte le variabili classiche devono essere segnate come '_'
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
    res1, res2 = consumption_analysis(cfg)
    print(name, ':')
    dup, ovw = check_dupl_over(cfg, res1, res2)
    print(dup)
    print(ovw)
    print('var to uncompute %s' % res2['Exit'])
    print('---------')
    break


# consider_discard = True
# print(entaglement_analysis(g, consider_discard))
