import numpy as np
import networkx as nx

def compute_full_stress(graph, pos):
    shortest_paths = dict(nx.all_pairs_shortest_path_length(graph))
    full_stress = 0

    nodes = list(graph.nodes())
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            u, v = nodes[i], nodes[j]

            if shortest_paths[u][v] == 0:
                continue

            euclidean_dist = np.linalg.norm(np.array(pos[str(u)]) - np.array(pos[str(v)]))
            graph_dist = shortest_paths[u][v]

            stress_contrib = ((euclidean_dist / graph_dist) - 1) ** 2
            full_stress += stress_contrib

    return round(full_stress, 2)