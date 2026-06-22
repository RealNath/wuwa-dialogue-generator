import argparse
from urllib import request
import urllib
import urllib.request
import json
import concurrent.futures
import argparse

def get_latest_version(url: str = "https://api.github.com/repos/Arikatsu/WutheringWaves_Data"):
    with request.urlopen(url) as res:
        data = json.loads(res.read().decode())
        return data["default_branch"]

def download_file(file_info: tuple):
    url, filename = file_info
    print(f"Downloading {filename}...")
    request.urlretrieve(url, filename)
    print(f"Finished downloading {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download the required json files")
    parser.add_argument("game_version", type=float, help="The version of the game's data (the name of the Arikatsu repo's branch)")
    parser.add_argument("language", type=str, help="The language of the MultiText - [de,en,es,fr,id,ja,ko,pt,ru,th,vi,zh-Hans,zh-Hant]")
    args = parser.parse_args()

    ver = args.game_version
    lang = args.language

    flow = f"https://raw.githubusercontent.com/Arikatsu/WutheringWaves_Data/{ver}/BinData/flow/flow.json"
    flowstate = f"https://raw.githubusercontent.com/Arikatsu/WutheringWaves_Data/{ver}/BinData/flowState/flowstate.json"
    plot_handbook = f"https://raw.githubusercontent.com/Arikatsu/WutheringWaves_Data/{ver}/BinData/PlotHandBook/plothandbookconfig.json"
    multi_text = f"https://raw.githubusercontent.com/Arikatsu/WutheringWaves_Data/{ver}/Textmaps/{lang}/multi_text/MultiText.json"
    multi_text_1sthalf = f"https://raw.githubusercontent.com/Arikatsu/WutheringWaves_Data/{ver}/Textmaps/{lang}/multi_text_1sthalf/MultiText.json"
    multi_text_2ndhalf = f"https://raw.githubusercontent.com/Arikatsu/WutheringWaves_Data/{ver}/Textmaps/{lang}/multi_text_2ndhalf/MultiText.json"

    files = {
        "flow": (flow, "flow.json"),
        "flowstate": (flowstate, "flowstate.json"),
        "plot_handbook": (plot_handbook, "plothandbookconfig.json"),
        "multi_text": (multi_text, "MultiText.json"),
        "multi_text_1sthalf": (multi_text_1sthalf, "MultiText_1.json"),
        "multi_text_2ndhalf": (multi_text_2ndhalf, "MultiText_2.json"),
    }

    # Parallel Download
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(download_file, files.values())