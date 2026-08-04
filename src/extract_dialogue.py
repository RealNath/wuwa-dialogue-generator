import sys
import argparse
from pathlib import Path
from utils import get_actions_for_state_keys
from flow_parser import get_node_sequence
from data_loader import load_plothandbookconfig, load_multitext
from quest_processor import get_quest_state_keys
from dialogue_printer import print_dialogues

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract dialogues for a given QuestId")
    parser.add_argument("quest_id", type=int, help="QuestId to extract dialogues for")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent

    plothb_data = load_plothandbookconfig(base_dir)
    multitext_dict = load_multitext(base_dir)

    state_keys, state_key_tips = get_quest_state_keys(args.quest_id, plothb_data)

    if not state_keys:
        print(f"QuestId {args.quest_id} not found in plothandbookconfig. Falling back to questnodedata.json...")
        state_keys, state_key_tips = get_node_sequence(args.quest_id)

    if not state_keys:
        print(f"No valid state keys found for QuestId {args.quest_id}.")
        sys.exit(0)

    actions_dict = get_actions_for_state_keys(state_keys)
        
    print_dialogues(state_keys, state_key_tips, actions_dict, multitext_dict)
