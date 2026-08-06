import re

def format_dialogue(character_name: str, dialogue: str, prefix: str = "_", multitext_dict: dict = None) -> str:
    if multitext_dict is None:
        multitext_dict = {}
        
    if prefix == "dicon":
        dicon = "{{DIcon}}"
        line = f"{dicon} {dialogue}"
    elif prefix == "center":
        line = f"'''{dialogue}'''"
        line = line.replace("{PlayerName}", "{{Rover}}")
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
