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

def task_1_answer(i) -> str:
    if i in [2, 5, 6]:
        return "No"
    else: 
        return "Yes"

def task_2_answer(i) -> str:
    return ["Euclidean distance is less than graph-theoretic distance", "Euclidean distance is less than graph-theoretic distance."]

def task_3_answer(i) -> int:
    ls = [4, 3, 3, 4, 3, 2, 4, 2, 5, 3]
    return ls[i]

def parse_equal(str):
    possibles = ["Both layouts have the same number of edge crossings.", "None, both have zero crossings", "Both", "Both layouts are equally good"]
    if str in possibles:
        return 3
    return str

def write_dict_to_csv(data, filename):
    row_identifiers = sorted(set((key[0], key[2]) for key in data.keys()))  # (model, modality)
    column_identifiers = sorted(set(key[1] for key in data.keys()))  # (task)
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Model-Modality"] + [f"{t}" for t in column_identifiers])
        
        for row_id in row_identifiers:
            row = [f"{row_id[0]}-{row_id[1]}"]
            for col_id in column_identifiers:
                print((row_id[0], col_id, row_id[1]))
                value = data.get((row_id[0], col_id, row_id[1]), '')  # Default to empty if missing
                row.append(value)
            writer.writerow(row)

def extract_components(s):
    pattern = re.compile(r"(?P<model>[^/]+)/(?P<task>[^/]+)/(?P<modality>[^/]+)")
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
    if json_blocks == []:
        try:
            rs = json.loads(text)
            json_blocks.append(rs)
        except json.JSONDecodeError:
            pass
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
                model, task, modality = components.values()
            else:
                continue
            if file.endswith('.txt'):
                parts = file.rstrip(".txt").split("_")
                if len(parts) != 3:
                    raise utils.CustomError(f"Invalid parts length {parts}")
                i = int(parts[0])
                
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
                        f.write(f"No answer found {model}, {i}, {task}, {modality}\n")
                    continue

                match task:
                    case "edge":
                        grouped_answers.append(answer == task_1_answer(i))
                    case "distance":
                        grouped_answers.append(answer in task_2_answer(i))
                    case "community":
                        try:
                            answer = int(answer)
                        except Exception as e:
                            print(f"Invalid answer {answer} for {model}, {i}, {task}, {modality}")
                            continue
                        grouped_answers.append(answer == task_3_answer(i))
                    case _:
                        raise utils.CustomError("Invalid question.")

                    
                #source_path = file_path
                #destination = file_path.replace("results_local/", "categorized_results_local/")
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
            answers[(model, task, modality)] = grouped_answers

    return answers

# Example usage
base_directory = "results_local"
answers_dict = extract_answers(base_directory)

fmts = ["edge_list"]
models = ["gpt-4o-2024-11-20", "gemini-2.0-flash-001"]
modalities = ["image","data+pos","image+data+pos"]
tasks = ["edge", "distance", "community"]
potential_tasks = ["edge", "distance", "community"]

p_ks = list(product(models, tasks, modalities))

out_grouped = dict()
for k, a in answers_dict.items():
    divisor = 10
    if len(a) != divisor:
        print(k, len(a), divisor)
    out_grouped[k] = a.count(True)/divisor
os.makedirs("analysis/local", exist_ok=True)
print(out_grouped)
write_dict_to_csv(out_grouped, f"analysis/local/analyse.csv")