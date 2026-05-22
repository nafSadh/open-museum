#!/usr/bin/env python3
"""
Resolve Wikimedia Commons image URLs for every entry in
goya/wiki_works_raw.json. Populates image_url / thumb_url (960 px wide) /
commons_page / image_width / image_height / mime on each entry, then emits a
catalog.json enriched with era, subject, series, date triplet, slug, id, and famous tags.

Usage:  python3 goya/scripts/resolve_commons_urls.py
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
USER_AGENT = "open-museum/1.0 goya-build (https://github.com/nafSadh/open-museum)"
WIKI_LIST_URL = "https://en.wikipedia.org/wiki/List_of_works_by_Francisco_Goya"

# Sleep 1s between API requests
SLEEP_SECONDS = 1.0


def fetch_image_info(filenames: list) -> dict:
    if not filenames:
        return {}
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
            data = json.loads(resp.read().decode("utf-8"))
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


def slugify(text: str) -> str:
    s = text.lower()
    s = s.replace("'", "").replace("'", "").replace("'", "")
    s = s.replace("ç", "c").replace("é", "e").replace("è", "e").replace("ê", "e").replace("ë", "e")
    s = s.replace("à", "a").replace("â", "a").replace("á", "a").replace("ã", "a")
    s = s.replace("î", "i").replace("í", "i").replace("ï", "i")
    s = s.replace("ô", "o").replace("ó", "o").replace("ö", "o")
    s = s.replace("ù", "u").replace("û", "u").replace("ú", "u").replace("ü", "u")
    s = s.replace("ñ", "n")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "untitled"


def make_unique(slug: str, seen: dict) -> str:
    if slug not in seen:
        seen[slug] = 1
        return slug
    seen[slug] += 1
    return f"{slug}-{seen[slug]}"


def parse_date_triplet(raw: str):
    """
    Parse Goya date format, supporting 'to', 'and', '–', '-'
    """
    if not raw:
        return None, None, False
    s = raw.strip()
    circa = bool(re.search(r"\bc\.|\bcirca\b|\bca\.", s, re.I))
    s_clean = re.sub(r"\bc\.\s*|\bcirca\s*|\bca\.\s*", "", s, flags=re.I)

    # Range like "1786 to 1787", "1786-87", "1786–1787"
    m = re.search(r"(1[789]\d\d)\s*(?:to|and|[–\-])\s*(\d{2,4})(?!\d)", s_clean, re.I)
    if m:
        start = int(m.group(1))
        end_raw = m.group(2)
        if len(end_raw) == 2:
            end_full = (start // 100) * 100 + int(end_raw)
            if end_full < start:
                end_full += 100
        else:
            end_full = int(end_raw)
        return start, end_full, circa

    # Single year
    m = re.search(r"(1[789]\d\d)", s_clean)
    if m:
        y = int(m.group(1))
        return y, y, circa

    return None, None, circa


def classify_subject(work: dict) -> str:
    title = work.get("title", "").lower()
    sec = work.get("section", "").lower()
    
    # Quinta del Sordo check for black paintings
    if "1819" in sec and any(k in title for k in ("saturn", "dog", "witches sabbath", "great he-goat", "judith", "asmodea", "men reading", "two old", "destinies", "pilgrimage", "holy office")):
        return "dark_painting"
    
    # Other subjects
    if any(k in title for k in ("portrait", "self-portrait", "self portrait", "carlos iv", "charles iv", "duchess", "condesa", "marquesa", "family of", "maja", "majas", "majo", "majos", "godoy", "señora", "senora")):
        return "portrait"
    
    if any(k in title for k in ("saint", "christ", "virgin", "annunciation", "san ", "santa ", "consecration", "crucifixion", "adoration", "nativity", "church", "patron", "pope", "cardinal", "bishop", "altarpiece")):
        return "religious"
        
    if any(k in title for k in ("saturn", "colossus", "venus", "jupiter", "minerva", "hercules", "mythological")):
        return "mythological"
        
    if any(k in title for k in ("second of may", "third of may", "war", "disasters of", "execution", "defense", "charge of", "battle", "assault", "famine", "plague", "murder", "arrest", "torture")):
        return "history"
        
    if any(k in title for k in ("parasol", "quitasol", "kite", "cometa", "swing", "stroll", "walk", "picnic", "dance", "game", "play", "cartoon", "tapestry", "festival", "bullfight", "bullfighter", "matador", "corrida", "carnival", "mask", "lunatics", "asylum", "prison", "madhouse", "inn", "forge", "water-carrier", "milkmaid")):
        return "genre"
        
    if any(k in title for k in ("allegory", "truth", "time", "liberty", "poetry")):
        return "allegory"
        
    if any(k in title for k in ("landscape", "view of", "road", "river", "bridge", "ruins")):
        return "landscape"
        
    return "other"


def is_famous(work: dict) -> bool:
    t = work.get("title", "").lower()
    if "third of may 1808" in t:
        return True
    if "second of may 1808" in t and "sketch" not in t:
        return True
    if "saturn devouring" in t:
        return True
    if "nude maja" in t:
        return True
    if "clothed maja" in t:
        return True
    if "the parasol" in t:
        return True
    if "sleep of reason" in t:
        return True
    if "charles iv of spain and his family" in t:
        return True
    if "witches sabbath" in t or "great he-goat" in t or "aquelarre" in t:
        # Quinta del Sordo or the 1797-1798 one
        return True
    if "the dog" in t and "dogs" not in t:
        return True
    if "the colossus" in t:
        return True
    if "yard with lunatics" in t:
        return True
    if "witches' flight" in t or "witches flight" in t or "vuelo de brujas" in t:
        return True
    if "milkmaid of bordeaux" in t:
        return True
    if "manuel osorio manrique" in t:
        return True
    return False


def main():
    print(f"Loading {INPUT_PATH}")
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        works = json.load(f)
    print(f"Loaded {len(works)} works")

    # Deduplicate filenames for resolution
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

    # Merge resolved info
    resolved_count = 0
    for norm, indices in fname_to_indices.items():
        info = resolved.get(norm) or resolved.get(urllib.parse.unquote(norm))
        if not info:
            continue
        for i in indices:
            works[i].update(info)
            resolved_count += 1
    print(f"Resolved image URLs for {resolved_count} entries")

    # Enrich metadata
    seen_slugs = {}
    for i, w in enumerate(works):
        w["harvest_method"] = "wikipedia_list"
        w["provenance_url"] = w.get("wikipedia_url") or WIKI_LIST_URL
        w.pop("wikipedia_url", None)
        
        base_slug = slugify(w.get("title", ""))
        w["slug"] = make_unique(base_slug, seen_slugs)
        w["id"] = i + 1

        # Date triplet
        y_start, y_end, circa = parse_date_triplet(w.get("date", ""))
        if y_start:
            w["year_start"] = y_start
            w["year_end"] = y_end
            w["circa"] = circa
        else:
            # Fallback if already set by prints series
            pass

        # Subjects
        w["subject"] = classify_subject(w)

        # Famous and tier
        if is_famous(w):
            w["tier"] = "famous"
            w["famous"] = True
        elif w.get("provenance_url") and w["provenance_url"] != WIKI_LIST_URL:
            w["tier"] = "well_known"
            w["famous"] = False
        else:
            w["famous"] = False

    # Disambiguation for duplicate titles
    title_counter = Counter(w["title"].strip().lower() for w in works if w.get("title"))
    dup_titles = {t for t, c in title_counter.items() if c > 1}
    for w in works:
        if w.get("title", "").strip().lower() in dup_titles:
            parts = []
            if w.get("date"):
                parts.append(str(w["date"]))
            if w.get("current_location"):
                loc = w["current_location"]
                if len(loc) > 20:
                    loc = loc.split(",")[0]  # Take first part to keep it short
                parts.append(loc)
            elif w.get("series"):
                parts.append(w["series"].replace("_", " ").title())
            if parts:
                w["title_disambig"] = " · ".join(parts)

    # Order keys nicely
    def reorder(w):
        order = [
            "id", "slug", "type", "title", "title_disambig", "date", "year_start",
            "year_end", "circa", "era", "series", "section", "subject",
            "medium", "dimensions", "current_location",
            "commons_filename", "image_url", "thumb_url", "commons_page",
            "image_width", "image_height", "mime",
            "tier", "famous", "provenance_url", "harvest_method",
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
    famous_count = sum(1 for w in catalog if w.get("famous"))
    print(f"\nWritten {len(catalog)} works to {OUTPUT_PATH}")
    print(f"With image_url: {with_url} ({100 * with_url / len(catalog):.1f}%)")
    print(f"With thumb_url: {with_thumb} ({100 * with_thumb / len(catalog):.1f}%)")
    print(f"Famous works: {famous_count}")
    print(f"Eras:     {Counter(w.get('era') for w in catalog if w.get('era'))}")
    print(f"Series:   {Counter(w.get('series') for w in catalog if w.get('series'))}")
    print(f"Subject:  {Counter(w.get('subject') for w in catalog)}")


if __name__ == "__main__":
    main()
