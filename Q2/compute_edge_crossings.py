import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations

def cross_product(x1, y1, x2, y2, x3, y3):
    return (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)

def is_overlapping(x1, y1, x2, y2, x3, y3, x4, y4):
    if cross_product(x1, y1, x2, y2, x3, y3) != 0 or cross_product(x1, y1, x2, y2, x4, y4) != 0:
        return False

    x_overlap = max(min(x1, x2), min(x3, x4)) < min(max(x1, x2), max(x3, x4))
    y_overlap = max(min(y1, y2), min(y3, y4)) < min(max(y1, y2), max(y3, y4))

    return x_overlap and y_overlap

def is_intersecting(x1, y1, x2, y2, x3, y3, x4, y4):
    shared_endpoint = (x1, y1) == (x3, y3) or (x1, y1) == (x4, y4) or \
                      (x2, y2) == (x3, y3) or (x2, y2) == (x4, y4)

    if shared_endpoint:
        return is_overlapping(x1, y1, x2, y2, x3, y3, x4, y4)

    d1 = cross_product(x1, y1, x2, y2, x3, y3) * cross_product(x1, y1, x2, y2, x4, y4)
    d2 = cross_product(x3, y3, x4, y4, x1, y1) * cross_product(x3, y3, x4, y4, x2, y2)

    if d1 < 0 and d2 < 0:
        return True

    return is_overlapping(x1, y1, x2, y2, x3, y3, x4, y4)

def count_edge_crossings(G, pos):
    edges = list(G.edges())
    crossing_count = 0

    for (u1, v1), (u2, v2) in combinations(edges, 2):
        x1, y1 = pos[str(u1)]
        x2, y2 = pos[str(v1)]
        x3, y3 = pos[str(u2)]
        x4, y4 = pos[str(v2)]

        if is_intersecting(x1, y1, x2, y2, x3, y3, x4, y4):
            crossing_count += 1

    return crossing_count