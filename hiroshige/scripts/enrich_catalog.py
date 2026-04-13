#!/usr/bin/env python3
"""
Enrich hiroshige/catalog.json with derived fields:
  era      -> "early" (pre-1830) | "middle" (1830-1845) | "late" (post-1845)
  subject  -> "landscape" | "nature" | "urban" | "portrait" | "other"
  famous   -> bool

Reads/writes hiroshige/catalog.json in place.
Uses title, series, and date to classify each work.
"""

import json
import os
import re

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "catalog.json",
)

# ── Known famous works ────────────────────────────────────────────────
# Curated list of Hiroshige's most renowned individual prints
FAMOUS_TITLES = {
    # Tokaido stations
    "nihonbashi",
    "hara",
    "kanbara",
    "shono",
    "kameyama",
    "mishima",
    "hakone",
    "numazu",
    "okazaki",
    "kyoto",
    "keishi",

    # Edo views
    "suruga-cho",
    "kinryuzan temple",
    "nihonbashi: clearing after snow",
    "nihonbashi clearing after snow",
    "sudden shower over shin-ohashi bridge and atake",
    "sudden shower over shin-ohashi",
    "shin-ohashi bridge",
    "plum park in kameido",
    "plum estate kameido",
    "kameido plum",
    "the city flourishing",
    "tanabata festival",
    "asakusa ricefields and torinomachi festival",
    "asakusa ricefields",
    "maple trees at mama",
    "drum bridge at meguro and sunset hill",
    "drum bridge",
    "inside kameido tenjin shrine",
    "view of a full moon beneath the leaves at takanawa",
    "suijin shrine and massaki on the sumida river",
    "new fuji meguro",
    "open garden at fukagawa hachiman shrine",
    "moon cape",
    "the sea at satta",

    # From Sixty-nine Stations
    "magome",
    "narai",
    "nojiri",

    # Mount Fuji views
    "the sea off satta",
    "lake at hakone",

    # From Sixty-odd Provinces
    "awa province",
    "sado province",
    "shinano province",

    # Other famous prints
    "eagle over 100,000 acre plain at susaki, fukagawa",
    "eagle over the plain",
    "cranes on a snowy pine",
    "swallows and peach blossoms",
    "cat at window",
    "moon over the sumida river",
    "night snow at kambara",
    "evening snow at kanbara",
    "wild geese flying across a full moon",
    "cherry blossoms at arashiyama",
    "fireworks at ryogoku",
    "whirlpools at awa",
    "navaro rapids",
    "rough sea at naruto",
    "naruto whirlpool",
}

# Famous series - all prints from these are notable
FAMOUS_SERIES_PARTIAL = {
    "The Fifty-three Stations of the Tokaido",
    "One Hundred Famous Views of Edo",
}

# ── Subject keywords ──────────────────────────────────────────────────

NATURE_KW = [
    "bird", "crane", "eagle", "geese", "swallow", "sparrow", "heron",
    "fish", "carp", "crab", "lobster", "shrimp",
    "flower", "blossom", "peach", "plum", "iris", "chrysanthemum",
    "wisteria", "morning glory", "camellia", "peony", "hydrangea",
    "maple", "willow", "bamboo", "pine",
    "cat", "deer", "horse", "monkey", "fox",
    "moon", "snow", "rain", "waterfall",
    "insect", "firefly", "dragonfly", "butterfly",
]

URBAN_KW = [
    "bridge", "temple", "shrine", "castle", "gate", "market",
    "festival", "firework", "boat", "ferry", "wharf", "harbor",
    "nihonbashi", "edo", "shop", "theater", "teahouse",
    "town", "city", "street", "quarter", "district",
    "ginza", "asakusa", "yoshiwara", "ryogoku",
]

PORTRAIT_KW = [
    "portrait", "beauty", "beauties", "woman", "courtesan",
    "actor", "kabuki", "geisha", "samurai",
]

# Landscape is the default for Hiroshige — most works are landscapes


def parse_year(date_str: str):
    """Extract the first 4-digit year from a date string."""
    if not date_str:
        return None
    m = re.search(r"\d{4}", date_str)
    return int(m.group()) if m else None


def assign_era(year) -> str:
    if year is None:
        return "unknown"
    if year < 1830:
        return "early"
    if year <= 1845:
        return "middle"
    return "late"


def assign_subject(title: str, series: str) -> str:
    """Classify the work's subject based on title and series."""
    tl = title.lower()
    sl = series.lower() if series else ""
    combined = tl + " " + sl

    # Check for portrait first (least common for Hiroshige)
    for kw in PORTRAIT_KW:
        if kw in combined:
            return "portrait"

    # Check for nature (birds, flowers, animals)
    nature_score = sum(1 for kw in NATURE_KW if kw in combined)
    urban_score = sum(1 for kw in URBAN_KW if kw in combined)

    # If strong nature signal, classify as nature
    if nature_score > 0 and nature_score > urban_score:
        return "nature"

    # If urban signal, classify as urban
    if urban_score > 0:
        return "urban"

    # Default: landscape (Hiroshige's primary genre)
    return "landscape"


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"^(the|a|an)\s+", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def is_famous(title: str, series: str) -> bool:
    """Check if a work is one of Hiroshige's most famous."""
    t = normalize(title)

    # Check against famous titles list
    for f in FAMOUS_TITLES:
        nf = normalize(f)
        if nf == t or nf in t or t in nf:
            return True

    # Special: "Night Snow at Kanbara" / "Kanbara" from Tokaido
    if series == "The Fifty-three Stations of the Tokaido":
        # The most iconic stations
        iconic_stations = {
            "kanbara", "shono", "kameyama", "nihonbashi",
            "hakone", "hara", "mishima", "numazu", "keishi",
            "kyoto", "okazaki",
        }
        for station in iconic_stations:
            if station in t:
                return True

    if series == "One Hundred Famous Views of Edo":
        # All Edo views are notable, but mark the most iconic
        iconic_edo = {
            "ohashi", "shin-ohashi", "kameido", "plum",
            "drum bridge", "suruga", "kinryuzan", "asakusa",
            "tanabata", "eagle", "susaki", "moon cape",
            "suijin", "sumida", "full moon",
        }
        for kw in iconic_edo:
            if kw in t:
                return True

    return False


def main():
    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)

    era_counts = {}
    subject_counts = {}
    famous_count = 0

    for entry in catalog:
        year = parse_year(entry.get("date", ""))
        series = entry.get("series", "")

        era = assign_era(year)
        subject = assign_subject(entry.get("title", ""), series)
        famous = is_famous(entry.get("title", ""), series)

        entry["era"] = era
        entry["subject"] = subject
        entry["famous"] = famous

        era_counts[era] = era_counts.get(era, 0) + 1
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
        if famous:
            famous_count += 1

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"Enriched {len(catalog)} entries -> {CATALOG_PATH}")
    print(f"\nEra distribution:     {era_counts}")
    print(f"Subject distribution: {subject_counts}")
    print(f"Famous works:         {famous_count}")


if __name__ == "__main__":
    main()
