#!/usr/bin/env python3
"""
Resolve Wikimedia Commons image URLs for every entry in
cezanne/wiki_works_raw.json. Populates image_url / thumb_url (960 px wide,
the smallest pre-cached size the lightbox uses by default) / commons_page /
image_width / image_height / mime on each entry, then emits a catalog.json
enriched with era, subject, series, date triplet, slug and id.

Usage:  python3 cezanne/scripts/resolve_commons_urls.py
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
COLL_DIR = os.path.dirname(HERE)
INPUT_PATH = os.path.join(COLL_DIR, "wiki_works_raw.json")
OUTPUT_PATH = os.path.join(COLL_DIR, "catalog.json")

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
BATCH_SIZE = 50
THUMB_WIDTH = 960
USER_AGENT = "open-museum/1.0 cezanne-build"
WIKI_LIST_URL = "https://en.wikipedia.org/wiki/List_of_paintings_by_Paul_C%C3%A9zanne"

# Sleep 1s between API requests per spec
SLEEP_SECONDS = 1.0


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
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  API error: {e}")
        return {}

    out = {}
    pages = data.get("query", {}).get("pages", {})
    for pid, page in pages.items():
        if int(pid) < 0:
            continue
        raw_title = page.get("title", "")
        if not raw_title.startswith("File:"):
            continue
        fn = raw_title[5:].replace(" ", "_")
        ii = (page.get("imageinfo") or [{}])[0]
        record = {
            "image_url": ii.get("url", ""),
            "thumb_url": ii.get("thumburl", ""),
            "commons_page": ii.get("descriptionurl", ""),
            "image_width": ii.get("width"),
            "image_height": ii.get("height"),
            "mime": ii.get("mime", ""),
        }
        out[fn] = record
        out[urllib.parse.unquote(fn)] = record
    return out


# ─────────────────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    s = text.lower()
    s = s.replace("'", "").replace("'", "").replace("'", "")
    s = s.replace("ç", "c").replace("é", "e").replace("è", "e").replace("ê", "e")
    s = s.replace("à", "a").replace("â", "a").replace("î", "i").replace("ô", "o")
    s = s.replace("ù", "u").replace("û", "u").replace("ü", "u")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "untitled"


def make_unique(slug: str, seen: dict) -> str:
    if slug not in seen:
        seen[slug] = 1
        return slug
    seen[slug] += 1
    return f"{slug}-{seen[slug]}"


# ─────────────────────────────────────────────────────────────────────
def main():
    print(f"Loading {INPUT_PATH}")
    with open(INPUT_PATH, encoding="utf-8") as f:
        works = json.load(f)
    print(f"Loaded {len(works)} works")

    # Deduplicate filenames
    fname_to_indices = {}
    unique_fnames = []
    for i, w in enumerate(works):
        fn = w.get("commons_filename")
        if not fn:
            continue
        norm = fn.replace(" ", "_")
        if norm not in fname_to_indices:
            fname_to_indices[norm] = []
            unique_fnames.append(norm)
        fname_to_indices[norm].append(i)

    print(f"Need to resolve {len(unique_fnames)} unique filenames")

    resolved = {}
    total_batches = (len(unique_fnames) + BATCH_SIZE - 1) // BATCH_SIZE
    for b in range(total_batches):
        batch = unique_fnames[b * BATCH_SIZE:(b + 1) * BATCH_SIZE]
        print(f"  Batch {b + 1}/{total_batches} ({len(batch)} files)")
        resolved.update(fetch_image_info(batch))
        if b < total_batches - 1:
            time.sleep(SLEEP_SECONDS)

    # Merge
    resolved_count = 0
    for norm, indices in fname_to_indices.items():
        info = resolved.get(norm) or resolved.get(urllib.parse.unquote(norm))
        if not info:
            continue
        for i in indices:
            works[i].update(info)
            resolved_count += 1
    print(f"Resolved image URLs for {resolved_count} entries")

    # Stamp provenance + harvest method + slug + id
    seen_slugs = {}
    for i, w in enumerate(works):
        w["harvest_method"] = "wikipedia_list"
        # Prefer per-work wikipedia article if present, else the list page
        w["provenance_url"] = w.get("wikipedia_url") or WIKI_LIST_URL
        w.pop("wikipedia_url", None)
        base_slug = slugify(w.get("title", ""))
        w["slug"] = make_unique(base_slug, seen_slugs)
        w["id"] = i + 1

    # Disambiguation for duplicate titles
    title_counter = Counter(w["title"].strip().lower() for w in works if w.get("title"))
    dup_titles = {t for t, c in title_counter.items() if c > 1}
    for w in works:
        if w.get("title", "").strip().lower() in dup_titles:
            parts = []
            if w.get("date"):
                parts.append(str(w["date"]))
            if w.get("fwn_number"):
                parts.append(w["fwn_number"])
            elif w.get("v_number"):
                parts.append(w["v_number"])
            if parts:
                w["title_disambig"] = " · ".join(parts)

    # Order keys nicely for JSON readability (mirror other collections)
    def reorder(w):
        order = [
            "id", "slug", "title", "title_disambig", "date", "year_start",
            "year_end", "circa", "era", "section", "subject", "series",
            "dimensions", "current_location",
            "v_number", "r_number", "fwn_number", "raw_cat_no",
            "commons_filename", "image_url", "thumb_url", "commons_page",
            "image_width", "image_height", "mime",
            "provenance_url", "harvest_method",
        ]
        out = {}
        for k in order:
            if k in w:
                out[k] = w[k]
        for k, v in w.items():
            if k not in out:
                out[k] = v
        return out

    catalog = [reorder(w) for w in works]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    # Stats
    with_url = sum(1 for w in catalog if w.get("image_url"))
    with_thumb = sum(1 for w in catalog if w.get("thumb_url"))
    print(f"\nWritten {len(catalog)} works to {OUTPUT_PATH}")
    print(f"With image_url: {with_url} ({100 * with_url / len(catalog):.1f}%)")
    print(f"With thumb_url: {with_thumb} ({100 * with_thumb / len(catalog):.1f}%)")
    print(f"Era:     {Counter(w.get('era') for w in catalog)}")
    print(f"Subject: {Counter(w.get('subject') for w in catalog)}")
    print(f"Series:  {Counter(w.get('series') for w in catalog if w.get('series'))}")


if __name__ == "__main__":
    main()
