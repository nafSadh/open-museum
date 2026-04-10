#!/usr/bin/env python3
"""
Enrich vermeer/catalog.json with derived fields:
  era     → "early" | "middle" | "late"
  subject → "genre" | "allegory" | "portrait" | "landscape" | "religious" | "other"
  famous  → bool

Reads/writes vermeer/catalog.json in place.

Vermeer's career is short (~1653–1675), so eras are:
  early:  before 1658 (history paintings + early genre)
  middle: 1658–1665 (peak genre scenes, interiors)
  late:   after 1665 (late style, allegories)
"""

import json
import os
import re

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "catalog.json",
)

FAMOUS_TITLES = {
    "girl with a pearl earring",
    "the milkmaid",
    "milkmaid",
    "the girl with the pearl earring",
    "girl with the pearl earring",
    "the art of painting",
    "art of painting",
    "the allegory of painting",
    "allegory of painting",
    "view of delft",
    "the little street",
    "little street",
    "the love letter",
    "love letter",
    "the lacemaker",
    "lacemaker",
    "woman with a pearl necklace",
    "woman with a balance",
    "woman holding a balance",
    "the music lesson",
    "music lesson",
    "the concert",
    "concert",
    "officer and laughing girl",
    "the astronomer",
    "astronomer",
    "the geographer",
    "geographer",
    "a lady writing",
    "lady writing a letter",
    "the glass of wine",
    "glass of wine",
    "girl reading a letter at an open window",
    "girl reading a letter by an open window",
    "the procuress",
    "procuress",
    "diana and her companions",
    "diana and her nymphs",
    "christ in the house of martha and mary",
    "allegory of the catholic faith",
    "a lady standing at a virginal",
    "a lady seated at a virginal",
    "young woman with a water pitcher",
    "woman in blue reading a letter",
    "the letter",
    "mistress and maid",
    "a girl asleep",
    "girl interrupted at her music",
    "lady writing a letter with her maid",
}

GENRE_KW = [
    "milkmaid", "lacemaker", "music lesson", "concert", "wine",
    "girl reading", "woman reading", "letter", "virginal",
    "interrupted", "girl asleep", "woman in blue", "water pitcher",
    "maid", "mistress", "officer and laughing", "glass of",
    "procuress", "girl with a flute", "girl with a red hat",
    "young woman", "lady writing", "lady standing", "lady seated",
    "woman with a", "woman holding",
]

ALLEGORY_KW = [
    "allegory", "art of painting", "faith",
]

PORTRAIT_KW = [
    "portrait", "girl with a pearl earring", "head of a girl",
    "study of a young woman",
]

LANDSCAPE_KW = [
    "view of delft", "little street",
]

RELIGIOUS_KW = [
    "christ", "martha", "mary", "diana", "saint", "praxis",
]


def parse_year(date_str: str):
    if not date_str:
        return None
    m = re.search(r"\d{4}", date_str)
    return int(m.group()) if m else None


def assign_era(year) -> str:
    if year is None:
        return "unknown"
    if year < 1658:
        return "early"
    if year <= 1665:
        return "middle"
    return "late"


def assign_subject(title: str) -> str:
    tl = title.lower()
    for kw in RELIGIOUS_KW:
        if kw in tl:
            return "religious"
    for kw in ALLEGORY_KW:
        if kw in tl:
            return "allegory"
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

    print(f"Enriched {len(catalog)} entries → {CATALOG_PATH}")
    print(f"\nEra distribution:     {era_counts}")
    print(f"Subject distribution: {subject_counts}")
    print(f"Famous works:         {famous_count}")


if __name__ == "__main__":
    main()
