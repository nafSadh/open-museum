import json
from pathlib import Path

ROOT = Path("/Users/nafsadh/src/open-museum")
rrv_path = ROOT / "raja-ravi-varma/catalog.json"
with open(rrv_path, "r", encoding="utf-8") as f:
    rrv_data = json.load(f)

lady_upd = {
    "commons_filename": "Raja_Ravi_Varma,_Reverie.jpg",
    "image_url": "https://upload.wikimedia.org/wikipedia/commons/1/19/Raja_Ravi_Varma%2C_Reverie.jpg",
    "thumb_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Raja_Ravi_Varma%2C_Reverie.jpg/960px-Raja_Ravi_Varma%2C_Reverie.jpg",
    "commons_page": "https://commons.wikimedia.org/wiki/File:Raja_Ravi_Varma,_Reverie.jpg",
    "provenance_url": "https://commons.wikimedia.org/wiki/File:Raja_Ravi_Varma,_Reverie.jpg",
    "image_width": 8108,
    "image_height": 11173
}

for i, entry in enumerate(rrv_data):
    if entry.get("id") == 38:
        new_entry = {}
        new_entry["commons_filename"] = lady_upd["commons_filename"]
        new_entry["title"] = entry["title"]
        new_entry["image_url"] = lady_upd["image_url"]
        new_entry["thumb_url"] = lady_upd["thumb_url"]
        new_entry["commons_page"] = lady_upd["commons_page"]
        new_entry["image_width"] = lady_upd["image_width"]
        new_entry["image_height"] = lady_upd["image_height"]
        
        for k, v in entry.items():
            if k in ("commons_filename", "title", "image_url", "thumb_url", "commons_page", "image_width", "image_height", "provenance_url"):
                continue
            new_entry[k] = v
        new_entry["provenance_url"] = lady_upd["provenance_url"]
        rrv_data[i] = new_entry
        print("Successfully updated entry 38 with all image fields.")
        break

with open(rrv_path, "w", encoding="utf-8") as f:
    json.dump(rrv_data, f, ensure_ascii=False, indent=2)
    f.write("\n")
