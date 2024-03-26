import networkx as nx
import matplotlib.pyplot as plt


from cfg_build import build_cfg, clean_empty_line
from parser import obtain_function
from analysis import consumption_analysis, entaglement_analysis


def print_cfg(cfg):
    pos = nx.spring_layout(cfg)
    labels = nx.get_edge_attributes(cfg, 'label')
    nx.draw(cfg, pos, with_labels=True, node_size=300, node_color="lightblue", font_size=8, font_color="black",
            font_weight="bold", arrows=True)
    nx.draw_networkx_edge_labels(cfg, pos, edge_labels=labels, font_size=7)
    plt.title("Control Flow Graph with Edge Labels")
    plt.show()


file_path = 'txt_files/test'
tag = '@guppy'
groups = obtain_function(file_path)
# for group in groups:
#     print('----')
#     print(group)


g = build_cfg(clean_empty_line(groups[0]))
# print(type(g))
print_cfg(g)
# res1, res2 = consumption_analysis(g)

# print(res1)
# print(res2)

print(entaglement_analysis(g))