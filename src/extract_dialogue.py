import sys
import os
import argparse
from json import encoder
import json
import re
from typing import List

def format_dialogue(character_name: str, dialogue: str, prefix: str = "_", multitext_dict: dict = None) -> str:
    if multitext_dict is None:
        multitext_dict = {}
        
    if prefix == "dicon":
        dicon = "{{DIcon}}"
        line = f"{dicon} {dialogue}"
    else:
        line = f"'''{character_name}:''' {dialogue}"
        line = line.replace("{PlayerName}", "{{Rover}}")
    
    # Replace <b>X</b> with '''X'''
    line = re.sub(r'<b>(.*?)</b>', r"'''\1'''", line)

    # Replace {Male=X;Female=Y} with {{MC|m=X|f=Y}}
    line = re.sub(r'\{Male=(.*?);Female=(.*?)\}', r'{{MC|m=\1|f=\2}}', line)

    # Replace <ano=Y>X</ano> with {{Rubi|X|Y}}
    line = re.sub(r'<ano=(.*?)>(.*?)</ano>', r'{{Rubi|\2|\1}}', line)
    
    # Replace <te href=(number)>X</te> with {{Extra Effect|Text|Title|Description}}
    def replace_te(match):
        term_id = match.group(1)
        text = match.group(2)
        title = multitext_dict.get(f"Term{term_id}_Title", "")
        desc = multitext_dict.get(f"Term{term_id}_Desc", "")
        return f"{{{{Extra Effect|{text}|{title}|{desc}}}}}"
        
    line = re.sub(r'<te href=(\d+)>(.*?)</te>', replace_te, line)
    
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
        # Dump the parsed_data (list/dict)
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
        talk_items_list = params.get("TalkItems", [])
        talk_items = {item["Id"]: item for item in talk_items_list}
        talk_sequence = params.get("TalkSequence", [])
        
        # If a quest doesn't have TalkSequence
        if not talk_sequence and talk_items_list:
            talk_sequence = [[item["Id"] for item in talk_items_list]]
            
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
                    
                    formatted_dialogue = format_dialogue(character_name, dialogue, multitext_dict=multitext_dict)
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
                                dialogue_line = format_dialogue("_", translated_opt, "dicon", multitext_dict)
                                output_lines.append(f"{indent}{dialogue_line}")
            
            if has_branching_options:
                next_seqs = set()
                
                for opt, branch_seq_idx in options_to_branch:
                    opt_tid = opt.get("TidTalkOption")
                    if opt_tid:
                        translated_opt = multitext_dict.get(opt_tid, opt_tid)
                        dialogue_line = format_dialogue("_", translated_opt, "dicon", multitext_dict)
                        output_lines.append(f"{indent}{dialogue_line}")
                        
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

