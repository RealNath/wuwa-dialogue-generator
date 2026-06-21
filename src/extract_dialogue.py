from json import encoder
import json
from typing import List

def get_states_for_id(filepath: str, target_id: str) -> List[str]:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for item in data:
        if item.get("Id") == target_id:
            states = item.get("States", [])
            return [f"{target_id}_{state}" for state in states]
            
    return []

def get_actions_for_state_keys(filepath: str, state_keys: List[str]) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
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
        # We must dump the parsed_data (the list/dict), NOT the action_string!
        json.dump(parsed_data, f, ensure_ascii=False, indent=4)
    
    return parsed_data

def get_talk_flow_lines(parsed_data: list, multitext_dict: dict = None) -> list:
    if multitext_dict is None:
        multitext_dict = {}
    show_talks = [item for item in parsed_data if item.get("Name") == "ShowTalk"]
    if not show_talks:
        return []
        
    output_lines = []
    
    for idx, show_talk in enumerate(show_talks):
        params = show_talk.get("Params", {})
        talk_items = {item["Id"]: item for item in params.get("TalkItems", [])}
        talk_sequence = params.get("TalkSequence", [])
        seq_transitions = params.get("SequenceTransitions", {})
        
        visited = set()
        
        def traverse(seq_idx, indent_level, stop_seqs):
            if seq_idx in visited or seq_idx >= len(talk_sequence) or seq_idx in stop_seqs:
                return
            visited.add(seq_idx)
            
            seq = talk_sequence[seq_idx]
            indent = ":" * indent_level
            
            transitions = seq_transitions.get(str(seq_idx), [])
            
            has_branching_options = False
            options_to_branch = []
            
            for talk_id in seq:
                item = talk_items.get(talk_id)
                if not item: continue
                
                tid_talk = item.get("TidTalk")
                who_id = item.get("WhoId")
                if tid_talk:
                    character_name = multitext_dict.get(f"Speaker_{who_id}_Name", who_id)
                    dialogue = multitext_dict.get(tid_talk, tid_talk)
                    
                    dialogue_line = f"{indent}'''{character_name}:''' {dialogue}"
                    
                    dialogue_line = dialogue_line.replace("{PlayerName}", "{{Rover}}")
                    output_lines.append(dialogue_line)
                    
                if item.get("Options"):
                    options = item.get("Options")
                    
                    # Check if these options trigger a branch in SequenceTransitions
                    branches = False
                    for opt in options:
                        opt_tid = opt.get("TidTalkOption")
                        for trans in transitions:
                            if trans.get("OptionTextKey") == opt.get("PlotLineKey") or trans.get("OptionTextKey") == opt_tid:
                                branches = True
                                break
                                
                    if branches:
                        has_branching_options = True
                        options_to_branch = options
                        break
                    else:
                        # Fake/inline options. Print them and continue the sequence.
                        for opt in options:
                            opt_tid = opt.get("TidTalkOption")
                            if opt_tid:
                                translated_opt = multitext_dict.get(opt_tid, opt_tid)
                                diicon = "{{DIcon}}"
                                output_lines.append(f"{indent}{diicon} {translated_opt}")
            
            if has_branching_options:
                next_seqs = set()
                for opt in options_to_branch:
                    opt_tid = opt.get("TidTalkOption")
                    for trans in transitions:
                        if trans.get("OptionTextKey") == opt.get("PlotLineKey") or trans.get("OptionTextKey") == opt_tid:
                            branch_seq_idx = trans.get("NextSequenceIndex")
                            if branch_seq_idx is not None:
                                b_trans_list = seq_transitions.get(str(branch_seq_idx), [])
                                for bt in b_trans_list:
                                    if not bt.get("OptionTextKey"):
                                        next_seqs.add(bt.get("NextSequenceIndex"))
                            break
                            
                for opt in options_to_branch:
                    opt_tid = opt.get("TidTalkOption")
                    if opt_tid:
                        translated_opt = multitext_dict.get(opt_tid, opt_tid)
                        diicon = "{{DIcon}}"
                        output_lines.append(f"{indent}{diicon} {translated_opt}")
                        
                    branch_seq_idx = None
                    for trans in transitions:
                        if trans.get("OptionTextKey") == opt.get("PlotLineKey") or trans.get("OptionTextKey") == opt_tid:
                            branch_seq_idx = trans.get("NextSequenceIndex")
                            break
                    
                    if branch_seq_idx is not None:
                        traverse(branch_seq_idx, indent_level + 1, stop_seqs.union(next_seqs))
                
                if len(next_seqs) == 1:
                    traverse(next_seqs.pop(), indent_level, stop_seqs)
                elif len(next_seqs) > 1:
                    for n_seq in sorted(next_seqs):
                        traverse(n_seq, indent_level, stop_seqs)
            else:
                if transitions:
                    for trans in transitions:
                        n_seq = trans.get("NextSequenceIndex")
                        if n_seq is not None:
                            traverse(n_seq, indent_level, stop_seqs)
                else:
                    # Proceed linearly if no transitions are defined
                    traverse(seq_idx + 1, indent_level, stop_seqs)

        traverse(0, 1, set())
        
    return output_lines

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Extract dialogues for a given QuestId")
    parser.add_argument("quest_id", type=int, help="QuestId to extract dialogues for")
    args = parser.parse_args()

    with open("plothandbookconfig.json", "r", encoding="utf-8") as f:
        plothb_data = json.load(f)
        
    multitext_dict = {}
    for filename in ["MultiText.json", "MultiText_1.json", "MultiText_2.json"]:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if item.get("Id"):
                        if filename == "MultiText.json" and item.get("RedirectDbIndex") == 1:
                            continue
                        multitext_dict[item.get("Id")] = item.get("Content")
        except FileNotFoundError:
            print(f"Please download and put {filename} to current directory")
            sys.exit(1)
        
    quest_data_str = None
    for item in plothb_data:
        if item.get("QuestId") == args.quest_id:
            quest_data_str = item.get("Data")
            break
            
    if not quest_data_str:
        print(f"QuestId {args.quest_id} not found in plothandbookconfig.json")
        sys.exit(1)
        
    parsed_data = parse_json_string(quest_data_str)
    
    state_keys = []
    for item in parsed_data:
        flow = item.get("Flow", {})
        flow_list_name = flow.get("FlowListName", "")
        flow_id = flow.get("FlowId", 0)
        state_id = flow.get("StateId", 0)
        
        if not flow_list_name:
            continue
            
        state_key = f"{flow_list_name}_{flow_id}_{state_id}"
        state_keys.append(state_key)
        
    if not state_keys:
        print(f"No valid state keys found for QuestId {args.quest_id}.")
        sys.exit(0)
        
    try:
        actions_dict = get_actions_for_state_keys("flowstate.json", state_keys)
    except FileNotFoundError:
        print("flowstate.json not found.")
        sys.exit(1)
        
    first_print = True
    for state_key in state_keys:
        action_string = actions_dict.get(state_key)
        if action_string:
            parsed_actions = parse_json_string(action_string)
            lines = get_talk_flow_lines(parsed_actions, multitext_dict)
            if lines:
                if not first_print:
                    print("==========")
                for line in lines:
                    print(line)
                first_print = False
