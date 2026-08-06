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

def get_actions_and_missing_keys(state_keys: List[str]) -> tuple:
    data = load_flowstate(get_base_dir())
    state_keys_set = set(state_keys)
    
    flow_list_names = set()
    for sk in state_keys:
        parts = sk.split('_')
        if len(parts) >= 3:
            flow_list_name = '_'.join(parts[:-2])
            flow_list_names.add(flow_list_name)
            
    result = {}
    missing_keys = []
    
    for item in data:
        state_key = item.get("StateKey")
        if not state_key:
            continue
            
        if state_key in state_keys_set:
            result[state_key] = item.get("Actions")
        else:
            for fln in flow_list_names:
                if state_key.startswith(f"{fln}_"):
                    missing_keys.append(state_key)
                    result[state_key] = item.get("Actions")
                    break
                    
    return result, missing_keys

# insert missing StateKeys and sort
def interleave_missing_keys(state_keys: List[str], missing_state_keys: List[str]) -> tuple:
    state_keys_list = list(state_keys)
    unplaced_keys = []
    
    for mk in missing_state_keys:
        # divide missing StateKeys into FlowListName, FlowId, StateId
        parts = mk.split('_')
        if len(parts) < 3:
            unplaced_keys.append(mk)
            continue
            
        try:
            m_state_id = int(parts[-1])
            m_flow_id = parts[-2]
            m_flow_list_name = '_'.join(parts[:-2])
        except ValueError:
            unplaced_keys.append(mk)
            continue
        
        best_idx = len(state_keys_list)
        found_spot = False
        
        for i, sk in enumerate(state_keys_list):
            # divide available StateKeys into FlowListName, FlowId, StateId
            s_parts = sk.split('_')
            if len(s_parts) < 3:
                continue
            
            try:
                s_state_id = int(s_parts[-1])
                s_flow_id = s_parts[-2]
                s_flow_list_name = '_'.join(s_parts[:-2])
            except ValueError:
                continue
                
            # if available key and missing key belong to same sub-chapter
            # sort (insert) based on StateId
            if s_flow_list_name == m_flow_list_name and s_flow_id == m_flow_id:
                found_spot = True
                if s_state_id > m_state_id:
                    best_idx = i
                    break
                else:
                    best_idx = i + 1
                    
        if found_spot:
            state_keys_list.insert(best_idx, mk)
        else:
            unplaced_keys.append(mk)
        
    return state_keys_list, unplaced_keys

def parse_json_string(json_string: str) -> list:
    if not json_string:
        return []
    
    parsed_data = json.loads(json_string)
    
    with open("test.json", "w", encoding="utf-8") as f:
        # Dump the parsed_data (list/dict)
        json.dump(parsed_data, f, ensure_ascii=False, indent=4)
    
    return parsed_data
