#!/usr/bin/env python3
"""
Enrich titian/catalog.json with derived fields:
  era      → "early" | "middle" | "late"
  subject  → "portrait" | "religious" | "mythological" | "allegory" | "other"
  type     → "painting" | "fresco" | "drawing"
  famous   → bool

Reads/writes titian/catalog.json in place.
Uses existing wikidata_genres / wikidata_depicts if present;
falls back to title-keyword heuristics.
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
    "assumption of the virgin",
    "sacred and profane love",
    "venus of urbino",
    "bacchus and ariadne",
    "the pesaro madonna",
    "pesaro madonna",
    "man with a glove",
    "portrait of pope paul iii",
    "diana and actaeon",
    "diana and callisto",
    "the rape of europa",
    "rape of europa",
    "allegory of prudence",
    "venus with a mirror",
    "equestrian portrait of charles v",
    "charles v on horseback",
    "portrait of charles v",
    "flora",
    "the entombment",
    "the presentation of the virgin",
    "concert champetre",
    "noli me tangere",
    "venus and adonis",
    "the flaying of marsyas",
    "flaying of marsyas",
    "pieta",
    "salome",
    "portrait of a man",
    "portrait of a young man",
    "portrait of isabella deste",
    "la bella",
    "girl in a fur",
    "tarquin and lucretia",
    "venus and the lute player",
    "the crown of thorns",
    "ecce homo",
    "danaë",
    "danae",
}

# ── Subject keywords ──────────────────────────────────────────────────
RELIGIOUS_KW = [
    "madonna", "virgin", "christ", "saint", "st.", "annunciation",
    "baptism", "entombment", "assumption", "holy", "resurrection",
    "nativity", "crucifixion", "adoration", "last supper",
    "transfiguration", "presentation", "noli me tangere", "pieta",
    "pietà", "ecce homo", "crown of thorns", "deposition",
    "sacra conversazione", "sacred conversation", "trinity",
    "god the father", "angel", "evangelist", "apostle",
]

MYTHOLOGICAL_KW = [
    "venus", "diana", "bacchus", "apollo", "mars", "jupiter", "minerva",
    "nymph", "perseus", "andromeda", "rape of", "triumph of",
    "flora", "ariadne", "actaeon", "callisto", "danae", "danaë",
    "europa", "adonis", "tarquin", "lucretia", "marsyas", "prometheus",
    "tantalus", "sisyphus", "mythology", "mythological",
    "concert champetre", "champêtre", "bacchanal",
]

PORTRAIT_KW = [
    "portrait", "man with", "woman with", "lady", "gentleman",
    "cardinal", "pope", "emperor", "doge", "duke", "king", "queen",
    "bella", "girl in", "girl with", "young man", "old man",
]

ALLEGORY_KW = [
    "allegory", "sacred and profane", "prudence", "vanity",
    "time", "love", "fortune", "fame",
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
    if year < 1530:
        return "early"
    if year <= 1550:
        return "middle"
    return "late"


def assign_subject(title: str, genres: list, depicts: list) -> str:
    tl = title.lower()
    gl = " ".join(genres).lower()
    dl = " ".join(depicts).lower()
    combined = tl + " " + gl + " " + dl

    # Priority order: religious > mythological > allegory > portrait > other
    for kw in RELIGIOUS_KW:
        if kw in combined:
            return "religious"
    for kw in MYTHOLOGICAL_KW:
        if kw in combined:
            return "mythological"
    for kw in ALLEGORY_KW:
        if kw in combined:
            return "allegory"
    for kw in PORTRAIT_KW:
        if kw in combined:
            return "portrait"
    return "other"


def assign_type(title: str, genres: list) -> str:
    tl = title.lower()
    gl = " ".join(genres).lower()
    if "fresco" in tl or "fresco" in gl:
        return "fresco"
    if "drawing" in tl or "drawing" in gl or "sketch" in tl:
        return "drawing"
    return "painting"


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"^(the|a|an)\s+", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def is_famous(title: str) -> bool:
    t = normalize(title)
    for f in FAMOUS_TITLES:
        if normalize(f) == t or normalize(f) in t or t in normalize(f):
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
        genres = entry.get("wikidata_genres", [])
        depicts = entry.get("wikidata_depicts", [])

        era = assign_era(year)
        subject = assign_subject(entry.get("title", ""), genres, depicts)
        work_type = assign_type(entry.get("title", ""), genres)
        famous = is_famous(entry.get("title", ""))

        entry["era"] = era
        entry["subject"] = subject
        entry["type"] = work_type
        entry["famous"] = famous

        era_counts[era] = era_counts.get(era, 0) + 1
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
        if famous:
            famous_count += 1

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"Enriched {len(catalog)} entries → {CATALOG_PATH}")
    print(f"\nEra distribution:     {era_counts}")
    print(f"Subject distribution: {subject_counts}")
    print(f"Famous works:         {famous_count}")


if __name__ == "__main__":
    main()
