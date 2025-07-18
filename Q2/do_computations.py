from compute_stress import compute_full_stress
from compute_edge_crossings import count_edge_crossings
from utils import get_graph_data_repr_by_pk, CustomError
import networkx as nx
import json
import os
import numpy as np
from itertools import product
from compute_community import compute_community_distances
import warnings
warnings.filterwarnings("error")

def do_compute(json_path, pks, q, virtual=False):

    graph_data = get_graph_data_repr_by_pk(*pks)

    try:
        with open(json_path, "r") as f:
            pos = json.load(f)
    except json.decoder.JSONDecodeError:
        with open(json_path, "r") as f:
            lines = f.readlines()
        if len(lines) == 0:
            print("None JSON JSON", json_path)
        else:
            if "ModuleNotFoundError" in lines[-1]:
                print("ModuleNotFoundError", json_path)
        return False
    
    G = nx.Graph(graph_data)

    output_file = os.path.join(metric_dir_path, os.path.basename(json_path))

    try:
        pos = rescale_positions(pos, 1, json_path)
    except CustomError as e:
        print(e, json_path)
        return False

    if pos == None:
        print("None answer", json_path)
        return False

    if True in np.isnan(list(pos.values())):
        print("NAN error: posx and posy should be finite values:", json_path)
        return False

    try:
        stress = compute_full_stress(G, pos)
        crossings = count_edge_crossings(G, pos)
        if p_alias == "SBM":
            intra, inter = compute_community_distances(G, pos)
        d = {}
        if q == 3:
            d["crossings"] = crossings
        elif q == 2:
            d["stress"] = stress
        if p_alias == "SBM" and q == 4:
            d["intra"] = intra
            d["inter"] = inter
        if virtual:
            j = json.dumps(d)
        else:
            with open(output_file, "w") as f:
                json.dump(d, f)
    except KeyError or ValueError as e:
        return False

    global COUNT
    COUNT +=1
    return True

def rescale_positions(pos, new_scale=1, json_path=None):
    if 'positions' in pos.keys():
        pos = pos['positions']
    elif "nodes" in pos.keys():
        pos = pos["nodes"]
        if type(pos) == list:
            if "id" in pos[0].keys():
                pos = {str(ele["id"]): {"x": ele["x"], "y": ele["y"]} for ele in pos}
            else:
                pos = {str(ele["node"]): {"x": ele["x"], "y": ele["y"]} for ele in pos}
    elif "layout" in pos.keys():
        pos = pos["layout"]
    
    pos_arr = np.array(list(pos.values()))
    if len(pos_arr) == 0:
        return None
    if type(pos_arr[0]) == dict:
        try:
            pos_arr = [[d['x'], d['y']] for d in pos_arr]
        except KeyError as e:
            print(f"{e}, {json_path}")
            exit()
    center = np.mean(pos_arr, axis=0)
    pos_arr = pos_arr - center
    #print(pos_arr)
    max_dist = np.max(np.linalg.norm(pos_arr, axis=1))
    try:
        scale_factor = new_scale / max_dist
    except RuntimeWarning as e:
        raise CustomError(e)
    pos_arr *= scale_factor
    pos_arr = pos_arr + center

    return {node: tuple(pos_arr[i]) for i, node in enumerate(pos.keys())}

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
COUNT = 0
for p_k in p_ks:
    model, size, fmt, p_alias, q, allow_alg = p_k
    s_allow = "_algpermitted" if allow_alg else "_algrestricted"
    source_dir_path = f"outputs{s_allow}{s_debug}/{model}/{size}/{p_alias}/{q}"
    metric_dir_path = f"metrics{s_allow}{s_debug}/{model}/{size}/{p_alias}/{q}"
    os.makedirs(metric_dir_path, exist_ok=True)
    # Process all Python scripts in the directory
    for filename in os.listdir(source_dir_path):
        id = int(filename.split("_")[4])
        pks = [fmt, p_alias, size, id]
        if filename.endswith(".txt"):
            count += 1
            is_valid = do_compute(os.path.join(source_dir_path, filename), pks, q, virtual)
            s_valid = "correct" if is_valid else "error"

print(f"Valid answer count: {COUNT}")