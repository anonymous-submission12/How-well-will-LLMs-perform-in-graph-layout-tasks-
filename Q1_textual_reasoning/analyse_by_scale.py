import os
import json
import re
import networkx as nx
import utils
import numpy as np
from itertools import product
import csv
import pathlib
import shutil

def f_alias(fmt:str) -> str:
    return "A.L." if fmt == "adjacency_list" else "E.L."

def s_alias(size:str) -> str:
    return "S." if size == "small" else "L."


def write_dict_to_csv(data, filename):
    row_identifiers = sorted(set((key[0], key[1]) for key in data.keys()))  # (model, fmt)
    column_identifiers = sorted(set((key[2]) for key in data.keys()))  # (size)
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        writer.writerow(["Model-Fmt"] + [f"{s_alias(s)}" for s in column_identifiers])
        
        for row_id in row_identifiers:
            row = [f"{row_id[0]}-{f_alias(row_id[1])}"]
            for col_id in column_identifiers:
                value = data.get((row_id[0], row_id[1], col_id), '')  # Default to empty if missing
                row.append(value)
            writer.writerow(row)

def extract_components(s):
    pattern = re.compile(r"(?P<model>[^/]+)/(?P<size>[^/]+)/(?P<fmt>[^/]+)/(?P<pattern>[^/]+)/(?P<q>[^/]+)")
    match = pattern.fullmatch(s)
    
    if match:
        components = match.groupdict()
        if components['q'] == '.ipynb_checkpoints':
            return None
        return components
    return None

