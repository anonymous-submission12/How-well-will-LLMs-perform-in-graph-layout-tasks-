import os
import json
import re
import networkx as nx
import utils
import numpy as np
from itertools import product
import csv
import shutil
import pathlib

def f_alias(fmt:str) -> str:
    return "A.L." if fmt == "adjacency_list" else "E.L."

def s_alias(size:str) -> str:
    return "S." if size == "small" else "L."


def write_dict_to_csv(data, filename):
    # Extract unique row and column identifiers
    row_identifiers = sorted(set((key[0], key[2]) for key in data.keys()))  # (model, fmt)
    column_identifiers = sorted(set((key[1], key[3]) for key in data.keys()))  # (p-alias, size)
    
    # Write to CSV file
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Write header
        writer.writerow(["Model-Fmt"] + [f"{p}-{s_alias(s)}" for p, s in column_identifiers])
        
        # Write rows
        for row_id in row_identifiers:
            row = [f"{row_id[0]}-{f_alias(row_id[1])}"]
            for col_id in column_identifiers:
                value = data.get((row_id[0], col_id[0], row_id[1], col_id[1]), '')  # Default to empty if missing
                row.append(value)
            writer.writerow(row)

def extract_components(s):
    pattern = re.compile(r"(?P<model>[^/]+)/(?P<size>[^/]+)/(?P<fmt>[^/]+)/(?P<pattern>[^/]+)/(?P<q>[^/]+)")
    match = pattern.fullmatch(s)
    
    if match:
        components = match.groupdict()
        if components['q'] == '.ipynb_checkpoints':
            return None  # Invalid q value, filter it out
        return components
    return None  # No match

