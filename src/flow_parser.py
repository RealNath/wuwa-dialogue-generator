import json
from pathlib import Path
from formatting import format_dialogue
from data_loader import load_questnodedata

def get_base_dir():
    return Path(__file__).resolve().parent.parent

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
            entry_points = {talk_items_list[0]["Id"]}
            for item in talk_items_list:
                for opt in item.get("Options", []):
                    for action in opt.get("Actions", []):
                        if action.get("Name") == "JumpTalk":
                            t_id = action.get("Params", {}).get("TalkId")
                            if t_id is not None:
                                entry_points.add(t_id)
                for action in item.get("Actions", []):
                    if action.get("Name") == "JumpTalk":
                        t_id = action.get("Params", {}).get("TalkId")
                        if t_id is not None:
                            entry_points.add(t_id)

            built_sequences = []
            current_seq = []
            for item in talk_items_list:
                item_id = item["Id"]
                if item_id in entry_points and current_seq:
                    built_sequences.append(current_seq)
                    current_seq = []
                
                current_seq.append(item_id)
                ends_sequence = False
                if item.get("Options"):
                    ends_sequence = True
                else:
                    for action in item.get("Actions", []):
                        if action.get("Name") in ("JumpTalk", "FinishTalk"):
                            ends_sequence = True
                
                if ends_sequence:
                    built_sequences.append(current_seq)
                    current_seq = []
                    
            if current_seq:
                built_sequences.append(current_seq)
            talk_sequence = built_sequences
            
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
                    
            # Check last item for JumpTalk or FinishTalk
            if b_seq:
                last_item = talk_items.get(b_seq[-1])
                if last_item:
                    for action in last_item.get("Actions", []):
                        if action.get("Name") == "JumpTalk":
                            target_talk_id = action.get("Params", {}).get("TalkId")
                            return talk_id_to_seq_idx.get(target_talk_id)
                        elif action.get("Name") == "FinishTalk":
                            return None
                            
                    options = last_item.get("Options", [])
                    if len(options) == 1:
                        for action in options[0].get("Actions", []):
                            if action.get("Name") == "JumpTalk":
                                target_talk_id = action.get("Params", {}).get("TalkId")
                                return talk_id_to_seq_idx.get(target_talk_id)
                            elif action.get("Name") == "FinishTalk":
                                return None
                    elif len(options) > 1:
                        return None
            
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
                item_type = item.get("Type")
                if tid_talk:
                    character_name = multitext_dict.get(f"Speaker_{who_id}_Name", who_id) if who_id else ""
                    dialogue = multitext_dict.get(tid_talk, tid_talk)
                    
                    prefix = "center" if item_type == "CenterText" else "_"
                    formatted_dialogue = format_dialogue(character_name, dialogue, prefix=prefix, multitext_dict=multitext_dict)
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

def get_node_sequence(quest_id: int):
    data = load_questnodedata(get_base_dir())
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
