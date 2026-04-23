#!/usr/bin/env python3
"""
Append drawing entries from wiki_drawings_raw.json to catalog.json.

  - assigns unique ids continuing from max(existing id) + 1
  - derives (year_start, year_end, circa) from the `date` string
  - assigns era from created_in / section (same mapping as enrich_catalog.py)
  - assigns subjects from title keywords (same rules)
  - generates a slug; appends "-drawing" if it collides with an existing slug
  - skips entries with no resolved image (image_url empty)
  - leaves tier/famous UNSET (curation is a separate manual step)
  - does NOT modify existing painting entries

Writes van-gogh/catalog.json in place.
"""

import json
import re

CATALOG_PATH = "van-gogh/catalog.json"
DRAWINGS_PATH = "van-gogh/wiki_drawings_raw.json"


# ── Era mapping (mirrors enrich_catalog.py) ──
ERA_MAP = {
    "Etten":              "Etten",
    "The Hague":          "The Hague",
    "Drenthe":            "Drenthe",
    "Nieuw-Amsterdam":    "Drenthe",
    "Scheveningen":       "The Hague",
    "Nuenen":             "Nuenen",
    "Antwerp":            "Antwerp",
    "Amsterdam":          "Amsterdam",
    "Paris":              "Paris",
    "Arles":              "Arles",
    "Saint-Rémy":         "Saint-Rémy",
    "Saint Rémy":         "Saint-Rémy",
    "Auvers-sur-Oise":    "Auvers-sur-Oise",
    "Cuesmes":            "Early",
    "Brussels":           "Early",
    "London":             "Early",
    "Borinage":           "Early",
    "Zundert":            "Early",
    "Tilburg":            "Early",
}

# Section-based fallback (drawings page sections):
#   London-Belgium-Etten, The Hague-Drenthe, Nuenen-Antwerp,
#   Paris, Arles, Saint-Rémy, Auvers-sur-Oise
SECTION_ERA = {
    "London-Belgium-Etten": "Early",
    "The Hague-Drenthe":    "The Hague",
    "Nuenen-Antwerp":       "Nuenen",
    "Paris":                "Paris",
    "Arles":                "Arles",
    "Saint-Rémy":           "Saint-Rémy",
    "Auvers-sur-Oise":      "Auvers-sur-Oise",
}

# ── Subject detection (mirrors enrich_catalog.py) ──
SUBJECT_RULES = [
    ("self_portrait",  r"\bself[- ]portrait\b"),
    ("portrait",       r"\bportrait\b|\bhead of\b|\bface of\b|\bwoman\b|\bman\b|\bgirl\b|\bboy\b|\bpeasant\b|\bfigure\b|\bzouave\b|\bpostman\b|\bmadame\b|\barlésienne\b|\barlesian\b|\bwoman reading\b|\bwoman sitting\b|\bwoman sewing\b|\bmother\b|\bbaby\b|\bchild\b"),
    ("landscape",      r"\blandscape\b|\bfield\b|\bwheat\b|\bmeadow\b|\bgarden\b|\bpark\b|\borchard\b|\bplain\b|\bhill\b|\bmountain\b|\bvalley\b|\broad\b|\bpath\b|\blane\b|\bview of\b|\bview from\b|\bsunset\b|\bsunrise\b|\bsky\b|\bstarry\b|\bnight\b|\bcypres\b|\bolive\b|\btree\b|\bwood\b|\bforest\b|\bblossom\b|\bflowering\b|\bharvest\b|\bploughed\b|\bsower\b|\bwheatfield\b|\bvinyard\b|\bvineyard\b|\bprovence\b|\bmontmartre\b|\bravine\b|\briver\b|\bcanal\b|\bsea\b|\bbeach\b|\bshore\b|\bdune\b|\bcoast\b"),
    ("cityscape",      r"\bcity\b|\bstreet\b|\btown\b|\bbridge\b|\bbuilding\b|\bhouse\b|\bcottage\b|\bchurch\b|\bcafé\b|\bcafe\b|\brestaurant\b|\bterrace\b|\bfactory\b|\bmill\b|\bwindmill\b|\bstation\b|\brailway\b|\btower\b|\bvillage\b"),
    ("still_life",     r"\bstill life\b|\bvase\b|\bflower\b|\bsunflower\b|\biris\b|\broses\b|\bfruit\b|\bapple\b|\bpear\b|\blemon\b|\borange\b|\bonion\b|\bpotato\b|\bbook\b|\bbottle\b|\bshoe\b|\bboot\b|\bhat\b|\bchair\b|\bcandle\b|\bpipe\b|\bplate\b|\bbowl\b|\bbasket\b|\bcabbage\b|\bherring\b"),
    ("interior",       r"\binterior\b|\bbedroom\b|\broom\b|\bstudio\b|\bhospital\b|\bcorridor\b|\bhall\b"),
    ("animal",         r"\bdog\b|\bcat\b|\bhorse\b|\bbox\b|\bsheep\b|\bcow\b|\bbird\b|\bbull\b|\bcrab\b|\bbeetle\b|\bbutterfl\b|\bmoth\b|\bskull\b|\bhen\b|\bcock\b|\brooster\b"),
]


