#!/usr/bin/env python3
"""
Enrich catalog.json with:
  - era (period/location)
  - subject tags (landscape, portrait, still_life, etc.)
  - famous flag for well-known works

Reads:  van-gogh/catalog.json
Writes: van-gogh/catalog.json (in-place)
"""

import json
import re

INPUT = "van-gogh/catalog.json"

# ── Era mapping ──
# Normalize created_in to canonical eras with date ranges
ERA_MAP = {
    "Etten":              ("Etten",           "1881"),
    "The Hague":          ("The Hague",       "1881–83"),
    "Drenthe":            ("Drenthe",         "1883"),
    "Nieuw-Amsterdam":    ("Drenthe",         "1883"),
    "Scheveningen":       ("The Hague",       "1881–83"),
    "Nuenen":             ("Nuenen",          "1883–85"),
    "Antwerp":            ("Antwerp",         "1885–86"),
    "Amsterdam":          ("Amsterdam",       "1886"),
    "Paris":              ("Paris",           "1886–88"),
    "Arles":              ("Arles",           "1888–89"),
    "Saint-Rémy":         ("Saint-Rémy",      "1889–90"),
    "Saint Rémy":         ("Saint-Rémy",      "1889–90"),
    "Auvers-sur-Oise":   ("Auvers-sur-Oise", "1890"),
    "Cuesmes":            ("Early",           "1879–80"),
}

# Also infer era from section name if created_in is missing
SECTION_ERA = {
    "The Hague-Drenthe":  "The Hague",
    "Nuenen-Antwerp":     "Nuenen",
    "Paris":              "Paris",
    "Arles":              "Arles",
    "Saint-Rémy":         "Saint-Rémy",
    "Auvers-sur-Oise":   "Auvers-sur-Oise",
}

# ── Subject detection via title keywords ──
SUBJECT_RULES = [
    # Order matters: first match wins for primary, but we collect all
    ("self_portrait",  r"\bself[- ]portrait\b"),
    ("portrait",       r"\bportrait\b|\bhead of\b|\bface of\b|\bwoman\b|\bman\b|\bgirl\b|\bboy\b|\bpeasant\b|\bfigure\b|\bzouave\b|\bpostman\b|\bmadame\b|\barlésienne\b|\barlesian\b|\bwoman reading\b|\bwoman sitting\b|\bwoman sewing\b|\bmother\b|\bbaby\b|\bchild\b"),
    ("landscape",      r"\blandscape\b|\bfield\b|\bwheat\b|\bmeadow\b|\bgarden\b|\bpark\b|\borchard\b|\bplain\b|\bhill\b|\bmountain\b|\bvalley\b|\broad\b|\bpath\b|\blane\b|\bview of\b|\bview from\b|\bsunset\b|\bsunrise\b|\bsky\b|\bstarry\b|\bnight\b|\bcypres\b|\bolive\b|\btree\b|\bwood\b|\bforest\b|\bblossom\b|\bflowering\b|\bharvest\b|\bploughed\b|\bsower\b|\bwheatfield\b|\bvinyard\b|\bvineyard\b|\bprovence\b|\bmontmartre\b|\bravine\b|\briver\b|\bcanal\b|\bsea\b|\bbeach\b|\bshore\b|\bdune\b|\bcoast\b"),
    ("cityscape",      r"\bcity\b|\bstreet\b|\btown\b|\bbridge\b|\bbuilding\b|\bhouse\b|\bcottage\b|\bchurch\b|\bcafé\b|\bcafe\b|\brestaurant\b|\bterrace\b|\bfactory\b|\bmill\b|\bwindmill\b|\bstation\b|\brailway\b|\btower\b|\bvillage\b"),
    ("still_life",     r"\bstill life\b|\bvase\b|\bflower\b|\bsunflower\b|\biris\b|\broses\b|\bfruit\b|\bapple\b|\bpear\b|\blemon\b|\borange\b|\bonion\b|\bpotato\b|\bbook\b|\bbottle\b|\bshoe\b|\bboot\b|\bhat\b|\bchair\b|\bcandle\b|\bpipe\b|\bplate\b|\bbowl\b|\bbasket\b|\bcabbage\b|\bherring\b"),
    ("interior",       r"\binterior\b|\bbedroom\b|\broom\b|\bstudio\b|\bhospital\b|\bcorridor\b|\bhall\b"),
    ("animal",         r"\bdog\b|\bcat\b|\bhorse\b|\bbox\b|\bsheep\b|\bcow\b|\bbird\b|\bbull\b|\bcrab\b|\bbeetle\b|\bbutterfl\b|\bmoth\b|\bskull\b"),
]

