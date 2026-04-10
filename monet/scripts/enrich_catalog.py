#!/usr/bin/env python3
"""
Enrich monet/catalog.json with derived fields:
  era      → "early" | "impressionist" | "series"
  subject  → "landscape" | "water" | "garden" | "portrait" | "still_life" | "urban" | "other"
  famous   → bool

Reads/writes monet/catalog.json in place.
"""

import json, os, re
from collections import Counter

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "catalog.json",
)

# ── Famous works ─────────────────────────────────────────────────────
FAMOUS_TITLES = {
    "impression, sunrise",
    "impression sunrise",
    "women in the garden",
    "woman in the garden",
    "luncheon on the grass",
    "the luncheon on the grass",
    "la grenouillere",
    "la grenouillère",
    "the grenouillere",
    "the grenouillère",
    "bathers at la grenouillere",
    "bathers at la grenouillere",
    "the magpie",
    "woman with a parasol",
    "camille monet with a parasol",
    "camille",
    "the bridge at argenteuil",
    "regatta at argenteuil",
    "the seine at argenteuil",
    "boats at argenteuil",
    "gare saint-lazare",
    "the gare saint-lazare",
    "saint-lazare station",
    "haystacks",
    "stacks of wheat",
    "rouen cathedral",
    "water lilies",
    "nymphéas",
    "nympheas",
    "the japanese bridge",
    "japanese bridge",
    "bridge over a pond of water lilies",
    "water lily pond",
    "poplars",
    "poplar series",
    "cliffs at etretat",
    "the manneporte",
    "the needle at etretat",
    "the cliff",
    "london, houses of parliament",
    "houses of parliament",
    "charing cross bridge",
    "waterloo bridge",
    "venice",
    "grand canal",
    "palazzo da mula",
    "bordighera",
    "morning on the seine",
    "branch of the seine",
    "the seine in flood",
    "ice floes",
    "breakup of ice",
    "garden at giverny",
    "irises",
    "the water lily pond",
    "agapanthus",
    "the artist's garden at giverny",
    "the artist's garden at vétheuil",
    "camille on her deathbed",
}


def parse_year(date_str: str):
    if not date_str:
        return None
    m = re.search(r"\d{4}", str(date_str))
    return int(m.group()) if m else None


def assign_era(year) -> str:
    """
    early        → before 1870  (early career, proto-Impressionism)
    impressionist→ 1870–1890   (core Impressionist period, Argenteuil etc.)
    series       → after 1890   (famous series: haystacks, cathedrals, water lilies)
    """
    if year is None:
        return "unknown"
    if year < 1870:
        return "early"
    if year <= 1890:
        return "impressionist"
    return "series"


# Subject keyword lists
WATER_KW = [
    "water lili", "nymphea", "pond", "lake", "river", "seine",
    "thames", "canal", "lagoon", "sea", "seashore", "coast",
    "cliff", "beach", "ocean", "harbour", "harbor", "port",
    "boats", "boat", "regatta", "sailing", "fishermen",
    "bridge", "grenouill", "flood", "ice floe", "breakup of ice",
    "venice", "grand canal", "palazzo",
]
GARDEN_KW = [
    "garden", "giverny", "irises", "agapanthus", "roses",
    "chrysanthemum", "gladioli", "tulip", "poppy", "wisteria",
    "flower", "flowerbed", "path in", "spring flower",
]
PORTRAIT_KW = [
    "portrait", "woman with", "man with", "camille", "jean monet",
    "alice", "suzanne", "blanche", "self-portrait", "madame",
    "lady", "girl", "young woman", "child",
]
STILL_LIFE_KW = [
    "still life", "pheasant", "partridge", "hunting trophy",
    "fruit", "apple", "bottle", "carafe", "meat", "bread",
    "dog's head", "greyhound",
]
URBAN_KW = [
    "gare saint-lazare", "saint-lazare", "boulevard", "street",
    "houses of parliament", "charing cross", "waterloo bridge",
    "westminster", "city", "town", "village", "church", "cathedral",
    "rouen", "factory", "factories", "industrial",
]
LANDSCAPE_KW = [
    "landscape", "meadow", "field", "forest", "road", "path",
    "farm", "farmyard", "haystack", "wheat", "poplar", "wood",
    "valley", "hill", "plain", "pasture", "moor", "sunrise",
    "sunset", "snow", "winter", "morning", "effect of snow",
    "bordighera", "antibes", "etretat", "étretat", "pourville",
    "varengeville", "vétheuil", "vetheuil", "argenteuil",
    "cliffs", "rocky", "trees",
]


def assign_subject(title: str, series: str) -> str:
    tl = title.lower()
    sl = (series or "").lower()
    combined = tl + " " + sl

    for kw in PORTRAIT_KW:
        if kw in combined:
            return "portrait"
    for kw in STILL_LIFE_KW:
        if kw in combined:
            return "still_life"
    for kw in WATER_KW:
        if kw in combined:
            return "water"
    for kw in GARDEN_KW:
        if kw in combined:
            return "garden"
    for kw in URBAN_KW:
        if kw in combined:
            return "urban"
    for kw in LANDSCAPE_KW:
        if kw in combined:
            return "landscape"
    return "other"


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"^(the|a|an|le|la|les)\s+", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def is_famous(title: str, series: str) -> bool:
    t = normalize(title)
    s = normalize(series or "")
    for f in FAMOUS_TITLES:
        fn = normalize(f)
        if fn == t or fn in t or t in fn:
            return True
    # Works in iconic series are famous by default
    if series in {"water lilies", "haystacks", "rouen cathedral",
                  "japanese bridge", "poplars", "houses of parliament"}:
        return True
    return False


def main():
    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)

    era_counts, subject_counts = {}, {}
    famous_count = 0

    for entry in catalog:
        year = parse_year(entry.get("date", ""))
        title = entry.get("title", "")
        series = entry.get("series", "other")

        era = assign_era(year)
        subject = assign_subject(title, series)
        famous = is_famous(title, series)

        entry["era"] = era
        entry["subject"] = subject
        entry["famous"] = famous

        era_counts[era] = era_counts.get(era, 0) + 1
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
        if famous:
            famous_count += 1

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"Enriched {len(catalog)} entries → {CATALOG_PATH}")
    print(f"\nEra:     {dict(sorted(era_counts.items()))}")
    print(f"Subject: {dict(sorted(subject_counts.items()))}")
    print(f"Famous:  {famous_count}")


if __name__ == "__main__":
    main()
