from utils import parse_json_string

def get_quest_state_keys(quest_id, plothb_data):
    quest_data_str = None
    for item in plothb_data:
        if item.get("QuestId") == quest_id:
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
            
    return state_keys, state_key_tips
