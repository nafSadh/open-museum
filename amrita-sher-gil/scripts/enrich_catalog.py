#!/usr/bin/env python3
"""
Enrich amrita-sher-gil/catalog.json with derived fields:
  era      -> "paris" (pre-1934) | "india" (1934-1941)
  subject  -> "portrait" | "village" | "self-portrait" | "other"
  famous   -> bool

Reads/writes amrita-sher-gil/catalog.json in place.
Uses title-keyword heuristics to classify works.
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
    # Paris period
    "young girls",
    "sleep",
    "self-portrait as tahitian",
    "professional model",
    "portrait of marie louise chassany",
    "hungarian gypsy girl",
    "self-portrait 1",
    "self-portrait 2",
    # India period
    "group of three girls",
    "group of young girls",
    "bride's toilet",
    "brides toilet",
    "brahmacharis",
    "south indian villagers going to market",
    "village scene",
    "in the ladies enclosure",
    "in the ladies' enclosure",
    "two women",
    "hill men",
    "hill women",
    "ancient story teller",
    "ancient storyteller",
    "red clay elephant",
    "elephant promenade",
    "woman on charpai",
    "woman on the charpai",
    "mother india",
    "haldi grinders",
    "the haldi grinders",
    "camels",
    "resting",
    "siesta",
    "three girls",
    "the swing",
    "woman resting on a charpoy",
    "the child bride",
    "child bride",
    "ganesh puja",
    "women on the ghats",
    "fruit vendors",
    "summer",
    "village girls",
    "two elephants",
    "raja surat singh",
}

# ── Subject keywords ──────────────────────────────────────────────────
SELF_PORTRAIT_KW = [
    "self-portrait", "self portrait", "autoportrait",
]

PORTRAIT_KW = [
    "portrait", "man with", "woman with", "lady", "girl",
    "klára", "clara", "marie", "boris", "ervin",
    "raja", "maharaja", "rani", "denyse",
    "mrs", "mr", "madame",
]

VILLAGE_KW = [
    "village", "villager", "market", "bride", "brahmachar",
    "haldi", "grinder", "charpai", "charpoy", "ghats",
    "hill men", "hill women", "fruit vendor", "camels",
    "elephant", "swing", "resting", "siesta", "ganesh puja",
    "bathing", "women on", "summer", "winter",
    "ancient story", "child bride", "mother india",
    "two women", "three girls", "group of",
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
    if year < 1934:
        return "paris"
    return "india"


def assign_subject(title: str) -> str:
    tl = title.lower()

    # Self-portraits take priority
    for kw in SELF_PORTRAIT_KW:
        if kw in tl:
            return "self-portrait"

    # Village/rural scenes
    for kw in VILLAGE_KW:
        if kw in tl:
            return "village"

    # Portraits
    for kw in PORTRAIT_KW:
        if kw in tl:
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
