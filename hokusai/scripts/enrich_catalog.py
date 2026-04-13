#!/usr/bin/env python3
"""
Enrich hokusai/catalog.json with derived fields:
  era      -> "early" (pre-1800) | "middle" (1800-1830) | "late" (post-1830)
  subject  -> "landscape" | "nature" | "portrait" | "mythology" | "erotica" | "other"
  famous   -> bool

Reads/writes hokusai/catalog.json in place.
Uses title keywords and series information for classification.
"""

import json
import os
import re

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "catalog.json",
)

# ── Known famous works ────────────────────────────────────────────────
FAMOUS_TITLES = {
    "the great wave off kanagawa",
    "the great wave",
    "great wave",
    "fine wind clear morning",
    "south wind clear sky",
    "red fuji",
    "thunderstorm beneath the summit",
    "rainstorm beneath the summit",
    "kajikazawa in kai province",
    "ejiri in suruga province",
    "the dream of the fishermans wife",
    "dream of the fishermans wife",
    "the hollow of the deep sea wave off kanagawa",
    "dragon ascending mount fuji",
    "dragon of smoke escaping from mount fuji",
    "tiger in the snow",
    "feminine wave",
    "masculine wave",
    "amida falls",
    "kirifuri waterfall",
    "the ghost of oiwa",
    "cuckoo and azaleas",
    "poppies",
    "irises and grasshopper",
    "canary and peony",
    "hibiscus and sparrow",
    "phoenix",
    "laughing hannya",
    "whaling off goto",
    "choshi in shimosa province",
    "mishima pass in kai province",
    "lake suwa in shinano province",
    "senju musashi province",
    "carp leaping up a cascade",
    "boy viewing mount fuji",
    "travellers crossing the oi river",
    "the waterfall where yoshitsune washed his horse",
    "fuji from gotenyama",
    "shore of tago bay",
}

# ── Subject keywords ──────────────────────────────────────────────────
LANDSCAPE_KW = [
    "mount fuji", "fuji", "province", "bridge", "waterfall", "falls",
    "lake", "river", "sea", "ocean", "bay", "shore", "coast", "island",
    "mountain", "pass", "temple", "shrine", "village", "road", "field",
    "stream", "gorge", "valley", "view of", "views of",
    "ejiri", "kajikazawa", "nihonbashi", "enoshima", "tago", "mishima",
    "senju", "ushibori", "honganji", "suruga", "kai", "musashi",
    "shinano", "shimotsuke", "totomi", "sagami", "kazusa", "shimosa",
    "gotenyama", "tsukuda", "sumida", "mannen", "asakusa",
    "hodogaya", "tokaido", "hakone", "inume", "shojin",
]

NATURE_KW = [
    "flower", "bird", "cuckoo", "crane", "sparrow", "swallow",
    "hawk", "eagle", "rooster", "canary", "bullfinch", "wagtail",
    "turtle", "carp", "fish", "frog", "grasshopper", "dragonfly",
    "butterfly", "bee", "spider", "snake", "lizard",
    "cherry", "chrysanthemum", "iris", "peony", "poppy", "morning glory",
    "hydrangea", "hibiscus", "lily", "lotus", "plum", "wisteria",
    "bamboo", "pine", "willow", "maple",
    "wave", "waves", "wind",
    "azalea", "convolvulus", "bellflower",
]

PORTRAIT_KW = [
    "portrait", "self-portrait", "woman", "courtesan", "geisha",
    "beauty", "beautiful", "bijin",
    "man with", "girl with", "boy",
    "actor", "kabuki",
]

MYTHOLOGY_KW = [
    "ghost", "spirit", "demon", "oni", "tengu", "kappa",
    "dragon", "phoenix", "thunder god", "wind god",
    "raijin", "fujin", "hannya",
    "tale", "legend", "hero",
    "warrior", "samurai", "ronin",
    "bodhisattva", "buddha", "kannon",
    "hundred ghost", "hyaku monogatari",
]

EROTICA_KW = [
    "shunga", "dream of the fisherman",
    "erotic", "lovers",
]


def parse_year(date_str: str):
    """Extract the first 4-digit year from a date string."""
    if not date_str:
        return None
    m = re.search(r"\d{4}", date_str)
    return int(m.group()) if m else None


def assign_era(year) -> str:
    if year is None:
        return "unknown"
    if year < 1800:
        return "early"
    if year <= 1830:
        return "middle"
    return "late"


def assign_subject(title: str, series: str) -> str:
    tl = title.lower()
    sl = series.lower() if series else ""
    combined = tl + " " + sl

    # Priority: erotica > mythology > nature > landscape > portrait > other
    for kw in EROTICA_KW:
        if kw in combined:
            return "erotica"
    for kw in MYTHOLOGY_KW:
        if kw in combined:
            return "mythology"

    # Landscape series take priority
    landscape_series = [
        "thirty-six views", "one hundred views", "waterfalls",
        "bridges", "oceans of wisdom",
    ]
    if any(s in sl for s in landscape_series):
        # But check nature keywords first within landscape series
        for kw in NATURE_KW:
            if kw in tl and kw not in ["wave", "waves", "wind"]:
                return "nature"
        return "landscape"

    for kw in NATURE_KW:
        if kw in combined:
            return "nature"
    for kw in LANDSCAPE_KW:
        if kw in combined:
            return "landscape"
    for kw in PORTRAIT_KW:
        if kw in combined:
            return "portrait"
    return "other"


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"^(the|a|an)\s+", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def is_famous(title: str) -> bool:
    t = normalize(title)
    for f in FAMOUS_TITLES:
        nf = normalize(f)
        if nf == t or nf in t or t in nf:
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
        famous = is_famous(entry.get("title", ""))

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
