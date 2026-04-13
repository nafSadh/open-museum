#!/usr/bin/env python3
"""
Enrich kuniyoshi/catalog.json with derived fields:
  era      -> "early" (pre-1830) | "mature" (1830-1845) | "late" (post-1845)
  subject  -> "warrior" | "mythology" | "nature" | "cats" | "landscape" | "other"
  famous   -> bool

Reads/writes kuniyoshi/catalog.json in place.
Uses title-keyword heuristics for classification.
"""

import json
import os
import re

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "catalog.json",
)

# -- Known famous works -------------------------------------------------------
FAMOUS_TITLES = {
    "takiyasha the witch and the skeleton spectre",
    "skeleton spectre",
    "miyamoto musashi",
    "miyamoto musashi killing a giant lizard",
    "cats forming the characters for catfish",
    "cats suggested as the fifty-three stations of the tokaido",
    "four cats in different poses",
    "saito oniwakamaru",
    "saito oniwakamaru fights the giant carp",
    "hanagami danjo no jo arakage",
    "hanagami danjo no jo arakage fighting a giant salamander",
    "hatsuhana doing penance under the tonosawa waterfall",
    "keyamura rokusuke under the hikosan gongen waterfall",
    "oda nobunaga",
    "yoshitsune and benkei",
    "yoshitsune and benkei defending themselves in boat",
    "minamoto no tametomo",
    "on the shore of the sumida river",
    "mt fuji from the sumida",
    "pilgrims in the waterfall",
    "kajiwara kagesue",
    "the first emperor of the qin dynasty",
    "banners for boys day festival",
    "scribbling on the storehouse wall",
    "at first glance he looks very fierce",
    "portrait of chicasei goyo",
    "one hundred and eight heroes of the popular suikoden",
    "heroes of our country s suikoden",
    "the monster s chushingura",
    "takeda nobushige",
    "kakinomoto no hitomaro",
    "courtesan in training",
    "cats suggested as the fifty three stations",
    "portrait of chicasei goyo",
    "portrait of chicasei",
    "acts 9 11 of the kanadehon chushingura",
    "acts 5 8 of the kanadehon chushingura",
    "acts 1 4 of the kanadehon chushingura",
}

# -- Subject keywords ----------------------------------------------------------
WARRIOR_KW = [
    "warrior", "samurai", "battle", "fight", "sword", "hero",
    "suikoden", "musashi", "benkei", "yoshitsune", "tametomo",
    "nobunaga", "generals", "kagesue", "takatsuna", "shigetada",
    "arakage", "oniwakamaru", "nobushige", "rokusuke", "loyalty",
    "revenge", "filial piety", "paragons", "fidelity",
    "chushingura", "water margin", "chicasei",
    "killing", "fighting", "defending", "banners",
]

MYTHOLOGY_KW = [
    "witch", "skeleton", "spectre", "ghost", "demon", "spirit",
    "monster", "supernatural", "dragon", "magic", "spell",
    "takiyasha", "emperor of the qin", "qin dynasty",
    "chushingura", "chūshingura", "kanadehon",
    "taira", "ghosts",
]

NATURE_KW = [
    "waterfall", "carp", "salamander", "lizard", "fish",
    "insect", "bird", "flower", "animal", "goldfish",
    "tonosawa", "hikosan", "bishimon",
]

CAT_KW = [
    "cat", "cats", "catfish", "kitten", "neko",
]

LANDSCAPE_KW = [
    "landscape", "sumida", "fuji", "view", "famous views",
    "tokaido", "kisokaido", "station", "pilgrims",
    "shore", "river", "mountain",
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
    if year < 1830:
        return "early"
    if year <= 1845:
        return "mature"
    return "late"


def assign_subject(title: str) -> str:
    tl = title.lower()

    # Cats first (most specific)
    for kw in CAT_KW:
        if kw in tl:
            return "cats"

    # Mythology/supernatural
    for kw in MYTHOLOGY_KW:
        if kw in tl:
            return "mythology"

    # Nature (animals, waterfalls)
    for kw in NATURE_KW:
        if kw in tl:
            return "nature"

    # Landscape
    for kw in LANDSCAPE_KW:
        if kw in tl:
            return "landscape"

    # Warrior (broadest)
    for kw in WARRIOR_KW:
        if kw in tl:
            return "warrior"

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

        era = assign_era(year)
        subject = assign_subject(entry.get("title", ""))
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
