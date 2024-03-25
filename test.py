import networkx as nx
import matplotlib.pyplot as plt

import networkx as nx
import matplotlib.pyplot as plt

# Creazione del primo grafo
G1 = nx.DiGraph()
node = '10'
# G1.add_edges_from([(1, 2), (2, 3), (3, 4)])
G1.add_node(4)
G1.add_node(4)
G1.add_node(4)
G1.add_node(4)
G1.add_node(4)
G1.add_node(4)
G1.add_node(node)
G1.add_node(node)
G1.add_edge(node, 4)

print(node == 4)
print(node == '10')
# # Creazione del secondo grafo
# G2 = nx.DiGraph()
# G2.add_edges_from([(5, 6), (6, 7), (7, 8)])
# G2.add_node(node)
# G2.add_edge(node, 8)
#
# # Unione dei due grafi
# G = nx.compose(G1, G2)
# # G = nx.relabel_nodes(G, {node: 50})
#
print(G1.nodes)
# print(G2.out_degree(node))
# print(G.out_degree(node))


# Disegno del grafo unito
nx.draw(G1, with_labels=True, node_color='lightblue', node_size=1000, font_size=12, font_weight='bold')
plt.show()
