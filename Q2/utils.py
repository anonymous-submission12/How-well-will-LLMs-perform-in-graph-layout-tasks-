import ast
import glob
import re

class CustomError(RuntimeError):
    pass

def read_graph_from_edge_list(filename:str):
    edges = []
    nodes = set()

    with open(filename, 'r') as file:
        for line in file:
            node1, node2 = map(int, line.split())
            
            edges.append((node1, node2))
            
            nodes.add(node1)
            nodes.add(node2)
    
    return sorted(list(nodes)), sorted(list(edges))

def read_graph_from_adj_list(filename:str):
    edges = set()
    nodes = set()
    graph = {}

    with open(filename, 'r') as file:
        for line in file:
            node, adj_list_str = line.split(':')
            node = int(node.strip())
            
            adj_list = ast.literal_eval(adj_list_str.strip())
            
            graph[node] = adj_list

            nodes.add(node)
            
            for adj_node in adj_list:
                edge = tuple(sorted((node, adj_node)))  # Sort the edge to prevent duplicates
                edges.add(edge)
                nodes.add(adj_node)
    
    return sorted(list(nodes)), sorted(list(edges)), graph

def parse_graph_to_str_el(f):
    n, e = read_graph_from_edge_list(f)
    return e

def parse_graph_to_str_al(f):
    n, e, g = read_graph_from_adj_list(f)
    return g

def deal_with_synonym(pattern: str) -> str:
    match pattern:
        case "Clustered graph":
            return "clustered graph"
        case "Clustered":
            return "clustered graph"
        case "['Random']":
            return "random graph"
        case "Complete graph":
            return "Complete"
        case "Random":
            return "random graph"
        case "Random Graph":
            return "random graph"
        case "Random graph":
            return "random graph"
        case "Clustered Graph":
            return "clustered graph"
        case _:
            return pattern
        
def get_pattern_by_p_ailas(p_alias:str) -> str:
    if not is_valid_p_alias(p_alias):
        raise CustomError(f"Invalid p_alias {p_alias}")
    
    match p_alias:
        case "ER": return "random graph"
        case "SBM": return "clustered graph"
        case _: return p_alias

def is_valid_p_alias(p_alias: str) -> bool:
    return p_alias in ["Complete", "Cycle", "Grid", "Path", "Star", "ER", "SBM"]

def is_valid_pattern(pattern: str) -> bool:
    return pattern in ["Complete", "Cycle", "Grid", "Path", "Star", "random graph", "clustered graph", "Unknown"]

def get_graph_data_repr_by_pk(fmt:str, p_alias:str, size:str, index:int) -> str:
    if not is_valid_p_alias(p_alias):
        raise CustomError(f"Invalid p_alias {p_alias}")
    if size not in ["exlarge", "small"]:
        raise CustomError(f"Invalid size {size}.")
    if fmt not in ["adjacency_list", "edge_list"]:
        raise CustomError(f"Invalid fmt {fmt}.")

    term = "general" if p_alias == "ER" or p_alias == "SBM" else "special"

    str_pattern = f"{index}_{p_alias}_*.txt"
    files = glob.glob(f"data/{size}_{term}_graphs/{fmt}/{p_alias}/{str_pattern}")

    for file in files:
        match = re.match(rf"data/{size}_{term}_graphs/{fmt}/{p_alias}/(\d+)_.*\.txt$", file)
        if match and int(match.group(1)) == index:
            if fmt == "adjacency_list":
                n, e, g = read_graph_from_adj_list(file)
                return g
            else:
                n, e = read_graph_from_edge_list(file)
                return e

    
    raise CustomError(f"Filename not found for {fmt} {p_alias} {size} {index}")

def find_graph_data_by_pk(fmt:str, p_alias:str, size:str, index:int) -> str:
    """Find the path of graph data file for (FMT, P_ALIAS, SIZE, INDEX)"""
    if size not in ["large", "small"]:
        raise CustomError(f"Invalid size {size}.")
    if fmt not in ["adjacency_list", "edge_list"]:
        raise CustomError(f"Invalid fmt {fmt}.")

    term = "general" if p_alias == "ER" or p_alias == "SBM" else "special"

    str_pattern = f"{index}_{p_alias}_*.txt"
    files = glob.glob(f"data/{size}_{term}_graphs/{fmt}/{p_alias}/{str_pattern}")

    for file in files:
        match = re.match(rf"data/{size}_{term}_graphs/{fmt}/{p_alias}/(\d+)_.*\.txt$", file)
        if match and int(match.group(1)) == index:
            return file
