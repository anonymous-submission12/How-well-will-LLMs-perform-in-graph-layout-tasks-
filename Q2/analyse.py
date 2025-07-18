import os
import json
import re
import numpy as np
from itertools import product
import csv

def s_alias(size:str) -> str:
    return "S." if size == "small" else "L."

def write_dict_to_csv(data, filename):
    row_identifiers = sorted(set((key[0], key[1]) for key in data.keys()))  # (model, size)
    column_identifiers = sorted(set((key[2]) for key in data.keys()))  # (m)
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Model-size"] + [f"{s}" for s in column_identifiers])
        
        for row_id in row_identifiers:
            row = [f"{row_id[0]}-{row_id[1]}"]
            for col_id in column_identifiers:
                value = data.get((row_id[0], row_id[1], col_id), '')  # Default to empty if missing
                row.append(value)
            writer.writerow(row)

def extract_components(s):
    pattern = re.compile(r"(?P<model>[^/]+)/(?P<size>[^/]+)/(?P<pattern>[^/]+)/(?P<q>[^/]+)")
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



def extract_answers(base_path, answers):
    """Extract 'answer' values grouped by directory structure."""
    #answers = {}

    for root, _, files in os.walk(base_path):
        group_key = os.path.relpath(root, base_path)
        
        if "claude-3-5-sonnet-20241022" in group_key or ".ipynb_checkpoints" in group_key:
            print("GK", group_key)
            continue
        components = extract_components(group_key)
        metrics = dict()

        metric_names = []

        for file in files:
            if components != None:
                model, size, p_alias, req = components.values()
            if file.endswith('.txt'):
                parts = file.rstrip(".txt").split("_")
                
                path = os.path.join(root, file)
                with open(path, "r") as f:
                    rs = json.load(f)

                metric_names = ["stress", "crossings"]
                if p_alias == "SBM":
                    metric_names.extend(["intra", "inter"])

                for m in metric_names:
                    if m in metrics:
                        metrics[m].append(float(rs[m]))
                    else:
                        metrics[m] = [float(rs[m])]

        if metric_names:
            for m in metric_names:
                key = (group_key, m)
                if key in answers:
                    answers[key].extend(metrics[m])
                else:
                    answers[key] = metrics[m]

    return answers

answers_dict = dict()
alg_directory = "metrics_alg"
answers_dict = extract_answers(alg_directory, answers_dict)
noalg_directory = "metrics_noalg"
#answers_dict = extract_answers(noalg_directory, answers_dict)
# NOTE separately load raw data for code assisted reasoning or textual reasoning
with open("NoAnswerList_Updated.txt", "w") as f:
    f.write("")

models = ["gpt-4o-2024-11-20", "deepseek-v3", "gemini-2.0-flash-001"]
p_aliases = ["Cycle", "Grid", "Path", "Star", "SBM"]
fmts = ["edge_list"]
sizes = ["exlarge", "small"]
reqs = list(range(2, 5))
allow_algs = [True, False]
ms = ["stress", "crossings"]

indexes = {
    "stress": 2,
    "crossings": 3,
    "intra": 4,
    "inter": 4
}

metric_maps = {
    2: ["stress"],
    3: ["crossings"],
    4: ["intra", "inter"]
}

for req in reqs:
    keys = list(product(models, sizes, metric_maps[req])) #CHANGE HERE
    grouped = dict()
    for k in keys:
        grouped[k] = []
    for category, answers in answers_dict.items():
        c, m = category
        model, size, p_alias, qq = c.split("/")

        req_index_of_metric = indexes[m]
        if int(qq) != req or req_index_of_metric != int(qq):
            continue
        
        grouped[(model, size, m)].extend(answers) #CHANGE HERE
        print(answers, category)

    out_grouped = dict()

    for k, a in grouped.items():
        if req == 2 or req == 3:
            divisor = 60
        else:
            divisor = 20
        if len(a) != divisor:
            print(k, len(a), divisor, req)
        if len(a) == 0:
            out_grouped[k] = "N/A"
        else:
            out_grouped[k] = np.mean(a)
        

    write_dict_to_csv(out_grouped, f"analysis/alg_{req}.csv")
