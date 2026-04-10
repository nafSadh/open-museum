#!/usr/bin/env python3
"""
Re-resolve Commons URLs for catalog entries that have a commons_filename
but are missing thumb_url / image_url.

Reads/writes monet/catalog.json in place.
"""

import json, time, urllib.request, urllib.parse, os

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "catalog.json",
)
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
BATCH_SIZE  = 50
THUMB_WIDTH = 800


def fetch_image_info(filenames):
    titles = "|".join(f"File:{fn}" for fn in filenames)
    params = urllib.parse.urlencode({
        "action": "query", "titles": titles,
        "prop": "imageinfo", "iiprop": "url|size",
        "iiurlwidth": str(THUMB_WIDTH), "format": "json",
    })
    req = urllib.request.Request(
        f"{COMMONS_API}?{params}",
        headers={"User-Agent": "open-museum/1.0 (art catalog project)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  API error: {e}")
        return {}

    results = {}
    for page_id, page in data.get("query", {}).get("pages", {}).items():
        if int(page_id) < 0:
            continue
        raw = page.get("title", "")[5:]  # strip "File:"
        for key in (raw, raw.replace(" ", "_"), urllib.parse.unquote(raw.replace(" ", "_"))):
            ii = (page.get("imageinfo") or [{}])[0]
            results[key] = {
                "image_url":   ii.get("url", ""),
                "thumb_url":   ii.get("thumburl", ""),
                "commons_page": ii.get("descriptionurl", ""),
                "image_width":  ii.get("width"),
                "image_height": ii.get("height"),
            }
    return results


def main():
    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)

    # Gather entries missing thumb_url but having a filename
    missing = [(i, w) for i, w in enumerate(catalog)
               if w.get("commons_filename") and not w.get("thumb_url")]
    print(f"Entries to fix: {len(missing)}")

    if not missing:
        print("Nothing to do.")
        return

    # Build unique filename list
    fnames_order = []
    fname_to_idxs = {}
    for i, w in missing:
        fn = w["commons_filename"].replace(" ", "_")
        if fn not in fname_to_idxs:
            fname_to_idxs[fn] = []
            fnames_order.append(fn)
        fname_to_idxs[fn].append(i)

    print(f"Unique filenames: {len(fnames_order)}")

    # Batch resolve
    resolved = {}
    batches = (len(fnames_order) + BATCH_SIZE - 1) // BATCH_SIZE
    for b in range(batches):
        batch = fnames_order[b * BATCH_SIZE:(b + 1) * BATCH_SIZE]
        print(f"  Batch {b+1}/{batches} ({len(batch)} files)")
        resolved.update(fetch_image_info(batch))
        if b < batches - 1:
            time.sleep(0.5)

    # Patch catalog
    fixed = 0
    for fn, idxs in fname_to_idxs.items():
        info = resolved.get(fn) or resolved.get(urllib.parse.unquote(fn))
        if info and info.get("thumb_url"):
            for i in idxs:
                catalog[i].update(info)
                fixed += 1
        else:
            print(f"  Still unresolved: {fn}")

    print(f"\nFixed {fixed} / {len(missing)} entries")

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"Written {CATALOG_PATH}")

    total_img = sum(1 for w in catalog if w.get("thumb_url"))
    print(f"Total with thumbnail: {total_img} / {len(catalog)}")


if __name__ == "__main__":
    main()
