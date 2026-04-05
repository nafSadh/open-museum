#!/usr/bin/env python3
"""
Fetch Wikidata genre and depicts metadata for Van Gogh paintings,
then merge into catalog.json by matching F-numbers (primary) or
fuzzy title match (fallback).

Reads:  van-gogh/catalog.json
Writes: van-gogh/catalog.json (in-place, adds wikidata_genres / wikidata_depicts)
"""

import json
import re
import urllib.request
import urllib.parse
import urllib.error
import os
import sys

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "catalog.json",
)

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

SPARQL_QUERY = """\
SELECT ?item ?itemLabel ?fNumber ?genreLabel ?depictsLabel WHERE {
  ?item wdt:P170 wd:Q5582 .
  ?item wdt:P31 wd:Q3305213 .
  OPTIONAL { ?item wdt:P136 ?genre . }
  OPTIONAL { ?item wdt:P180 ?depicts . }
  OPTIONAL { ?item p:P528 ?catalogStatement . ?catalogStatement ps:P528 ?fNumber . ?catalogStatement pq:P972 wd:Q17280421 . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
"""

USER_AGENT = "open-museum/1.0 (contact: nafsadh@gmail.com)"
TIMEOUT = 60  # seconds


# ── Helpers ──────────────────────────────────────────────────────────

def normalize_f_number(raw: str) -> str:
    """Normalize an F-number to a canonical form like 'F1', 'F2a'.

    Handles inputs like 'F 1', 'F1', 'F 123a', 'F123a'.
    """
    raw = raw.strip()
    m = re.match(r"[Ff]\s*(\d+[a-zA-Z]?)", raw)
    if m:
        return "F" + m.group(1)
    return raw


def normalize_title(title: str) -> str:
    """Lowercase, strip articles and punctuation for fuzzy matching."""
    t = title.lower().strip()
    # Remove leading articles
    t = re.sub(r"^(the|a|an|le|la|les|de|het|een)\s+", "", t)
    # Remove punctuation except spaces
    t = re.sub(r"[^a-z0-9\s]", "", t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


# ── SPARQL fetch ─────────────────────────────────────────────────────

def fetch_wikidata() -> list[dict]:
    """Query Wikidata SPARQL endpoint, return list of result bindings."""
    params = urllib.parse.urlencode({"query": SPARQL_QUERY})
    url = f"{SPARQL_ENDPOINT}?{params}"

    req = urllib.request.Request(url)
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/sparql-results+json")

    print(f"Querying Wikidata SPARQL endpoint (timeout={TIMEOUT}s)...")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"ERROR: Network request failed: {e}", file=sys.stderr)
        sys.exit(1)
    except TimeoutError:
        print("ERROR: SPARQL query timed out.", file=sys.stderr)
        sys.exit(1)

    bindings = data.get("results", {}).get("bindings", [])
    print(f"Received {len(bindings)} raw result rows from Wikidata.")
    return bindings


# ── Group results by Wikidata item ───────────────────────────────────

def group_by_item(bindings: list[dict]) -> dict:
    """Group SPARQL rows into per-item dicts.

    Returns: { qid: { "label": str, "f_number": str|None,
                       "genres": set, "depicts": set } }
    """
    items: dict[str, dict] = {}

    for row in bindings:
        qid = row["item"]["value"].rsplit("/", 1)[-1]

        if qid not in items:
            items[qid] = {
                "label": row.get("itemLabel", {}).get("value", ""),
                "f_number": None,
                "genres": set(),
                "depicts": set(),
            }

        item = items[qid]

        # F-number
        if "fNumber" in row and row["fNumber"]["value"]:
            item["f_number"] = normalize_f_number(row["fNumber"]["value"])

        # Genre
        genre_val = row.get("genreLabel", {}).get("value", "")
        if genre_val and not genre_val.startswith("http"):
            item["genres"].add(genre_val)

        # Depicts
        depicts_val = row.get("depictsLabel", {}).get("value", "")
        if depicts_val and not depicts_val.startswith("http"):
            item["depicts"].add(depicts_val)

    return items


