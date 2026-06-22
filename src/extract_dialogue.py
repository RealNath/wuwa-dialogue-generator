from json import encoder
import json
import re
from typing import List

def format_dialogue(character_name: str, dialogue: str) -> str:
    line = f"'''{character_name}:''' {dialogue}"
    line = line.replace("{PlayerName}", "{{Rover}}")
    
    # Replace {Male=X;Female=Y} with {{MC|m=X|f=Y}}
    line = re.sub(r'\{Male=(.*?);Female=(.*?)\}', r'{{MC|m=\1|f=\2}}', line)

    # Replace <ano=Y>X</ano> with {{Rubi|X|Y}}
    line = re.sub(r'<ano=(.*?)>(.*?)</ano>', r'{{Rubi|\2|\1}}', line)
    
    return line

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
        
        talk_id_to_seq_idx = {}
        for s_idx, seq in enumerate(talk_sequence):
            for t_id in seq:
                talk_id_to_seq_idx[t_id] = s_idx
                
        visited = set()
        
        def get_next_seq_from_branch(b_seq_idx):
            if b_seq_idx is None or b_seq_idx >= len(talk_sequence):
                return None
            b_seq = talk_sequence[b_seq_idx]
            b_trans_list = seq_transitions.get(str(b_seq_idx), [])
            
            # Check transitions for unconditional jump
            for trans in b_trans_list:
                if not trans.get("OptionTextKey"):
                    return trans.get("NextSequenceIndex")
                    
            # Check last item for JumpTalk
            if b_seq:
                last_item = talk_items.get(b_seq[-1])
                if last_item:
                    for action in last_item.get("Actions", []):
                        if action.get("Name") == "JumpTalk":
                            target_talk_id = action.get("Params", {}).get("TalkId")
                            return talk_id_to_seq_idx.get(target_talk_id)
            
            # Linear fallback
            return b_seq_idx + 1

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
                    
                    formatted_dialogue = format_dialogue(character_name, dialogue)
                    dialogue_line = f"{indent}{formatted_dialogue}"
                    output_lines.append(dialogue_line)
                    
                if item.get("Options"):
                    options = item.get("Options")
                    
                    branch_targets = []
                    for opt in options:
                        opt_tid = opt.get("TidTalkOption")
                        branch_seq_idx = None
                        
                        # Check SequenceTransition first
                        for trans in transitions:
                            if trans.get("OptionTextKey") == opt.get("PlotLineKey") or trans.get("OptionTextKey") == opt_tid:
                                branch_seq_idx = trans.get("NextSequenceIndex")
                                break
                                
                        # If not found, check JumpTalk instead
                        # (usually for older quests)
                        if branch_seq_idx is None:
                            for action in opt.get("Actions", []):
                                if action.get("Name") == "JumpTalk":
                                    t_id = action.get("Params", {}).get("TalkId")
                                    branch_seq_idx = talk_id_to_seq_idx.get(t_id)
                                    break
                                    
                        branch_targets.append(branch_seq_idx)
                        
                    if any(bt is not None for bt in branch_targets):
                        has_branching_options = True
                        options_to_branch = list(zip(options, branch_targets))
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
                
                for opt, branch_seq_idx in options_to_branch:
                    opt_tid = opt.get("TidTalkOption")
                    if opt_tid:
                        translated_opt = multitext_dict.get(opt_tid, opt_tid)
                        diicon = "{{DIcon}}"
                        output_lines.append(f"{indent}{diicon} {translated_opt}")
                        
                    if branch_seq_idx is not None:
                        n_seq = get_next_seq_from_branch(branch_seq_idx)
                        if n_seq is not None:
                            next_seqs.add(n_seq)
                        
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
                    print("----")
                for line in lines:
                    print(line)
                first_print = False
