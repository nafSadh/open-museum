#!/usr/bin/env python3
"""
Resolve Wikimedia Commons image URLs for artworks in wiki_works_raw.json.

Uses the Wikimedia Commons API to fetch image info (full URL, thumbnail URL,
description page URL) for each artwork that has a commons_filename.

Outputs: behzad/catalog.json
"""

import json
import time
import urllib.request
import urllib.parse

INPUT_PATH = "behzad/wiki_works_raw.json"
OUTPUT_PATH = "behzad/catalog.json"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
BATCH_SIZE = 50  # API limit per request
THUMB_WIDTH = 800  # thumbnail width in pixels


def fetch_image_info(filenames: list[str]) -> dict:
    """Fetch image info for a batch of filenames from Commons API."""
    titles = "|".join(f"File:{fn}" for fn in filenames)
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": titles,
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": str(THUMB_WIDTH),
        "format": "json",
    })
    url = f"{COMMONS_API}?{params}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "open-museum/1.0 (art catalog project)"
    })

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  API error: {e}")
        return {}

    results = {}
    pages = data.get("query", {}).get("pages", {})
    for page_id, page_data in pages.items():
        if int(page_id) < 0:
            continue  # missing page
        title = page_data.get("title", "")
        # Strip "File:" prefix and normalize spaces to underscores
        fname = title[5:] if title.startswith("File:") else title
        fname = fname.replace(" ", "_")
        ii = page_data.get("imageinfo", [{}])[0]
        results[fname] = {
            "image_url": ii.get("url", ""),
            "thumb_url": ii.get("thumburl", ""),
            "commons_page": ii.get("descriptionurl", ""),
            "width": ii.get("width"),
            "height": ii.get("height"),
            "mime": ii.get("mime", ""),
        }
    return results


def main():
    print(f"Loading {INPUT_PATH}")
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        works = json.load(f)
    print(f"Loaded {len(works)} works")

    # Collect unique filenames — normalize to underscores for matching
    def norm_fn(fn):
        return fn.replace(" ", "_")

    filenames_to_resolve = []
    fname_to_indices = {}  # normalized_filename -> [indices]
    for i, work in enumerate(works):
        fn = work.get("commons_filename")
        if fn:
            key = norm_fn(fn)
            if key not in fname_to_indices:
                fname_to_indices[key] = []
                filenames_to_resolve.append(fn)  # keep original for API
            fname_to_indices[key].append(i)

    print(f"Need to resolve {len(filenames_to_resolve)} unique Commons filenames")

    # Batch API calls
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
            time.sleep(0.5)  # be polite to the API

    print(f"Resolved {len(resolved)} filenames")

    # Merge resolved data back into works (resolved keys are already underscore-normalized)
    resolved_count = 0
    for key, indices in fname_to_indices.items():
        if key in resolved:
            for i in indices:
                info = resolved[key]
                works[i]["image_url"] = info.get("image_url", "")
                works[i]["thumb_url"] = info.get("thumb_url", "")
                works[i]["commons_page"] = info.get("commons_page", "")
                works[i]["image_width"] = info.get("width")
                works[i]["image_height"] = info.get("height")
                resolved_count += 1

    print(f"Updated {resolved_count} work entries with image URLs")

    # Add sequential ID
    for i, work in enumerate(works):
        work["id"] = i + 1

    # Write output
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(works, f, ensure_ascii=False, indent=2)
    print(f"\nWritten {len(works)} works to {OUTPUT_PATH}")

    # Stats
    with_full_url = sum(1 for w in works if w.get("image_url"))
    with_thumb = sum(1 for w in works if w.get("thumb_url"))
    print(f"With full image URL: {with_full_url}")
    print(f"With thumbnail URL: {with_thumb}")


if __name__ == "__main__":
    main()
