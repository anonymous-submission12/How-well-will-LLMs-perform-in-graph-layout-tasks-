import networkx as nx
import matplotlib.pyplot as plt
import os
from utils import get_graph_data_repr_by_pk
import json
from itertools import product
import numpy as np

def draw_image(graph_data, positions, image_path, pks, metric: dict):
    G = nx.Graph(graph_data)
    communities = nx.community.greedy_modularity_communities(G)

    fig = plt.figure(figsize=(20, 10))
    axes = fig.subplots()
    colors = ("tab:blue", "tab:orange", "tab:green", "tab:red", "tab:gray", "tab:purple", "tab:olive")
    for nodes, clr in zip(communities, colors):
        nx.draw_networkx_nodes(G, pos=positions, ax=axes, nodelist=nodes, node_color=clr, node_size=100)
    nx.draw_networkx_edges(G, ax=axes, pos=positions)
    axes.axis("off")
    plt.savefig(image_path, format="png", bbox_inches="tight")
    plt.close()

def unify_pos_format(pos):
    if 'positions' in pos.keys():
        pos = pos['positions']
    elif "nodes" in pos.keys():
        pos = pos["nodes"]
        if type(pos) == list:
            if "id" in pos[0].keys():
                pos = {str(ele["id"]): {"x": ele["x"], "y": ele["y"]} for ele in pos}
            else:
                pos = {str(ele["node"]): {"x": ele["x"], "y": ele["y"]} for ele in pos}
            """except KeyError as e:
                print(f"{e}, {json_path}")
                exit()"""
    elif "layout" in pos.keys():
        pos = pos["layout"]
    
    pos_arr = np.array(list(pos.values()))
    if type(pos_arr[0]) == dict:
        pos_arr = [[d['x'], d['y']] for d in pos_arr]

    return {int(node): tuple(pos_arr[i]) for i, node in enumerate(pos.keys())}

models = ["gpt-4o-2024-11-20", "deepseek-v3", "gemini-2.0-flash-001"]
p_aliases = ["Cycle", "Grid", "Path", "Star", "SBM"]
fmts = ["edge_list"]
sizes = ["exlarge", "small"]
reqs = list(range(2, 4))
allow_algs = [True, False]

p_ks = list(product(models, sizes, fmts, p_aliases, reqs, allow_algs))
communites = list(product(models, sizes, fmts, ["SBM"], [4], allow_algs))
p_ks.extend(communites)

debug = False
s_debug = "-debug" if debug else ""
virtual = False
count = 0
for p_k in p_ks:
    model, size, fmt, p_alias, q, allow_alg = p_k
    s_allow = "_algpermitted" if allow_alg else "_algretricted"
    source_dir_path = f"outputs{s_allow}{s_debug}/{model}/{size}/{p_alias}/{q}"
    metric_dir_path = f"metrics{s_allow}{s_debug}/{model}/{size}/{p_alias}/{q}"
    image_dir_path = f"images{s_allow}{s_debug}/{model}/{size}/{p_alias}/{q}"
    os.makedirs(image_dir_path, exist_ok=True)    
    for filename in os.listdir(source_dir_path):
        id = int(filename.split("_")[4])
        if filename.endswith(".txt"):                
            pks = [fmt, p_alias, size, id]
            graph_data = get_graph_data_repr_by_pk(*pks)
            json_path = os.path.join(source_dir_path, filename)
            metric_path = os.path.join(metric_dir_path, filename)
            f_name_no_suffix = filename.rsplit(".txt", maxsplit=1)[0]
            try:
                with open(json_path, "r") as f:
                    pos = json.load(f)
            except json.decoder.JSONDecodeError:
                print(f"Invalid JSON: {json_path}")
                continue
            try:
                with open(metric_path, "r") as f:
                    metric = json.load(f)
            except json.decoder.JSONDecodeError:
                print(f"Invalid JSON: {metric_path}")
                continue
            except FileNotFoundError:
                print(f"No such file: {metric_path}")
                continue
  
            count += 1
            pos = unify_pos_format(pos)
            if True in np.isnan(list(pos.values())):
                print("NAN error: posx and posy should be finite values:", filename)
                continue
            image_path = f"{image_dir_path}/{f_name_no_suffix}.png"
            try:
                draw_image(graph_data, pos, image_path, pks, metric)
            except Exception as e:
                print(filename)
                print(e, type(e), e.with_traceback())
                exit()

print("Done!")
