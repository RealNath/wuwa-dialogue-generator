import json
from typing import List
from pathlib import Path
from data_loader import load_flow, load_flowstate

def get_base_dir():
    return Path(__file__).resolve().parent.parent

def get_states_for_id(target_id: str) -> List[str]:
    data = load_flow(get_base_dir())
    for item in data:
        if item.get("Id") == target_id:
            states = item.get("States", [])
            return [f"{target_id}_{state}" for state in states]
            
    return []

def get_actions_for_state_keys(state_keys: List[str]) -> dict:
    data = load_flowstate(get_base_dir())
    state_keys_set = set(state_keys)
    result = {}
    
    for item in data:
        state_key = item.get("StateKey")
        if state_key in state_keys_set:
            result[state_key] = item.get("Actions")
            
    return result

def parse_json_string(json_string: str) -> list:
    if not json_string:
        return []
    
    parsed_data = json.loads(json_string)
    
    with open("test.json", "w", encoding="utf-8") as f:
        # Dump the parsed_data (list/dict)
        json.dump(parsed_data, f, ensure_ascii=False, indent=4)
    
    return parsed_data
