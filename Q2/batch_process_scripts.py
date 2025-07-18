import os
from itertools import product
from llm_sandbox import SandboxSession
from func_time_out import func_timeout, FunctionTimedOut
import time

e_count = 0

def run_with_sandbox(session, script_path, data_pk):
    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()
    model, size, fmt, p_alias, q, allow_alg = data_pk
    t = time.localtime()
    print("Starting:", model, size, p_alias, q, allow_alg, f"{t.tm_hour}:{t.tm_min}:{t.tm_sec}")
    try:
        result = func_timeout(300, session.run, args=[script_text])
    except FunctionTimedOut as e:
        result = "exception FunctionTimedOut"
    result = str(result)
    if result.startswith("exception: invalid syntax"):
        if script_text == "No valid code block.":
            print(script_path, script_text)
        else:
            print(script_path, "\nWHATEVER\n")
    elif result.startswith("exception"):
        global e_count
        e_count += 1
        print(script_path, result)
    output_file = os.path.join(output_dir_path, os.path.basename(script_path).replace(".py", ".txt"))

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result)

models = ["gpt-4o-2024-11-20", "deepseek-v3", "gemini-2.0-flash-001"]
p_aliases = ["Cycle", "Grid", "Path", "Star", "SBM"]
fmts = ["edge_list"]
sizes = ["exlarge", "small"]
allow_algs = [True, False]

p_ks = list(product(models, sizes, fmts, ["SBM"], [4], allow_algs))

debug = False
s_debug = "-debug" if debug else ""

count = 0
with SandboxSession(image="my:third", keep_template=False, lang="python") as session:
    for p_k in p_ks:
        model, size, fmt, p_alias, q, allow_alg = p_k
        s_allow = "_algpermitted" if allow_alg else "_algrestricted"
        code_dir_path = f"codes{s_allow}{s_debug}/{model}/{size}/{p_alias}/{q}"
        output_dir_path = f"outputs{s_allow}{s_debug}/{model}/{size}/{p_alias}/{q}"
        os.makedirs(output_dir_path, exist_ok=True)

        for filename in os.listdir(code_dir_path):
            if filename.endswith(".py"):
                id = int(filename.split("_")[4])
                data_pk = (model, size, fmt, p_alias, q, allow_alg)
                count += 1
                run_with_sandbox(session, os.path.join(code_dir_path, filename), data_pk)
print("Batch processing complete.")

print(e_count)