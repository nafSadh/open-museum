#!/usr/bin/env python3
"""
Enrich degas/catalog.json with derived fields:
  era     → "early" | "impressionist" | "late"
  subject → "dance" | "portrait" | "nude" | "racing" | "landscape" | "genre" | "other"
  famous  → bool

Reads/writes degas/catalog.json in place.

Degas eras:
  early: before 1870 (academic period, history paintings)
  impressionist: 1870–1886 (Impressionist exhibitions era)
  late: after 1886 (mature pastels, failing eyesight)
"""

import json
import os
import re

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "catalog.json",
)

FAMOUS_TITLES = {
    "the dance class",
    "dance class",
    "the ballet class",
    "ballet class",
    "the star",
    "l'etoile",
    "the bellelli family",
    "bellelli family",
    "the absinthe drinker",
    "absinthe",
    "l'absinthe",
    "the tub",
    "after the bath",
    "little dancer of fourteen years",
    "little dancer aged fourteen",
    "the little fourteen-year-old dancer",
    "a cotton office in new orleans",
    "cotton office",
    "the orchestra at the opera",
    "orchestra of the opera",
    "musicians in the orchestra",
    "the dance foyer at the opera",
    "rehearsal of the ballet",
    "ballet rehearsal",
    "dancers",
    "blue dancers",
    "dancers in blue",
    "four dancers",
    "two dancers",
    "dancers at the barre",
    "dancers at the bar",
    "woman ironing",
    "women ironing",
    "the laundresses",
    "miss la la at the cirque fernando",
    "miss lala",
    "at the races",
    "race horses",
    "racehorses",
    "jockeys",
    "the millinery shop",
    "at the milliner's",
    "woman with chrysanthemums",
    "self-portrait",
    "self portrait",
    "place de la concorde",
    "the rape",
    "interior",
    "sulking",
    "combing the hair",
    "woman combing her hair",
    "the bath",
    "morning bath",
}

DANCE_KW = [
    "dancer", "ballet", "dance", "ballerina", "barre", "rehearsal",
    "star", "l'etoile", "foyer", "tutu", "prima",
]

PORTRAIT_KW = [
    "portrait", "self-portrait", "self portrait", "bellelli",
    "woman with", "man with", "mademoiselle", "madame", "monsieur",
    "miss la la", "place de la concorde",
]

NUDE_KW = [
    "nude", "bath", "bather", "tub", "after the bath", "toilette",
    "combing", "washing", "morning bath",
]

RACING_KW = [
    "race", "jockey", "horse", "racehorses", "races", "steeplechase",
]

LANDSCAPE_KW = [
    "landscape", "seascape", "coast", "mountain", "field",
]

GENRE_KW = [
    "ironing", "laundress", "millinery", "milliner", "absinthe",
    "cotton", "café", "cafe", "interior", "sulking", "rape",
    "orchestra", "musicians", "opera", "circus", "cirque",
    "woman ironing", "women ironing",
]


def parse_year(date_str: str):
    if not date_str:
        return None
    m = re.search(r"\d{4}", date_str)
    return int(m.group()) if m else None


def assign_era(year) -> str:
    if year is None:
        return "unknown"
    if year < 1870:
        return "early"
    if year <= 1886:
        return "impressionist"
    return "late"


def assign_subject(title: str) -> str:
    tl = title.lower()
    for kw in DANCE_KW:
        if kw in tl:
            return "dance"
    for kw in NUDE_KW:
        if kw in tl:
            return "nude"
    for kw in RACING_KW:
        if kw in tl:
            return "racing"
    for kw in PORTRAIT_KW:
        if kw in tl:
            return "portrait"
    for kw in GENRE_KW:
        if kw in tl:
            return "genre"
    for kw in LANDSCAPE_KW:
        if kw in tl:
            return "landscape"
    return "other"


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"^(the|a|an|l')\s*", "", s)
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