# ── Matching ─────────────────────────────────────────────────────────

def match_catalog(catalog: list[dict], wd_items: dict) -> dict:
    """Match Wikidata items to catalog entries.

    Returns stats dict.
    """
    # Build lookup by F-number
    f_lookup: dict[str, dict] = {}
    for qid, info in wd_items.items():
        if info["f_number"]:
            f_lookup[info["f_number"]] = info

    # Build lookup by normalized title
    title_lookup: dict[str, dict] = {}
    for qid, info in wd_items.items():
        if info["label"]:
            nt = normalize_title(info["label"])
            if nt:
                title_lookup[nt] = info

    matched_f = 0
    matched_title = 0
    unmatched = 0

    for entry in catalog:
        wd_info = None

        # Primary: F-number
        f_num = entry.get("f_number", "")
        if f_num:
            norm_f = normalize_f_number(f_num)
            if norm_f in f_lookup:
                wd_info = f_lookup[norm_f]
                matched_f += 1

        # Fallback: fuzzy title match
        if wd_info is None:
            cat_title = normalize_title(entry.get("title", ""))
            if cat_title and cat_title in title_lookup:
                wd_info = title_lookup[cat_title]
                matched_title += 1

        if wd_info is None:
            unmatched += 1
            continue

        # Merge data
        genres = sorted(wd_info["genres"])
        depicts = sorted(wd_info["depicts"])

        if genres:
            entry["wikidata_genres"] = genres
        if depicts:
            entry["wikidata_depicts"] = depicts

    return {
        "matched_f": matched_f,
        "matched_title": matched_title,
        "unmatched": unmatched,
    }


# ── Main ─────────────────────────────────────────────────────────────

def main():
    # 1. Fetch from Wikidata
    bindings = fetch_wikidata()

    # 2. Group by item
    wd_items = group_by_item(bindings)
    wd_total = len(wd_items)
    with_f = sum(1 for v in wd_items.values() if v["f_number"])
    with_genres = sum(1 for v in wd_items.values() if v["genres"])
    with_depicts = sum(1 for v in wd_items.values() if v["depicts"])

    print(f"\nWikidata items (unique paintings): {wd_total}")
    print(f"  with F-number:  {with_f}")
    print(f"  with genres:    {with_genres}")
    print(f"  with depicts:   {with_depicts}")

    # 3. Read catalog
    print(f"\nReading catalog from {CATALOG_PATH}")
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    cat_total = len(catalog)
    print(f"Catalog entries: {cat_total}")

    # 4. Match and enrich
    stats = match_catalog(catalog, wd_items)

    # 5. Write back
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"\nWrote updated catalog to {CATALOG_PATH}")

    # 6. Stats
    total_matched = stats["matched_f"] + stats["matched_title"]
    print(f"\n{'─' * 50}")
    print(f"Matching stats:")
    print(f"  Matched by F-number:  {stats['matched_f']}")
    print(f"  Matched by title:     {stats['matched_title']}")
    print(f"  Total matched:        {total_matched} / {cat_total} catalog entries ({100*total_matched/cat_total:.1f}%)")
    print(f"  Unmatched:            {stats['unmatched']} / {cat_total} ({100*stats['unmatched']/cat_total:.1f}%)")

    enriched_genres = sum(1 for e in catalog if "wikidata_genres" in e)
    enriched_depicts = sum(1 for e in catalog if "wikidata_depicts" in e)
    print(f"\nEnrichment:")
    print(f"  Entries with wikidata_genres:  {enriched_genres} ({100*enriched_genres/cat_total:.1f}%)")
    print(f"  Entries with wikidata_depicts: {enriched_depicts} ({100*enriched_depicts/cat_total:.1f}%)")
    print(f"{'─' * 50}")


if __name__ == "__main__":
    main()
