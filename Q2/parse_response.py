import re
import os
from itertools import product

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

NOVCODE_FILE = "NoValidCodeList.txt"

count = 0
with open(NOVCODE_FILE, "w") as f:
    f.write("")
for p_k in p_ks:
    model, size, fmt, p_alias, q, allow_alg = p_k
    s_allow = "_algpermitted" if allow_alg else "_algrestricted"
    dir_path = f"results{s_allow}{s_debug}/{model}/{size}/{p_alias}/{q}"
    code_dir_path = f"codes{s_allow}{s_debug}/{model}/{size}/{p_alias}/{q}"
    
    os.makedirs(code_dir_path, exist_ok=True)
    try:
        filenames = os.listdir(dir_path)
    except FileNotFoundError as e:
        print(e)
        continue
    for filename in filenames:
        if not filename.endswith(".txt"):
            continue
        path = f"{dir_path}/{filename}"
        with open(path, "r") as f:
            response = f.read()
            
        pattern = re.compile(r'```python.*?\n(.*?)```', re.DOTALL)

    
        matches = pattern.findall(response)

        if matches: 
            python_code_blocks = [match.strip() for match in matches]
            
            if python_code_blocks == None:
                print(filename)
                continue
            extracted_code = python_code_blocks[0]
        else: 
            print("No valid code block",s_allow, q,model, filename)
            count += 1
            with open(NOVCODE_FILE, "a") as f:
                f.write(f"No valid code block,{q},{s_allow},{model},{filename}\n")
            continue #DO NOT GENERATE .PY FILE FOR RESPONSES WITHOUT CODEBLOCK
        code_file_path = f"{code_dir_path}/{filename}".replace(".txt", ".py")
        with open(code_file_path, "w") as f:
            f.write(extracted_code)

print(count)