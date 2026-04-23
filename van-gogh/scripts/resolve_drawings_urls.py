#!/usr/bin/env python3
"""
Resolve Wikimedia Commons image URLs for Van Gogh drawings.

Adapted from resolve_commons_urls.py. Reads wiki_drawings_raw.json,
queries Commons imageinfo in batches (50 per call, 1 s sleep between
calls per task spec), and writes the enriched file back in place.

Per the task spec:
  - User-Agent "open-museum/1.0 vg-drawings"
  - 1 s sleep between Commons requests

Outputs: van-gogh/wiki_drawings_raw.json (with image_url, thumb_url, etc.)
"""

import json
import time
import urllib.request
import urllib.parse

IN_OUT_PATH = "van-gogh/wiki_drawings_raw.json"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
BATCH_SIZE = 50
THUMB_WIDTH = 800
USER_AGENT = "open-museum/1.0 vg-drawings"


def fetch_image_info(filenames: list) -> dict:
    titles = "|".join(f"File:{fn}" for fn in filenames)
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": titles,
        "prop": "imageinfo",
        "iiprop": "url|size|mime",
        "iiurlwidth": str(THUMB_WIDTH),
        "format": "json",
    })
    url = f"{COMMONS_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  API error: {e}")
        return {}

    results = {}
    pages = data.get("query", {}).get("pages", {})
    # API may normalize names (spaces <-> underscores, %XX decoding). Use the
    # returned "title" to map back.
    normalized = {n["to"]: n["from"] for n in data.get("query", {}).get("normalized", [])}
    for page_id, page_data in pages.items():
        if int(page_id) < 0:
            continue
        title = page_data.get("title", "")
        fname = title[5:] if title.startswith("File:") else title
        # Preserve the original input filename under which we stored the request
        # so callers can look it up. The Commons API normalizes spaces → underscores.
        fname_us = fname.replace(" ", "_")
        ii_list = page_data.get("imageinfo", [])
        if not ii_list:
            continue
        ii = ii_list[0]
        entry = {
            "image_url": ii.get("url", ""),
            "thumb_url": ii.get("thumburl", ""),
            "commons_page": ii.get("descriptionurl", ""),
            "width": ii.get("width"),
            "height": ii.get("height"),
            "mime": ii.get("mime", ""),
        }
        # Store under both normalized forms (API often returns space-form title)
        results[fname_us] = entry
        results[fname] = entry
        # Also store under any inbound pre-normalization forms
        if title in normalized:
            src = normalized[title]
            if src.startswith("File:"):
                src = src[5:]
            results[src] = entry
            results[src.replace(" ", "_")] = entry
    return results


def main():
    print(f"Loading {IN_OUT_PATH}")
    with open(IN_OUT_PATH, "r", encoding="utf-8") as f:
        works = json.load(f)
    print(f"Loaded {len(works)} drawings")

    # Collect unique filenames
    fname_to_indices = {}
    filenames_to_resolve = []
    for i, w in enumerate(works):
        fn = w.get("commons_filename")
        if fn:
            if fn not in fname_to_indices:
                fname_to_indices[fn] = []
                filenames_to_resolve.append(fn)
            fname_to_indices[fn].append(i)
    print(f"Need to resolve {len(filenames_to_resolve)} unique Commons filenames")

    resolved = {}
    total_batches = (len(filenames_to_resolve) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_num in range(total_batches):
        start = batch_num * BATCH_SIZE
        end = start + BATCH_SIZE
        batch = filenames_to_resolve[start:end]
        print(f"  Batch {batch_num + 1}/{total_batches} ({len(batch)} files)")
        batch_results = fetch_image_info(batch)
        resolved.update(batch_results)
        if batch_num < total_batches - 1:
            time.sleep(1.0)  # per task spec

    print(f"Resolved {len(resolved)} filename keys")

    # Merge results back
    resolved_count = 0
    missing = 0
    for fn, indices in fname_to_indices.items():
        info = resolved.get(fn) or resolved.get(fn.replace("_", " "))
        if not info or not info.get("image_url"):
            missing += 1
            continue
        for i in indices:
            works[i]["image_url"] = info.get("image_url", "")
            works[i]["thumb_url"] = info.get("thumb_url", "")
            works[i]["commons_page"] = info.get("commons_page", "")
            works[i]["image_width"] = info.get("width")
            works[i]["image_height"] = info.get("height")
            resolved_count += 1

    print(f"Merged info into {resolved_count} entries; {missing} filenames unresolved")

    with open(IN_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(works, f, ensure_ascii=False, indent=2)
    print(f"Written back to {IN_OUT_PATH}")

    with_full = sum(1 for w in works if w.get("image_url"))
    print(f"With full image URL: {with_full} / {len(works)}")


if __name__ == "__main__":
    main()
