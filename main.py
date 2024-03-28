import networkx as nx
import matplotlib.pyplot as plt


from cfg_build import build_cfg, clean_empty_line, print_cfg
from parser import obtain_function
from analysis import consumption_analysis, entaglement_analysis

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


# TODO aggiungi rz, rx



file_path = 'txt_files/test'
tag = '@guppy'
groups = obtain_function(file_path)
# for group in groups:
#     print('----')
#     print(group)


g = build_cfg(clean_empty_line(groups[0]))
# print(type(g))
# print_cfg(g)
# res1, res2 = consumption_analysis(g)

# print(res1)
# print(res2)
consider_discard = True
print(entaglement_analysis(g, consider_discard))
