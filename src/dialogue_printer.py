from utils import parse_json_string
from flow_parser import get_talk_flow_lines

def print_dialogues(state_keys, state_key_tips, actions_dict, multitext_dict, show_state_keys=False):
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
                    
                if show_state_keys:
                    print(f"; StateKey: {state_key}")
                    
                tip_key = state_key_tips.get(state_key, "")
                if tip_key and tip_key != last_printed_tip:
                    translated_tip = multitext_dict.get(tip_key, tip_key)
                    if translated_tip.strip():
                        print(f";{translated_tip}")
                    last_printed_tip = tip_key
                    
                for line in lines:
                    print(line)
                first_print = False
