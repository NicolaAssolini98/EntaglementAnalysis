import networkx as nx

def build_cfg(root, cfg=None, prev_node=None, end_node=None):
    """
    :type end_node: str
    :type cfg: nx.DiGraph
    :type prev_node: str
    :type root: ASTNode

    return a list of couple (name fun, cfg)

    the return type change according to the root type
    """
    # # per funzioni
    # if root.type == NodeType.ProgRoot:
    #     res = []
    #     for c in root.children:
    #         g = build_cfg(c)
    #         res.append((c.val[0], g))
    #     return res

    if root.type == NodeType.FunRoot:
        graph = nx.DiGraph()
        start_node = 'Start'
        reset_count()
        graph.add_node(start_node)
        if len(root.children) > 2:
            # TODO functions case
            p_node = new_node()
            i = 1
            # g.add_edge(start_node, p_node, label=ASTNode(NodeType.Par, root.val[1]))
        else:
            i = 0
            p_node = start_node
        # the child of the 'Branch' type child of root
        for child in root.children[i].children:
            p_node = build_cfg(child, graph, p_node)
        end_node = 'End'
        graph.add_node(end_node)
        graph.add_edge(p_node, end_node, label=EdgeLabel(root.children[-1]))
        return graph

    if root.type == NodeType.IfRoot:
        if end_node is None:
            end_node = new_node()
            cfg.add_node(end_node)

        gard_val = [True, False]
        for i in range(1, len(root.children)):
            child = root.children[i]
            # As gard branch we use
            gard_node = ASTNode(NodeType.Gard, gard_val[i-1])
            gard_node.children.append(root.children[0])
            if len(child.children) > 0:
                b_node = new_node()
                cfg.add_node(b_node)
                cfg.add_edge(prev_node, b_node, label=EdgeLabel(gard_node))
                for nephew in child.children[:-1]:
                    # print(nephew)
                    b_node = build_cfg(nephew, cfg, b_node)
                build_cfg(child.children[-1], cfg, b_node, end_node)
            else:
                cfg.add_edge(prev_node, end_node, label=EdgeLabel(gard_node))

        return end_node

    # TODO da decidere se ha senso tenere i while o risolverli in if nestati all'inizio
    if root.type == NodeType.WhileRoot:
        if end_node is None:
            end_node = new_node()
            cfg.add_node(end_node)

        end_loop_node = new_node()
        cfg.add_node(end_loop_node)
        gard_node_true = ASTNode(NodeType.Gard, True)
        gard_node_true.children.append(root.children[0])
        gard_node_false = ASTNode(NodeType.Gard, False)
        gard_node_false.children.append(root.children[0])
        max_iter_node = ASTNode(NodeType.MaxIt, root.children[1])

        child = root.children[2]
        if len(child.children) > 0:
            b_node = new_node()
            cfg.add_node(b_node)
            cfg.add_edge(prev_node, b_node, label=EdgeLabel(gard_node_true))
            for nephew in child.children[:-1]:
                # print(nephew)
                b_node = build_cfg(nephew, cfg, b_node)
            build_cfg(child.children[-1], cfg, b_node, end_loop_node)
        else:
            cfg.add_edge(prev_node, end_loop_node, label=EdgeLabel(gard_node_true))

        cfg.add_edge(end_loop_node, prev_node, label=EdgeLabel(max_iter_node))
        cfg.add_edge(prev_node, end_node, label=EdgeLabel(gard_node_false))

        return end_node

    if root.type == NodeType.Assign:
        if end_node is None:
            end_node = new_node()
            cfg.add_node(end_node)
        # cfg.add_edge(prev_node, end_node, label=str(root))
        cfg.add_edge(prev_node, end_node, label=EdgeLabel(root))
        return end_node