def assign_era(work: dict) -> str:
    loc = (work.get("created_in") or "").strip()
    if loc in ERA_MAP:
        return ERA_MAP[loc]
    section = work.get("section", "")
    if section in SECTION_ERA:
        return SECTION_ERA[section]
    # Best-effort substring match on section
    for key, era in SECTION_ERA.items():
        if key in section:
            return era
    return "Unknown"


def assign_subjects(title: str) -> list:
    t = (title or "").lower()
    tags = []
    for tag, pattern in SUBJECT_RULES:
        if re.search(pattern, t):
            tags.append(tag)
    if not tags:
        tags.append("other")
    return tags


# ── Date parsing ──
# Covers:
#   "1888"
#   "1884–85" / "1884-85" / "1884–1885"
#   "c. 1882" / "circa 1882"
#   "1873 or 74" / "1873 or 1874"
#   "August 1882"
#   "November–December 1881"
#   "May, 1889"
#   "June–July 1890"
YEAR_RE = re.compile(r"(\d{4})")
TWO_DIGIT_TAIL_RE = re.compile(r"(\d{4})\s*[–\-]\s*(\d{2,4})")
CIRCA_RE = re.compile(r"(?:\bc\.|\bca\.|\bcirca\b|\baround\b|\bprobably\b)", re.IGNORECASE)
OR_RE = re.compile(r"(\d{4})\s+or\s+(\d{2,4})", re.IGNORECASE)


def parse_date(date_str: str):
    """Return (year_start, year_end, circa_bool) or (None, None, False)."""
    if not date_str:
        return (None, None, False)
    s = date_str.strip()
    circa = bool(CIRCA_RE.search(s))

    # "1873 or 74" / "1873 or 1874"
    m = OR_RE.search(s)
    if m:
        y1 = int(m.group(1))
        tail = m.group(2)
        y2 = int(tail) if len(tail) == 4 else (y1 // 100) * 100 + int(tail)
        return (min(y1, y2), max(y1, y2), circa)

    # "1884–85" / "1884-85" / "1884–1885"
    m = TWO_DIGIT_TAIL_RE.search(s)
    if m:
        y1 = int(m.group(1))
        tail = m.group(2)
        y2 = int(tail) if len(tail) == 4 else (y1 // 100) * 100 + int(tail)
        return (min(y1, y2), max(y1, y2), circa)

    # One or more bare 4-digit years. Use first as start, last as end.
    years = [int(y) for y in YEAR_RE.findall(s)]
    if years:
        return (min(years), max(years), circa)

    return (None, None, circa)


# ── Slug generation ──
def make_slug(title: str) -> str:
    t = (title or "").lower()
    # Keep only alnum + spaces + hyphens
    t = re.sub(r"[^a-z0-9\s\-]", "", t)
    t = re.sub(r"\s+", "-", t.strip())
    t = re.sub(r"-+", "-", t)
    return t or "untitled"


def main():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    with open(DRAWINGS_PATH, "r", encoding="utf-8") as f:
        drawings = json.load(f)

    print(f"Existing catalog entries: {len(catalog)}")
    print(f"Drawings to merge:        {len(drawings)}")

    existing_slugs = {w.get("slug") for w in catalog if w.get("slug")}
    max_id = max((w.get("id", 0) for w in catalog), default=0)
    next_id = max_id + 1
    print(f"Max existing id: {max_id}; new ids start at {next_id}")

    added = 0
    skipped_no_image = 0
    slug_collisions = 0

    for d in drawings:
        # Skip if no resolvable image
        if not d.get("image_url"):
            skipped_no_image += 1
            continue

        w = dict(d)
        w["type"] = "drawing"
        w["id"] = next_id
        next_id += 1

        # Year triplet
        y_start, y_end, circa = parse_date(w.get("date", ""))
        w["year_start"] = y_start
        w["year_end"] = y_end
        w["circa"] = circa

        # Era + subjects
        w["era"] = assign_era(w)
        w["subjects"] = assign_subjects(w.get("title", ""))

        # Slug (append -drawing if it collides)
        base_slug = make_slug(w.get("title", ""))
        slug = base_slug
        if slug in existing_slugs:
            slug = f"{base_slug}-drawing"
            slug_collisions += 1
            # Very rare second-level collision (two drawings with same title):
            # suffix with id so it's stable.
            if slug in existing_slugs:
                slug = f"{base_slug}-drawing-{w['id']}"
        existing_slugs.add(slug)
        w["slug"] = slug

        # tier/famous intentionally left UNSET — curation is manual

        catalog.append(w)
        added += 1

    print(f"\nAdded:              {added}")
    print(f"Skipped (no image): {skipped_no_image}")
    print(f"Slug collisions:    {slug_collisions} (suffix '-drawing' applied)")
    print(f"New catalog total:  {len(catalog)}")

    # Era + subject counts for drawings only
    new_drawings = [w for w in catalog if w.get("type") == "drawing"]
    era_counts = {}
    subj_counts = {}
    for w in new_drawings:
        era_counts[w["era"]] = era_counts.get(w["era"], 0) + 1
        for s in w["subjects"]:
            subj_counts[s] = subj_counts.get(s, 0) + 1

    print("\nDrawings by era:")
    for era, c in sorted(era_counts.items(), key=lambda x: -x[1]):
        print(f"  {era}: {c}")
    print("\nDrawings by subject:")
    for s, c in sorted(subj_counts.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}")

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"\nWritten {len(catalog)} entries to {CATALOG_PATH}")


if __name__ == "__main__":
    main()