def extract_json_blocks(text):
    """Extract JSON code blocks from text."""
    json_blocks = []
    matches = re.findall(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    for match in matches:
        # Ensure the match has balanced braces by trimming extra trailing '}'
        while match.count('{') < match.count('}'):
            match = match[:-1]  # Remove one trailing '}'

        try:
            json_blocks.append(json.loads(match))
        except json.JSONDecodeError:
            print(f"JSON DECODE ERROR")
    if json_blocks == []:
        matches = re.findall(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
        for match in matches:
            # Ensure the match has balanced braces by trimming extra trailing '}'
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
        group_key = os.path.relpath(root, base_path)  # Meaningful grouping
        
        if "claude-3-5-sonnet-20241022" in group_key or ".ipynb_checkpoints" in group_key:
            #print("GK", group_key)
            continue
        components = extract_components(group_key)
        #print(components)
        grouped_answers = []

        for file in files:
            if components != None:
                #print(components)
                model, size, fmt, p_alias, q = components.values()
                if size == "large":
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
                        answer = f.read().rstrip("\n")
                        """json_blocks = extract_json_blocks(content)
                        for block in json_blocks:
                            if "answer" in block:
                                answer = block["answer"]
                                #grouped_answers.append(block["answer"])
                        if answer == ")OKlsSF":
                            raise utils.CustomError("No answer found.")
                        elif answer == None:
                            print(f"NONE FOR {model}, {size}, {fmt}, {p_alias}, {i}, {q}")"""
                except utils.CustomError:
                    with open(FINAL_FILE, "a") as f:
                        f.write(f"No answer found {model}, {size}, {fmt}, {p_alias}, {i}, {q}\n")
                    continue

                source_path = file_path.replace("outputs", "results")
                destination = file_path.replace("outputs", "categorized_results")
                d_path = pathlib.Path(destination)
                d_path_parent = d_path.parent
                final_d_path = d_path_parent.joinpath()

                match q:
                    #case "pattern_None":
                    #    true_pattern = utils.get_pattern_by_p_ailas(p_alias)
                    #    answer = utils.deal_with_synonym(answer)
                    #    if not utils.is_valid_pattern(answer):
                    #        #print(f"Not valid answer \"{answer}\" for {model}, {size}, {fmt}, {p_alias}, {i}, {q}")
                    #        with open("NoAnswerList_Updated.txt", "a") as f:
                    #            f.write(f"Not valid answer \"{answer}\" for {model}, {size}, {fmt}, {p_alias}, {i}, {q}\n")
                    #        value = 1.0
                    #    else:
                    #        value = 0.0 if answer == true_pattern else 1.0
                    #        #print(value)
                    #    grouped_answers.append(value)
                    case "minor_edge_count":
                        true_e = graph.number_of_edges()
                        try:
                            answer = int(answer)
                        except ValueError as e:
                            print(type(e), e)
                            with open(FINAL_FILE, "a") as f:
                                f.write(f"{type(e)}, {e} for {model}, {size}, {fmt}, {p_alias}, {i}, {q}\n")
                            final_d_path = d_path_parent.joinpath(f"exception/{file}")
                            os.makedirs(final_d_path.parent, exist_ok=True)
                            shutil.copy(source_path, final_d_path)
                            continue
                        grouped_answers.append(abs((answer-true_e)/true_e))
                    case "minor_node_count":
                        true_n = graph.number_of_nodes()
                        try:
                            answer = int(answer)
                        except ValueError as e:
                            with open(FINAL_FILE, "a") as f:
                                f.write(f"{type(e)}, {e} for {model}, {size}, {fmt}, {p_alias}, {i}, {q}\n")
                            final_d_path = d_path_parent.joinpath(f"exception/{file}")
                            os.makedirs(final_d_path.parent, exist_ok=True)
                            shutil.copy(source_path, final_d_path)
                            continue
                        grouped_answers.append(abs((answer-true_n)/true_n))
                    case "minor_highest_degree":
                        degree_sequence = sorted((d for n, d in graph.degree()), reverse=True)
                        true_dmax = max(degree_sequence)
                        try:
                            answer = int(answer)
                        except ValueError as e:
                            with open(FINAL_FILE, "a") as f:
                                f.write(f"{type(e)}, {e} for {model}, {size}, {fmt}, {p_alias}, {i}, {q}\n")
                            final_d_path = d_path_parent.joinpath(f"exception/{file}")
                            os.makedirs(final_d_path.parent, exist_ok=True)
                            shutil.copy(source_path, final_d_path)
                            continue
                        grouped_answers.append(abs((answer-true_dmax)/true_dmax))
                    case "minor_shortest_path":
                        true_len = nx.shortest_path_length(graph, node1, node2)
                        if answer == None:
                            grouped_answers.append(None)
                        else:
                            try:
                                answer = int(answer)
                            except ValueError as e:
                                with open(FINAL_FILE, "a") as f:
                                    f.write(f"{type(e)}, {e} for {model}, {size}, {fmt}, {p_alias}, {i}, {q}\n")
                                final_d_path = d_path_parent.joinpath(f"exception/{file}")
                                os.makedirs(final_d_path.parent, exist_ok=True)
                                shutil.copy(source_path, final_d_path)
                                continue
                            grouped_answers.append(abs((answer-true_len)/true_len))
                    case "community_None":
                        true_comm = int(source_file.rstrip(".txt").split("_")[-1])
                        try:
                            answer = int(answer)
                        except ValueError as e:
                            with open(FINAL_FILE, "a") as f:
                                f.write(f"{type(e)}, {e} for {model}, {size}, {fmt}, {p_alias}, {i}, {q}\n")
                            final_d_path = d_path_parent.joinpath(f"exception/{file}")
                            os.makedirs(final_d_path.parent, exist_ok=True)
                            shutil.copy(source_path, final_d_path)
                            continue
                        grouped_answers.append(abs((answer-true_comm)/true_comm))
                    case _:
                        raise utils.CustomError("Invalid question.")
                    
                #if grouped_answers[-1] == 0.0:
                #    final_d_path = d_path_parent.joinpath(f"correct/{file}")
                #else:
                #    final_d_path = d_path_parent.joinpath(f"error/{file}")
                
                #print(source_path)
                #print(destination)
                #d_path = pathlib.Path(destination)
                ##print(final_d_path)
                #os.makedirs(final_d_path.parent, exist_ok=True)
                #shutil.copy(source_path, final_d_path)

                                                       

        if grouped_answers:
            answers[group_key] = grouped_answers

    return answers

FINAL_FILE = "WHATEVERIDONTKNOW.txt"

# Example usage
base_directory = "outputs"
with open(FINAL_FILE, "w") as f:
    f.write("")

answers_dict = extract_answers(base_directory)

#models = ["deepseek-v3", "gpt-4o-2024-11-20"]
models = ["gpt-4o-2024-11-20", "gemini-2.0-flash-001", "deepseek-v3"]
sizes = ["exlarge", "small"]
fmts = ["adjacency_list", "edge_list"]
#p_aliases = ["Complete", "Cycle", "Grid", "Path", "Star", "ER", "SBM"]
p_aliases = ["Cycle", "Grid", "Path", "Star", "SBM"]
#qs = ["pattern_None", "minor_edge_count", "minor_node_count", "minor_highest_degree", "minor_shortest_path", "community_None"]

"""keys = list(product(models, p_aliases, fmts, sizes)) #CHANGE HERE
#keys = [k for k in keys if k[1] == "SBM"]
#print(keys)
grouped = dict()
for k in keys:
    grouped[k] = []"""

# Print results

qs = ["edge_count", "node_count", "highest_degree", "shortest_path", "community"]

for qq in qs:
    keys = list(product(models, p_aliases, fmts, sizes)) #CHANGE HERE
    if qq == "community":
        keys = [k for k in keys if k[1] == "SBM"]
    #print(keys)
    grouped = dict()
    for k in keys:
        grouped[k] = []
    for category, answers in answers_dict.items():
        model, size, fmt, p_alias, q = category.split("/")

        match qq:
            case "pattern":
                raise utils.CustomError("PATTERN")
            #    if q != f"{qq}_None":
            #        continue
            case "community":
                if q != f"{qq}_None" or p_alias != "SBM":
                    continue
            case _:
                if q != f"minor_{qq}":
                    continue
        grouped[(model, p_alias, fmt, size)].extend(answers) #CHANGE HERE

    out_grouped = dict()

    for k, a in grouped.items():
        if k[1] in ["SBM", "ER"]:
            divisor = 50
        else:
            divisor = 10
        if len(a) != divisor:
            print(k, len(a), divisor, qq)
        out_grouped[k] = a.count(0.0)/divisor
        #grouped[k] = np.mean(a)
    #write_dict_to_csv(out_grouped, f"analysis/{qq}.csv")

    out_grouped = dict()
    if qq != "pattern":
        for k, a in grouped.items():
            non_none = [_ for _ in a if _ is not None]
            #out_grouped[k] = a.count(0.0)/len(a)
            if len(non_none) == 0:
                out_grouped[k] = "N/A"
            else:
                out_grouped[k] = np.mean(non_none)
        
        #write_dict_to_csv(out_grouped, f"analysis/{qq}_dev.csv")
