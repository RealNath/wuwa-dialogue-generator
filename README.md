# Wuthering Waves Dialogue Extractor (and Formatter)

This is a program that helps you automatically output the dialogue format of each Wuthering Waves quests. Do note that this may not include a few stuffs like WavesLine chats, some NPC convo (the ones without custom camera movement), as that's missing in the flowstate. But it should do 85%+ of the job.

This is made especially for Wuthering Waves Fandom Wiki, but anyone else are welcomed to use it.

## How to use

1. Download the following components from the [arikatsu](https://github.com/Arikatsu/WutheringWaves_Data) repo at minimal:
    - `flow.json`
    - `flowstate.json`
    - `MultiText.json`
    - `plothandbookconfig.json`

2. Run this command:
    ```python
    python extract_dialogue.py {QuestId}
    ```
    * QuestId can be seen at plothandbookconfig.json
    * The string/actual name of the quest can be seen at `MultiText.json`:
        * Search for `Quest_{QuestId}_QuestName`, see the value of `Content`.
        * Or you can search for the complete quest name, surrounded by quotation marks `"..."`, see the one that has `"Id": "Quest_{QuestId}_QuestName_..."` on the previous line.
    
    For example: `python extract_dialogue.py 119000000`