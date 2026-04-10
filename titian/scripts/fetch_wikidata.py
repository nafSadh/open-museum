#!/usr/bin/env python3
"""
Fetch Wikidata genre and depicts metadata for Titian paintings,
then merge into catalog.json by fuzzy title match.

Reads:  titian/catalog.json
Writes: titian/catalog.json (in-place, adds wikidata_genres / wikidata_depicts)
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
SELECT ?item ?itemLabel ?genreLabel ?depictsLabel WHERE {
  ?item wdt:P170 wd:Q47551 .
  ?item wdt:P31 wd:Q3305213 .
  OPTIONAL { ?item wdt:P136 ?genre . }
  OPTIONAL { ?item wdt:P180 ?depicts . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
"""

USER_AGENT = "open-museum/1.0 (contact: nafsadh@gmail.com)"
TIMEOUT = 60  # seconds


# ── Helpers ──────────────────────────────────────────────────────────

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

    Returns: { qid: { "label": str, "genres": set, "depicts": set } }
    """
    items: dict[str, dict] = {}

    for row in bindings:
        qid = row["item"]["value"].rsplit("/", 1)[-1]

        if qid not in items:
            items[qid] = {
                "label": row.get("itemLabel", {}).get("value", ""),
                "genres": set(),
                "depicts": set(),
            }

        item = items[qid]

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
    # Build lookup by normalized title
    title_lookup: dict[str, dict] = {}
    for qid, info in wd_items.items():
        if info["label"]:
            nt = normalize_title(info["label"])
            if nt:
                title_lookup[nt] = info

    matched_title = 0
    unmatched = 0

    for entry in catalog:
        wd_info = None

        cat_title_norm = normalize_title(entry.get("title", ""))
        
        # Exact fuzzy match
        if cat_title_norm in title_lookup:
            wd_info = title_lookup[cat_title_norm]
        else:
            # Fallback: substring match if the catalog title is very descriptive
            # e.g. "Sacred and Profane Love" contains "Sacred and Profane Love"
            for t_norm, info in title_lookup.items():
                if len(t_norm) > 5 and t_norm in cat_title_norm:
                    wd_info = info
                    break
                # Or the reverse: "Portrait of a Man" in "Portrait of a Man with a Red Cap"
                if len(cat_title_norm) > 5 and cat_title_norm in t_norm:
                    wd_info = info
                    break

        if wd_info is None:
            unmatched += 1
            continue

        matched_title += 1

        # Merge data
        genres = sorted(wd_info["genres"])
        depicts = sorted(wd_info["depicts"])

        if genres:
            entry["wikidata_genres"] = genres
        if depicts:
            entry["wikidata_depicts"] = depicts

    return {
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
    with_genres = sum(1 for v in wd_items.values() if v["genres"])
    with_depicts = sum(1 for v in wd_items.values() if v["depicts"])

    print(f"\\nWikidata items (unique paintings): {wd_total}")
    print(f"  with genres:    {with_genres}")
    print(f"  with depicts:   {with_depicts}")

    # 3. Read catalog
    print(f"\\nReading catalog from {CATALOG_PATH}")
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    cat_total = len(catalog)
    print(f"Catalog entries: {cat_total}")

    # 4. Match and enrich
    stats = match_catalog(catalog, wd_items)

    # 5. Write back
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"\\nWrote updated catalog to {CATALOG_PATH}")

    # 6. Stats
    print(f"\\n{'-' * 50}")
    print(f"Matching stats:")
    print(f"  Matched by title:     {stats['matched_title']} / {cat_total} ({100*stats['matched_title']/cat_total:.1f}%)")
    print(f"  Unmatched:            {stats['unmatched']} / {cat_total} ({100*stats['unmatched']/cat_total:.1f}%)")

    enriched_genres = sum(1 for e in catalog if "wikidata_genres" in e)
    enriched_depicts = sum(1 for e in catalog if "wikidata_depicts" in e)
    print(f"\\nEnrichment:")
    print(f"  Entries with wikidata_genres:  {enriched_genres} ({100*enriched_genres/cat_total:.1f}%)")
    print(f"  Entries with wikidata_depicts: {enriched_depicts} ({100*enriched_depicts/cat_total:.1f}%)")
    print(f"{'-' * 50}")


if __name__ == "__main__":
    main()
