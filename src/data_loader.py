import sys
import json
from pathlib import Path

def load_plothandbookconfig(base_dir):
    plothb_path = base_dir / "data" / "plothandbookconfig.json"
    try:
        with open(plothb_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"plothandbookconfig.json not found in {plothb_path}.")
        sys.exit(1)

def load_multitext(base_dir):
    multitext_dict = {}
    for filename in ["MultiText.json", "MultiText_1.json", "MultiText_2.json"]:
        filepath = base_dir / "data" / filename
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if item.get("Id"):
                        if filename == "MultiText.json" and item.get("RedirectDbIndex") == 1:
                            continue
                        multitext_dict[item.get("Id")] = item.get("Content")
        except FileNotFoundError:
            print(f"multitext files not found in {filepath}.")
            sys.exit(1)
    return multitext_dict

def load_flow(base_dir):
    flow_path = base_dir / "data" / "flow.json"
    try:
        with open(flow_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"flow.json not found in {flow_path}.")
        sys.exit(1)

def load_flowstate(base_dir):
    flowstate_path = base_dir / "data" / "flowstate.json"
    try:
        with open(flowstate_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"flowstate.json not found in {flowstate_path}.")
        sys.exit(1)

def load_questnodedata(base_dir):
    questnodedata_path = base_dir / "data" / "questnodedata.json"
    try:
        with open(questnodedata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"questnodedata.json not found in {questnodedata_path}.")
        sys.exit(1)
