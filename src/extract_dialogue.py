import sys
import argparse
from pathlib import Path
from utils import get_actions_and_missing_keys, interleave_missing_keys
from flow_parser import get_node_sequence
from data_loader import load_plothandbookconfig, load_multitext
from quest_processor import get_quest_state_keys
from dialogue_printer import print_dialogues

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract dialogues for a given QuestId")
    parser.add_argument("quest_id", type=int, help="QuestId to extract dialogues for")
    parser.add_argument("--show-state-keys", action="store_true", help="Show the StateKey of each part of the dialogue")
    parser.add_argument("--show-missing-keys", action="store_true", help="Show dialogue lines of StateKeys not found in the data (same FlowListName)")
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

    actions_dict, missing_keys = get_actions_and_missing_keys(state_keys)
    
    if args.show_missing_keys:
        final_keys, unplaced_keys = interleave_missing_keys(state_keys, missing_keys)
    else:
        final_keys = state_keys
        unplaced_keys = []
    
    print_dialogues(final_keys, state_key_tips, actions_dict, multitext_dict, show_state_keys=args.show_state_keys)

    if args.show_missing_keys and unplaced_keys:
        print("\n" + "="*50)
        print("MISSING FROM EXTRACTED DATA")
        print("="*50)
        print_dialogues(unplaced_keys, {}, actions_dict, multitext_dict, show_state_keys=args.show_state_keys)