def get_node_sequence(quest_id: int, questnodedata_path: str):
    with open(questnodedata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    nodes = {}
    for item in data:
        key = item.get("Key", "")
        if key.startswith(f"{quest_id}_"):
            node_data = item.get("Data", {})
            node_id = node_data.get("Id")
            if node_id is not None:
                nodes[node_id] = node_data
                
    if not nodes:
        return [], {}

    # Find root node(s)
    root_nodes = [n for n in nodes.values() if n.get("ParentNodeId") == 0]
    if not root_nodes:
        # Fallback: find nodes whose parent doesn't exist in this quest's nodes
        root_nodes = [n for n in nodes.values() if n.get("ParentNodeId") not in nodes]

    children_map = {}
    for node_id, node in nodes.items():
        parent_id = node.get("ParentNodeId")
        if parent_id not in children_map:
            children_map[parent_id] = []
        children_map[parent_id].append(node_id)
        
    state_keys = []
    state_key_tips = {}
    visited = set()
    
    def extract_play_flow_states(obj, current_tip):
        if isinstance(obj, dict):
            # Check if this dict represents a flow state
            flow_list = obj.get("FlowListName")
            flow_id = obj.get("FlowId")
            state_id = obj.get("StateId")
            if flow_list and flow_id is not None and state_id is not None:
                state_key = f"{flow_list}_{flow_id}_{state_id}"
                if state_key not in state_keys:
                    state_keys.append(state_key)
                    state_key_tips[state_key] = current_tip
            
            # Recursively check values
            for value in obj.values():
                extract_play_flow_states(value, current_tip)
        elif isinstance(obj, list):
            for item in obj:
                extract_play_flow_states(item, current_tip)

    def traverse(node_id, current_tip):
        if node_id in visited:
            return
        visited.add(node_id)
        
        node = nodes.get(node_id)
        if not node:
            return
            
        tid_tip = node.get("TidTip", "")
        if tid_tip:
            current_tip = tid_tip
            
        extract_play_flow_states(node, current_tip)
        
        for child_id in children_map.get(node_id, []):
            traverse(child_id, current_tip)

    for root in root_nodes:
        traverse(root.get("Id"), "")

    return state_keys, state_key_tips

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract dialogues for a given QuestId")
    parser.add_argument("quest_id", type=int, help="QuestId to extract dialogues for")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    plothb_path = os.path.join(base_dir, "BinData", "PlotHandBook", "plothandbookconfig.json")
    if not os.path.exists(plothb_path):
        plothb_path = "plothandbookconfig.json"

    try:
        with open(plothb_path, "r", encoding="utf-8") as f:
            plothb_data = json.load(f)
    except FileNotFoundError:
        print(f"plothandbookconfig.json not found in {plothb_path}.")
        sys.exit(1)
        
    multitext_dict = {}
    for filename in ["MultiText.json", "MultiText_1.json", "MultiText_2.json"]:
        filepath = os.path.join(script_dir, filename) if os.path.exists(os.path.join(script_dir, filename)) else filename
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if item.get("Id"):
                        if filename == "MultiText.json" and item.get("RedirectDbIndex") == 1:
                            continue
                        multitext_dict[item.get("Id")] = item.get("Content")
        except FileNotFoundError:
            print(f"Please download and put {filename} to appropriate directory")
            sys.exit(1)
        
    quest_data_str = None
    for item in plothb_data:
        if item.get("QuestId") == args.quest_id:
            quest_data_str = item.get("Data")
            break
            
    state_keys = []
    state_key_tips = {}
    current_tip = ""
    
    if quest_data_str:
        parsed_data = parse_json_string(quest_data_str)
        for item in parsed_data:
            tid_tip = item.get("TidTip", "")
            if tid_tip:
                current_tip = tid_tip
                
            flow = item.get("Flow", {})
            flow_list_name = flow.get("FlowListName", "")
            flow_id = flow.get("FlowId", 0)
            state_id = flow.get("StateId", 0)
            
            if not flow_list_name:
                continue
                
            state_key = f"{flow_list_name}_{flow_id}_{state_id}"
            state_keys.append(state_key)
            state_key_tips[state_key] = current_tip
    else:
        print(f"QuestId {args.quest_id} not found in plothandbookconfig. Falling back to questnodedata.json...")
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)
        questnodedata_path = os.path.join(base_dir, "BinData", "QuestNodeData", "questnodedata.json")
        if not os.path.exists(questnodedata_path):
            questnodedata_path = "questnodedata.json"
            
        try:
            state_keys, state_key_tips = get_node_sequence(args.quest_id, questnodedata_path)
        except FileNotFoundError:
            print(f"{questnodedata_path} not found.")
            sys.exit(1)
        
    if not state_keys:
        print(f"No valid state keys found for QuestId {args.quest_id}.")
        sys.exit(0)
        
    flowstate_path = os.path.join(base_dir, "BinData", "flowState", "flowstate.json")
    if not os.path.exists(flowstate_path):
        flowstate_path = "flowstate.json"
        
    try:
        actions_dict = get_actions_for_state_keys(flowstate_path, state_keys)
    except FileNotFoundError:
        print(f"{flowstate_path} not found.")
        sys.exit(1)
        
    first_print = True
    last_printed_tip = ""
    for state_key in state_keys:
        action_string = actions_dict.get(state_key)
        if action_string:
            parsed_actions = parse_json_string(action_string)
            lines = get_talk_flow_lines(parsed_actions, multitext_dict)
            if lines:
                if not first_print:
                    print("----")
                    
                tip_key = state_key_tips.get(state_key, "")
                if tip_key and tip_key != last_printed_tip:
                    translated_tip = multitext_dict.get(tip_key, tip_key)
                    if translated_tip.strip():
                        print(f";{translated_tip}")
                    last_printed_tip = tip_key
                    
                for line in lines:
                    print(line)
                first_print = False
