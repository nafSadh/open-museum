#!/usr/bin/env python3
"""
Enrich rembrandt/catalog.json with derived fields:
  era     → "early" | "middle" | "late"
  subject → "portrait" | "religious" | "mythological" | "landscape" | "genre" | "other"
  famous  → bool

Reads/writes rembrandt/catalog.json in place.
"""

import json
import os
import re

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "catalog.json",
)

# Famous works by Rembrandt
FAMOUS_TITLES = {
    "the night watch",
    "night watch",
    "the anatomy lesson of dr. nicolaes tulp",
    "anatomy lesson of dr. nicolaes tulp",
    "the anatomy lesson of dr tulp",
    "self-portrait with two circles",
    "self portrait with two circles",
    "the return of the prodigal son",
    "return of the prodigal son",
    "the syndics of the drapers' guild",
    "the syndics",
    "syndics of the drapers guild",
    "the jewish bride",
    "jewish bride",
    "bathsheba at her bath",
    "bathsheba",
    "the storm on the sea of galilee",
    "storm on the sea of galilee",
    "aristotle with a bust of homer",
    "aristotle contemplating a bust of homer",
    "the blinding of samson",
    "blinding of samson",
    "susanna and the elders",
    "the mill",
    "the polish rider",
    "polish rider",
    "man in a golden helmet",
    "man with a golden helmet",
    "saskia van uylenburgh in arcadian costume",
    "self-portrait as the apostle paul",
    "the hundred guilder print",
    "hundred guilder print",
    "the three crosses",
    "three crosses",
    "ecce homo",
    "christ presented to the people",
    "portrait of jan six",
    "the three trees",
    "three trees",
    "self-portrait",
    "landscape with three trees",
    "the rape of ganymede",
    "rape of ganymede",
    "danae",
    "danaë",
    "the adoration of the magi",
    "adoration of the magi",
    "the presentation in the temple",
    "joseph's coat brought to jacob",
    "the conspiracy of claudius civilis",
    "conspiracy of claudius civilis",
    "belshazzar's feast",
    "belshazzars feast",
    "st. john the baptist preaching",
    "jacob wrestling with the angel",
    "the raising of lazarus",
    "man in armour",
    "self-portrait at the easel",
    "titus reading",
    "hendrickje stoffels",
    "portrait of an old man in red",
    "the shipbuilder and his wife",
    "the standard bearer",
    "minerva",
    "an old woman reading",
    "old woman reading",
    "the prodigal son in the brothel",
    "self-portrait with beret",
}

RELIGIOUS_KW = [
    "christ", "jesus", "madonna", "virgin", "saint", "st.", "apostle",
    "angel", "baptism", "annunciation", "nativity", "crucifixion",
    "adoration", "resurrection", "entombment", "deposition",
    "presentation", "circumcision", "flight into egypt", "holy family",
    "holy", "prodigal son", "lazarus", "samson", "david", "goliath",
    "bathsheba", "susanna", "joseph", "jacob", "esau", "abraham",
    "isaac", "elders", "belshazzar", "conspiracy", "saul", "hannah",
    "elijah", "tobias", "tobit", "simeon", "anna", "peter", "paul",
    "matthew", "john the baptist", "jerome", "augustine", "francis",
    "gideon", "jephthah", "potiphar", "manoah", "hagar", "jeremiah",
    "jeremiah lamenting", "agony in the garden", "ecce homo",
    "hundred guilder", "three crosses", "raising of", "pieta", "pietà",
    "moses", "temple", "galilee",
]

MYTHOLOGICAL_KW = [
    "ganymede", "danae", "danaë", "flora", "minerva", "diana", "venus",
    "mars", "jupiter", "juno", "mercury", "pluto", "proserpine",
    "europa", "rape of", "triumph of", "arcadian", "antique", "mythological",
    "classical", "bellona",
]

PORTRAIT_KW = [
    "portrait", "self-portrait", "self portrait", "man in", "man with",
    "woman in", "woman with", "lady", "gentleman", "girl", "boy",
    "old man", "old woman", "young man", "young woman",
    "standard bearer", "soldier", "burgher", "merchant", "scholar",
    "rabbi", "officer", "captain", "rijksmuseum", "jan six",
    "saskia", "hendrickje", "titus", "polish rider",
]

LANDSCAPE_KW = [
    "landscape", "river", "winter", "storm", "sea", "coast", "river",
    "trees", "farmhouse", "mill", "village", "countryside", "windmill",
    "canal", "three trees",
]

GENRE_KW = [
    "kitchen", "domestic", "still life", "still-life", "allegory",
    "philosopher", "scholar", "reading", "writing", "musician",
    "night watch", "anatomy lesson", "syndics", "guild",
    "ship", "biblical scene",
]


def parse_year(date_str: str):
    if not date_str:
        return None
    m = re.search(r"\d{4}", date_str)
    return int(m.group()) if m else None


def assign_era(year) -> str:
    """
    Early: before 1640 (Leiden + early Amsterdam)
    Middle: 1640–1655 (mature Amsterdam)
    Late: after 1655 (late style)
    """
    if year is None:
        return "unknown"
    if year < 1640:
        return "early"
    if year <= 1655:
        return "middle"
    return "late"


def assign_subject(title: str, medium: str) -> str:
    if medium == "etching":
        tl = title.lower()
        for kw in RELIGIOUS_KW:
            if kw in tl:
                return "religious"
        for kw in MYTHOLOGICAL_KW:
            if kw in tl:
                return "mythological"
        for kw in PORTRAIT_KW:
            if kw in tl:
                return "portrait"
        for kw in LANDSCAPE_KW:
            if kw in tl:
                return "landscape"
        return "other"

    tl = title.lower()
    # Priority: religious > mythological > portrait > landscape > genre > other
    for kw in RELIGIOUS_KW:
        if kw in tl:
            return "religious"
    for kw in MYTHOLOGICAL_KW:
        if kw in tl:
            return "mythological"
    for kw in PORTRAIT_KW:
        if kw in tl:
            return "portrait"
    for kw in LANDSCAPE_KW:
        if kw in tl:
            return "landscape"
    for kw in GENRE_KW:
        if kw in tl:
            return "genre"
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
        medium = entry.get("medium", "painting")

        era = assign_era(year)
        subject = assign_subject(entry.get("title", ""), medium)
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

    print(f"Enriched {len(catalog)} entries → {CATALOG_PATH}")
    print(f"\nEra distribution:     {era_counts}")
    print(f"Subject distribution: {subject_counts}")
    print(f"Famous works:         {famous_count}")


if __name__ == "__main__":
    main()