def extract_json_blocks(text):
    """Extract JSON code blocks from text."""
    json_blocks = []
    matches = re.findall(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    for match in matches:
        while match.count('{') < match.count('}'):
            match = match[:-1]  # Remove one trailing '}'

        try:
            json_blocks.append(json.loads(match))
        except json.JSONDecodeError:
            print(f"JSON DECODE ERROR")
    if json_blocks == []:
        matches = re.findall(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
        for match in matches:
            while match.count('{') < match.count('}'):
                match = match[:-1]  # Remove one trailing '}'

            try:
                json_blocks.append(json.loads(match))
            except json.JSONDecodeError:
                print(f"JSON DECODE ERROR: {match}")
    return json_blocks



def extract_answers(base_path):
    """Extract 'answer' values grouped by directory structure."""
    answers = {}

    for root, _, files in os.walk(base_path):
        group_key = os.path.relpath(root, base_path)
        
        if "claude-3-5-sonnet-20241022" in group_key or ".ipynb_checkpoints" in group_key:
            #print("GK", group_key)
            continue
        components = extract_components(group_key)
        grouped_answers = []

        for file in files:
            if components != None:
                model, size, fmt, p_alias, q = components.values()
                if size == "large" or q == "pattern_None" or p_alias == "Complete" or p_alias == "ER":
                    continue
            if file.endswith('.txt'):
                parts = file.rstrip(".txt").split("_")
                if q == "minor_shortest_path":
                    if len(parts) != 8:
                        raise utils.CustomError(f"Invalid parts length {parts}")
                    i, node1, node2 = map(int, parts[4:7])
                else:
                    if len(parts) != 6:
                        raise utils.CustomError(f"Invalid parts length {parts}")
                    i = int(parts[4])
                source_file = utils.find_graph_data_by_pk(fmt, p_alias, size, i)
                
                if fmt == "adjacency_list":
                    n, e, _ = utils.read_graph_from_adj_list(source_file)
                else:
                    n, e = utils.read_graph_from_edge_list(source_file)
                graph = nx.Graph(e)
                file_path = os.path.join(root, file)
                answer = ")OKlsSF" #ARBITRARY STRING TO REPLACE NONE SINCE NONE MIGHT BE ANSWER
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        json_blocks = extract_json_blocks(content)
                        for block in json_blocks:
                            if "answer" in block:
                                answer = block["answer"]
                        if answer == ")OKlsSF":
                            raise utils.CustomError("No answer found.")
                        elif answer == None:
                            print(f"NONE FOR {model}, {size}, {fmt}, {p_alias}, {i}, {q}")
                except utils.CustomError:
                    print(f"No answer found {model}, {size}, {fmt}, {p_alias}, {i}, {q}")
                    with open("NoAnswerList.txt", "a") as f:
                        f.write(f"No answer found {model}, {size}, {fmt}, {p_alias}, {i}, {q}\n")
                    continue

                match q:
                    case "minor_edge_count":
                        true_e = graph.number_of_edges()
                        answer = int(answer)
                        grouped_answers.append(abs((answer-true_e)/true_e))
                    case "minor_node_count":
                        true_n = graph.number_of_nodes()
                        answer = int(answer)
                        grouped_answers.append(abs((answer-true_n)/true_n))
                    case "minor_highest_degree":
                        degree_sequence = sorted((d for n, d in graph.degree()), reverse=True)
                        true_dmax = max(degree_sequence)
                        answer = int(answer)
                        grouped_answers.append(abs((answer-true_dmax)/true_dmax))
                    case "minor_shortest_path":
                        true_len = nx.shortest_path_length(graph, node1, node2)
                        if answer == None:
                            grouped_answers.append(None)
                        else:
                            answer = int(answer)
                            grouped_answers.append(abs((answer-true_len)/true_len))
                    case "community_None":
                        true_comm = int(source_file.rstrip(".txt").split("_")[-1])
                        answer = int(answer)
                        grouped_answers.append(abs((answer-true_comm)/true_comm))
                    case _:
                        raise utils.CustomError("Invalid question.")

                #source_path = file_path.replace("outputs/", "results")
                """destination = file_path.replace("results/", "categorized_results/")
                d_path = pathlib.Path(destination)
                d_path_parent = d_path.parent
                final_d_path = d_path_parent.joinpath()
                if grouped_answers[-1] == 0.0:
                    final_d_path = d_path_parent.joinpath(f"correct/{file}")
                else:
                    final_d_path = d_path_parent.joinpath(f"error/{file}")
                """
                #d_path = pathlib.Path(destination)
                #os.makedirs(final_d_path.parent, exist_ok=True)
                #shutil.copy(file_path, final_d_path)        

        if grouped_answers:
            answers[group_key] = grouped_answers

    return answers

# Example usage
base_directory = "results"
answers_dict = extract_answers(base_directory)

models = ["deepseek-v3", "gpt-4o-2024-11-20", "gemini-2.0-flash-001"]
sizes = ["exlarge", "small"]
fmts = ["adjacency_list", "edge_list"]
p_aliases = ["Cycle", "Grid", "Path", "Star", "SBM"]

qs = ["edge_count", "node_count", "highest_degree", "shortest_path", "community"]

for qq in qs:
    keys = list(product(models, fmts, sizes)) #CHANGE HERE
    grouped = dict()
    for k in keys:
        grouped[k] = []
    for category, answers in answers_dict.items():
        model, size, fmt, p_alias, q = category.split("/")
        a_key = (model, fmt, size)
        if a_key not in keys:
            continue
        match qq:
            case "pattern":
                raise utils.CustomError("PATTERN")
            case "community":
                if q != f"{qq}_None" or p_alias != "SBM":
                    continue
            case _:
                if q != f"minor_{qq}":
                    continue
        grouped[(model, fmt, size)].extend(answers) #CHANGE HERE

    out_grouped = dict()

    for k, a in grouped.items():
        if qq == "community":
            divisor = 50
        else:
            divisor = 90
        if len(a) != divisor:
            print(k, len(a), divisor, qq)
        out_grouped[k] = a.count(0.0)/divisor
    write_dict_to_csv(out_grouped, f"analysis_by_scale/{qq}.csv")

    out_grouped = dict()
    for k, a in grouped.items():
        non_none = [_ for _ in a if _ is not None]
        out_grouped[k] = np.mean(non_none)
        write_dict_to_csv(out_grouped, f"analysis_by_scale/{qq}_dev.csv")