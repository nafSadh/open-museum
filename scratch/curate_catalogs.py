import json
from pathlib import Path

ROOT = Path("/Users/nafsadh/src/open-museum")

# 1. Update Amrita Sher-Gil catalog
asg_path = ROOT / "amrita-sher-gil/catalog.json"
with open(asg_path, "r", encoding="utf-8") as f:
    asg_data = json.load(f)

asg_updates = {
    45: {
        "commons_filename": "Amrita_Sher-Gil_Hungarian-gypsy-girl.jpg",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/c/c3/Amrita_Sher-Gil_Hungarian-gypsy-girl.jpg",
        "thumb_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Amrita_Sher-Gil_Hungarian-gypsy-girl.jpg/960px-Amrita_Sher-Gil_Hungarian-gypsy-girl.jpg",
        "commons_page": "https://commons.wikimedia.org/wiki/File:Amrita_Sher-Gil_Hungarian-gypsy-girl.jpg",
        "provenance_url": "https://commons.wikimedia.org/wiki/File:Amrita_Sher-Gil_Hungarian-gypsy-girl.jpg",
        "image_width": 6470,
        "image_height": 4192
    },
    68: {
        "commons_filename": "Professional_Model_1933.jpg",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/d/d2/Professional_Model_1933.jpg",
        "thumb_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Professional_Model_1933.jpg/960px-Professional_Model_1933.jpg",
        "commons_page": "https://commons.wikimedia.org/wiki/File:Professional_Model_1933.jpg",
        "provenance_url": "https://commons.wikimedia.org/wiki/File:Professional_Model_1933.jpg",
        "image_width": 4928,
        "image_height": 6926
    },
    120: {
        "commons_filename": "Two_Medicants_1937.jpg",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/8/87/Two_Medicants_1937.jpg",
        "thumb_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Two_Medicants_1937.jpg/960px-Two_Medicants_1937.jpg",
        "commons_page": "https://commons.wikimedia.org/wiki/File:Two_Medicants_1937.jpg",
        "provenance_url": "https://commons.wikimedia.org/wiki/File:Two_Medicants_1937.jpg",
        "image_width": 1507,
        "image_height": 1994
    },
    126: {
        "commons_filename": "Amrita_Sher-Gil_Ancient_Story_Teller_1940_Saraya.jpg",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/b/b4/Amrita_Sher-Gil_Ancient_Story_Teller_1940_Saraya.jpg",
        "thumb_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Amrita_Sher-Gil_Ancient_Story_Teller_1940_Saraya.jpg/960px-Amrita_Sher-Gil_Ancient_Story_Teller_1940_Saraya.jpg",
        "commons_page": "https://commons.wikimedia.org/wiki/File:Amrita_Sher-Gil_Ancient_Story_Teller_1940_Saraya.jpg",
        "provenance_url": "https://commons.wikimedia.org/wiki/File:Amrita_Sher-Gil_Ancient_Story_Teller_1940_Saraya.jpg",
        "image_width": 3456,
        "image_height": 4265
    }
}

asg_field_order = ["commons_filename", "title", "date", "current_location", "image_url", "thumb_url", "commons_page", "image_width", "image_height"]

for entry in asg_data:
    eid = entry.get("id")
    if eid in asg_updates:
        # Update entry fields preserving general schema placement
        upd = asg_updates[eid]
        # Reconstruct entry with correct field order
        new_entry = {}
        # Put commons_filename right before title
        new_entry["commons_filename"] = upd["commons_filename"]
        for k, v in entry.items():
            if k == "commons_filename":
                continue
            new_entry[k] = v
            if k == "date":
                new_entry["image_url"] = upd["image_url"]
                new_entry["thumb_url"] = upd["thumb_url"]
                new_entry["commons_page"] = upd["commons_page"]
                new_entry["image_width"] = upd["image_width"]
                new_entry["image_height"] = upd["image_height"]
        # Make sure provenance_url is set or updated
        new_entry["provenance_url"] = upd["provenance_url"]
        
        # Replace the original entry
        idx = asg_data.index(entry)
        asg_data[idx] = new_entry
        print(f"Updated Amrita Sher-Gil entry id={eid}: {new_entry['title']}")

with open(asg_path, "w", encoding="utf-8") as f:
    json.dump(asg_data, f, ensure_ascii=False, indent=2)
    f.write("\n")


# 2. Update Raja Ravi Varma catalog
rrv_path = ROOT / "raja-ravi-varma/catalog.json"
with open(rrv_path, "r", encoding="utf-8") as f:
    rrv_data = json.load(f)

# Find Lady Lost in Thought (id=38) and update it
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
        for k, v in entry.items():
            if k == "commons_filename":
                continue
            new_entry[k] = v
            if k == "date":
                new_entry["image_url"] = lady_upd["image_url"]
                new_entry["thumb_url"] = lady_upd["thumb_url"]
                new_entry["commons_page"] = lady_upd["commons_page"]
                new_entry["image_width"] = lady_upd["image_width"]
                new_entry["image_height"] = lady_upd["image_height"]
        new_entry["provenance_url"] = lady_upd["provenance_url"]
        rrv_data[i] = new_entry
        print("Updated Raja Ravi Varma entry id=38: Lady Lost in Thought")
        break

# Filter out duplicates
duplicates = {36, 39, 40, 41, 44, 45, 47, 48, 50, 51, 52, 54}
rrv_clean = [e for e in rrv_data if e.get("id") not in duplicates]
print(f"Removed {len(rrv_data) - len(rrv_clean)} duplicate entries from Raja Ravi Varma catalog.")

with open(rrv_path, "w", encoding="utf-8") as f:
    json.dump(rrv_clean, f, ensure_ascii=False, indent=2)
    f.write("\n")
