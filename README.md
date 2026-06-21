# Wuthering Waves Dialogue Generator (and Formatter)

This is a program that helps you automatically generate the dialogue transcriptions of each Wuthering Waves quests. Do note that this may not include a few stuffs like WavesLine chats, dialogues during the regular walking/fighting, some NPC convo (the ones without custom camera movement), as that's missing in the flowstate. But it should do 85%+ of the job.

This is made especially for Wuthering Waves Fandom Wiki, but anyone else are welcomed to use it.

## How to use

1. Clone this repo, or download it as a zip.
    ```bash
    git clone https://github.com/RealNath/wuwa-dialogue-extractor.git
    cd src
    ```

2. Download the following files from the [arikatsu](https://github.com/Arikatsu/WutheringWaves_Data) repo at minimum:
    - `BinData/flow/flow.json`
    - `BinData/flowState/flowstate.json`
    - `BinData/PlotHandBook/plothandbookconfig.json`
    - `Textmaps/{lang}/multi_text/MultiText.json`
    - `Textmaps/{lang}/multi_text_1sthalf/MultiText.json`
        * Rename to MultiText_1.json
    - `Textmaps/{lang}/multi_text_2ndhalf/MultiText.json`
        * Rename to MultiText_2.json

3. Put them at the same folder as extract_dialogue.py (e.g at `src`).

4. Run this command:
    ```bash
    python extract_dialogue.py {QuestId}
    ```
    * QuestId can be seen at plothandbookconfig.json
    * The string/actual name of the quest can be seen at `MultiText.json`:
        * Search for `Quest_{QuestId}_QuestName`, see the value of `Content`.
        * Or you can search for the complete quest name, surrounded by quotation marks `"..."`, see the one that has `"Id": "Quest_{QuestId}_QuestName_..."` on the previous line.
    
    For example: `python extract_dialogue.py 119000000`