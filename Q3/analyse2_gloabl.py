import os
import json
import re
import utils
from itertools import product
import csv
import pathlib
import shutil

def f_alias(fmt:str) -> str:
    return "A.L." if fmt == "adjacency_list" else "E.L."

def s_alias(size:str) -> str:
    return "S." if size == "small" else "L."


def parse_equal(str):
    possibles = ["Both layouts have the same number of edge crossings.", "None, both have zero crossings", "Both", "Both layouts are equally good"]
    if str in possibles:
        return 3
    return str

def write_dict_to_csv(data, filename):
    row_identifiers = sorted(set((key[0], key[2]) for key in data.keys()))  # (model, modality)
    column_identifiers = sorted(set((key[1]) for key in data.keys()))  # (size)
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Model-Fmt"] + [f"{p}" for p in column_identifiers])
        
        for row_id in row_identifiers:
            row = [f"{row_id[0]}-{row_id[1]}"]
            for col_id in column_identifiers:
                value = data.get((row_id[0], col_id, row_id[1]), '')  # Default to empty if missing
                row.append(value)
            writer.writerow(row)

def extract_components(s):
    pattern = re.compile(r"(?P<model>[^/]+)/(?P<size>[^/]+)/(?P<p_alias>[^/]+)/(?P<task>[^/]+)/(?P<modality>[^/]+)")
    match = pattern.fullmatch(s)
    
    if match:
        components = match.groupdict()
        if '.ipynb_checkpoints' in components:
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
                model, size, p_alias, task, modality = components.values()
                if size == "large":
                    continue
            if file.endswith('.txt'):
                parts = file.rstrip(".txt").split("_")
                if len(parts) != 5:
                    raise utils.CustomError(f"Invalid parts length {parts}")
                i = int(parts[2])
                
                graph = utils.get_graph_data_repr_by_pk(p_alias, size, i)
                file_path = os.path.join(root, file)
                answer = ")OKlsSF" #ARBITRARY STRING TO REPLACE NONE SINCE NONE MIGHT BE ANSWER
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        json_blocks = extract_json_blocks(content)
                        for block in json_blocks:
                            if "Answer" in block:
                                answer = block["Answer"]
                        if answer == ")OKlsSF":
                            raise utils.CustomError("No answer found.")
                        elif answer == None:
                            print(f"NONE FOR {file_path}")
                except utils.CustomError:
                    print(f"No answer found {file_path}")
                    with open("NoAnswerList.txt", "a") as f:
                        f.write(f"No answer found {model}, {size}, {p_alias}, {i}, {task}, {modality}\n")
                    continue

                metric1_path = f"metrics/{size}/{p_alias}/{i}_{p_alias}_iter10.json"
                metric2_path = f"metrics/{size}/{p_alias}/{i}_{p_alias}_iter50.json"

                with open(metric1_path, "r") as f:
                    metric1 = json.load(f)
                with open(metric2_path, "r") as f:
                    metric2 = json.load(f)

                if metric1["crossings"] < metric2["crossings"]:
                    answer_edge = 1
                elif metric1["crossings"] > metric2["crossings"]:
                    answer_edge = 2
                else:
                    answer_edge = 3
                
                if metric1["stress"] < metric2["stress"]:
                    answer_distance = 1
                elif metric1["stress"] > metric2["stress"]:
                    answer_distance = 2
                else:
                    raise utils.CustomError("SAME STRESS")

                answer = parse_equal(answer)

                match task:
                    case "edge":
                        try:
                            answer = int(answer)
                        except Exception as e:
                            print(f"Invalid answer {answer} for {file_path}")
                            continue
                        grouped_answers.append(answer == answer_edge)
                    case "distance":
                        try:
                            answer = int(answer)
                        except Exception as e:
                            print(f"Invalid answer {answer} for {model}, {size}, {p_alias}, {i}, {task}, {modality}")
                            continue
                        grouped_answers.append(answer == answer_distance)
                    case "community":
                        try:
                            answer = int(answer)
                        except Exception as e:
                            print(f"Invalid answer {answer} for {model}, {size}, {p_alias}, {i}, {task}, {modality}")
                            continue
                        grouped_answers.append(answer == 2)
                    case _:
                        raise utils.CustomError("Invalid question.")

                    
                #source_path = file_path
                #destination = file_path.replace("results_global/", "categorized_results_global/")
                #d_path = pathlib.Path(destination)
                #d_path_parent = d_path.parent
                #final_d_path = d_path_parent.joinpath()
                #if grouped_answers[-1] == True:
                #    final_d_path = d_path_parent.joinpath(f"correct/{file}")
                #else:
                #    final_d_path = d_path_parent.joinpath(f"error/{file}")
                #
                #os.makedirs(final_d_path.parent, exist_ok=True)
                #shutil.copy(file_path, final_d_path)

        if grouped_answers:
            answers[group_key] = grouped_answers

    return answers

# Example usage
base_directory = "results_global"
answers_dict = extract_answers(base_directory)

p_aliases = ["Cycle", "Grid", "Path", "Star", "SBM"]
fmts = ["edge_list"]
models = ["gpt-4o-2024-11-20", "gemini-2.0-flash-001"]
sizes = ["small", "exlarge"]
modalities = ["image","data+pos","image+data+pos"]
tasks = ["edge", "distance"]
potential_tasks = ["edge", "distance", "community"]

p_ks = list(product(models, sizes, p_aliases, tasks, modalities))
communites = list(product(models, sizes, ["SBM"], ["community"], modalities))
p_ks.extend(communites)


for qq in potential_tasks:
    keys = list(product(models, sizes, modalities)) #CHANGE HERE
    grouped = dict()
    for k in keys:
        grouped[k] = []
    for category, answers in answers_dict.items():
        model, size, p_alias, task, modality  = category.split("/")
        a_key = (model, size, modality)
        if a_key not in keys:
            continue
        if task != qq:
            continue
        grouped[(a_key)].extend(answers) #CHANGE HERE

    out_grouped = dict()

    for k, a in grouped.items():
        if qq == "community":
            divisor = 20
        else:
            divisor = 60
        if len(a) != divisor:
            print(k, len(a), divisor, qq)
        out_grouped[k] = a.count(True)/divisor

    os.makedirs("analysis/global", exist_ok=True)
    write_dict_to_csv(out_grouped, f"analysis/global/{qq}.csv")