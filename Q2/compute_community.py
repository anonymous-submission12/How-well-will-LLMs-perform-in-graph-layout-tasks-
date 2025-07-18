import networkx as nx
import numpy as np
import community as community_louvain
from scipy.spatial.distance import euclidean

def compute_community_distances(G, node_positions):
    partition = community_louvain.best_partition(G)
    
    communities = {}
    for node, comm in partition.items():
        communities.setdefault(comm, []).append(node)

    
    intra_distances = {}
    for comm, nodes in communities.items():
        if len(nodes) < 2:
            intra_distances[comm] = 0  # If only one node, distance is zero
            continue
        
        dists = [euclidean(node_positions[str(n1)], node_positions[str(n2)])
                 for i, n1 in enumerate(nodes) for n2 in nodes[i+1:]]
        intra_distances[comm] = np.mean(dists) if dists else 0
    
    inter_distances = {}
    comm_keys = list(communities.keys())
    for i, c1 in enumerate(comm_keys):
        for c2 in comm_keys[i+1:]:
            min_dist = min(
                euclidean(node_positions[str(n1)], node_positions[str(n2)])
                for n1 in communities[c1] for n2 in communities[c2]
            )
            inter_distances[(c1, c2)] = min_dist
    
    return np.mean(list(intra_distances.values())), min(inter_distances.values())