# ── Famous works ──
# Titles (case-insensitive partial match) of the ~50 most iconic works
FAMOUS_TITLES = [
    "the starry night",
    "starry night over the rhone",  # different painting
    "irises",
    "sunflowers",
    "the potato eaters",
    "bedroom in arles",
    "the bedroom",
    "café terrace at night",
    "cafe terrace at night",
    "the night café",
    "the night cafe",
    "wheatfield with crows",
    "wheat field with crows",
    "almond blossom",
    "self-portrait with bandaged ear",
    "self-portrait with grey felt hat",
    "self-portrait dedicated to paul gauguin",
    "the yellow house",
    "the church at auvers",
    "the red vineyard",
    "portrait of dr. gachet",
    "portrait of doctor gachet",
    "the sower",
    "the mulberry tree",
    "olive trees",
    "cypresses",
    "the bridge at langlois",
    "pont de langlois",
    "shoes",
    "a pair of shoes",
    "the harvest",
    "siesta",
    "noon rest from work",
    "the prison courtyard",
    "prisoners exercising",
    "skull of a skeleton with burning cigarette",
    "fishing boats on the beach",
    "la mousmé",
    "the postman joseph roulin",
    "joseph roulin",
    "l'arlésienne",
    "branches of an almond tree in blossom",
    "road with cypress and star",
    "green wheat field",
    "blossoming almond tree",
    "the old mill",
    "garden at arles",
    "memory of the garden at etten",
    "the pink peach tree",
    "peach tree in blossom",
    "landscape at saint-rémy",
    "sorrowing old man",
    "at eternity's gate",
    "the raising of lazarus",
    "peasant character studies",
    "head of a woman",
]


def assign_era(work: dict) -> str:
    """Assign a canonical era to a work."""
    loc = work.get("created_in", "")
    if loc in ERA_MAP:
        return ERA_MAP[loc][0]
    # Try section name
    section = work.get("section", "")
    for key, era in SECTION_ERA.items():
        if key in section:
            return era
    return "Unknown"


def assign_subjects(title: str) -> list[str]:
    """Detect subject tags from title."""
    t = title.lower()
    tags = []
    for tag, pattern in SUBJECT_RULES:
        if re.search(pattern, t):
            tags.append(tag)
    if not tags:
        tags.append("other")
    return tags


def fame_rank(title: str):
    """Return fame rank (0 = most famous) or None if not famous."""
    t = title.lower().strip()
    for i, famous in enumerate(FAMOUS_TITLES):
        if famous in t or t in famous:
            return i
    return None


def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        works = json.load(f)

    print(f"Enriching {len(works)} works...")

    era_counts = {}
    subject_counts = {}
    famous_count = 0

    for w in works:
        # Era
        era = assign_era(w)
        w["era"] = era
        era_counts[era] = era_counts.get(era, 0) + 1

        # Subjects
        subjects = assign_subjects(w.get("title", ""))
        w["subjects"] = subjects
        for s in subjects:
            subject_counts[s] = subject_counts.get(s, 0) + 1

        # Famous
        rank = fame_rank(w.get("title", ""))
        if rank is not None:
            w["famous"] = True
            w["fame_rank"] = rank
            famous_count += 1
        else:
            w.pop("famous", None)
            w.pop("fame_rank", None)

    print(f"\nEras:")
    for era, c in sorted(era_counts.items(), key=lambda x: -x[1]):
        print(f"  {era}: {c}")

    print(f"\nSubjects:")
    for s, c in sorted(subject_counts.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}")

    print(f"\nFamous: {famous_count}")

    with open(INPUT, "w", encoding="utf-8") as f:
        json.dump(works, f, ensure_ascii=False, indent=2)

    print(f"\nWritten enriched catalog to {INPUT}")


if __name__ == "__main__":
    main()
