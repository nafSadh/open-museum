#!/usr/bin/env python3
"""
Enrich xu-beihong/catalog.json with derived fields:
  era      -> "early" (pre-1927) | "mature" (1927-1945) | "late" (post-1945)
  subject  -> "horses" | "animals" | "portrait" | "landscape" | "mythology" | "other"
  famous   -> bool

Reads/writes xu-beihong/catalog.json in place.

Era divisions based on Xu Beihong's life:
  - Early (pre-1927): student years in Japan and Europe (Paris, Berlin)
  - Mature (1927-1945): return to China, teaching at Central University,
    wartime period, most iconic works created
  - Late (post-1945): post-war, president of Central Academy of Fine Arts,
    final prolific years until death in 1953
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
    # Iconic horse paintings
    "galloping horse",
    "eight horses",
    "the eight horses",
    "warhorse",
    "three steeds",
    "jiuju",
    # Major historical/mythological paintings
    "tian heng and five hundred heroes",
    "tianheng five hundreds heroes",
    "dian heng and five hundreds heroes",
    "yugongyishan",
    "put down your whip",
    "zhensanli",
    # Famous portraits
    "liao jingwen",
    "portrait of kang youwei",
    "portrait of madam kang youwei",
    "sun duoci",
    # Notable animal paintings
    "cat on rock scroll",
    "tiger",
    "buffle et serpent",
    # Other notable works
    "banana trees and sparrows",
}

# ── Subject keywords ──────────────────────────────────────────────────
HORSE_KW = [
    "horse", "horses", "galloping", "stallion", "mare", "foal",
    "equestrian", "riding", "cavalry", "warhorse",
    "马", "馬", "駿", "驹",
]

ANIMAL_KW = [
    "cat", "cats", "lion", "tiger", "eagle", "sparrow", "bird",
    "rooster", "chicken", "ox", "buffalo", "buffle",
    "snake", "serpent", "fish", "crane", "magpie",
    "虎", "貓", "猫", "鸡", "鹰",
]

PORTRAIT_KW = [
    "portrait", "ms ", "mr ", "mrs ", "madam", "mdm",
    "lady", "woman", "man", "self-portrait", "selfportrait",
    "sketch of", "liao jingwen", "sun duoci", "yan jici",
    "jenny", "christina", "jiang biwei",
    "kang youwei", "康有为",
]

LANDSCAPE_KW = [
    "landscape", "mountain", "river", "tree", "bamboo", "orchid",
    "banana", "pine", "lotus", "plum blossom", "scenery",
    "willow", "bridge", "waterfall",
]

MYTHOLOGY_KW = [
    "tian heng", "tianheng", "yu gong", "yugong",
    "heroes", "foolish old man", "mythology",
    "legend", "zhensanli", "slave and lion",
    "put down your whip",
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
    if year < 1927:
        return "early"
    if year <= 1945:
        return "mature"
    return "late"


def assign_subject(title: str, filename: str = "") -> str:
    combined = (title + " " + filename).lower()

    # Priority: horses first (his most iconic subject)
    for kw in HORSE_KW:
        if kw in combined:
            return "horses"
    for kw in MYTHOLOGY_KW:
        if kw in combined:
            return "mythology"
    for kw in PORTRAIT_KW:
        if kw in combined:
            return "portrait"
    for kw in ANIMAL_KW:
        if kw in combined:
            return "animals"
    for kw in LANDSCAPE_KW:
        if kw in combined:
            return "landscape"
    return "other"


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"^(the|a|an)\s+", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def is_famous(title: str, filename: str = "") -> bool:
    t = normalize(title)
    for f in FAMOUS_TITLES:
        nf = normalize(f)
        if nf == t or nf in t:
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
        title = entry.get("title", "")
        filename = entry.get("commons_filename", "")

        era = assign_era(year)
        subject = assign_subject(title, filename)
        famous = is_famous(title, filename)

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
