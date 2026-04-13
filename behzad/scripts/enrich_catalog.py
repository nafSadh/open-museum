#!/usr/bin/env python3
"""
Enrich behzad/catalog.json with derived fields:
  subject  -> "court" | "literary" | "religious" | "portrait" | "other"
  famous   -> bool

Reads/writes behzad/catalog.json in place.
Uses title-keyword heuristics to classify Persian miniature subjects.
"""

import json
import os
import re

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "catalog.json",
)

# ── Known famous works ────────────────────────────────────────────────
# Behzad's most celebrated and frequently referenced miniatures.
# Only the most recognizable titles; kept narrow to avoid over-matching.
FAMOUS_TITLES = {
    # Bustan of Sa'di illustrations (1488) — his masterpiece manuscript
    "yusuf and zulaikha",
    "yusef and zuleykha",
    "yusuf fleeing the advances of zulaikha",
    "seduction of yusuf",
    # Khamsa of Nizami illustrations
    "construction of the fort of kharnaq",
    "construction of khawarnaq",
    "building of the palace of khavarnaq",
    "the building of the palace of khavarnaq",
    # Famous individual works
    "dance of sufi dervishes",
    "dancing dervishes",
    "portrait of a dervish",
    # Battle/court scenes
    "battleground of timur and the mamluk sultan of egypt",
    "battle of timur and egypt",
    "timur granting audience on the occasion of his accession",
    # Zafarnama illustrations
    "building of the great mosque in samarkand",
    "building samarkand mosque",
    # Hunting scenes
    "the hunting ground",
    # Battle
    "battle on the river oxus",
    # Famous portraits
    "sultan husayn mirza by bihzad",
    "shah ismail i safavid",
    # Other famous works
    "the old man and the youth",
    "the old man encounters a youth",
    "darius and the herdsman",
    "the beggar at the mosque",
    "behzad beggar at a mosque",
    "a convivial gathering",
    "harun al-rashid and the barber",
    "funeral of the elderly attar",
    "beheading of a king",
}

# Titles to exclude from famous — photo variants, signatures, crops, etc.
FAMOUS_EXCLUDE_PATTERNS = [
    r'\bMET\b',
    r'\bsignature\b',
    r'\bfrontispiece\b',
    r'\bcropped\b',
    r'\bfolio\b.*\bMET\b',
]

# ── Subject keywords ──────────────────────────────────────────────────

# Court scenes: battles, royal audiences, hunting, political events
COURT_KW = [
    "battle", "timur", "siege", "assault", "troops", "army",
    "audience", "accession", "sultan", "shah", "king", "prince",
    "court", "gathering", "hunting", "hunt", "horseback",
    "fortress", "castle", "mosque", "samarkand", "building of",
    "construction", "palace", "royal", "equestrian",
    "umar shaykh", "jahangir mirza", "muhammad muhsin",
    "herat", "khiva", "urgench", "smyrna", "nerges",
    "georgia", "oxus", "kipchak",
    "zafarnama", "iskandar", "alexander",
]

# Literary: illustrations from literary texts (Khamsa, Bustan, Divan, etc.)
LITERARY_KW = [
    "yusuf", "zulaikha", "zuleykha", "khusraw", "shirin",
    "majnun", "layla", "leyla", "nizami", "khamsa",
    "bustan", "gulistan", "divan", "hafiz", "jami",
    "firdawsi", "shahnameh", "shahnama", "iskandarnama",
    "bahram", "dragon", "rostam", "div",
    "dervish", "dervishes", "dancing", "sufi",
    "hermit", "ascetic", "poet", "judge",
    "old man", "youth", "herdsman", "beggar",
    "attar", "hatifi", "khusraw",
    "sa'di", "sadi", "amir khusraw",
    "hasht bihisht", "hasht-bihisht",
    "seduction",
]

# Religious: Islamic religious themes
RELIGIOUS_KW = [
    "prophet", "muhammad", "mosque", "prayer", "quran",
    "mecca", "medina", "imam", "holy", "mi'raj", "miraj",
    "funeral", "burial", "harun al-rashid",
    "barber",  # the Harun al-Rashid and the barber story
]

# Portrait: individual portraits
PORTRAIT_KW = [
    "portrait", "self-portrait", "self portrait",
    "sultan husayn", "shah ismail", "shah tahmasp",
    "muhammad shaybani",
]


def assign_subject(title: str) -> str:
    """Classify a work by subject based on title keywords."""
    tl = title.lower()

    # Priority: portrait > religious > court > literary > other
    for kw in PORTRAIT_KW:
        if kw in tl:
            return "portrait"
    for kw in RELIGIOUS_KW:
        if kw in tl:
            return "religious"
    for kw in COURT_KW:
        if kw in tl:
            return "court"
    for kw in LITERARY_KW:
        if kw in tl:
            return "literary"
    return "other"


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"^(the|a|an)\s+", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def is_famous(title: str) -> bool:
    t = normalize(title)
    tl = title.lower()

    # Exclude photo variants, signatures, crops
    for pat in FAMOUS_EXCLUDE_PATTERNS:
        if re.search(pat, title, re.IGNORECASE):
            return False

    for f in FAMOUS_TITLES:
        nf = normalize(f)
        if nf == t or nf in t or t in nf:
            return True
    return False


def main():
    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)

    subject_counts = {}
    famous_count = 0

    for entry in catalog:
        title = entry.get("title", "")
        # Also consider commons_filename for classification
        filename = entry.get("commons_filename", "")
        combined_title = title + " " + filename.replace("_", " ")

        subject = assign_subject(combined_title)
        famous = is_famous(combined_title)

        entry["subject"] = subject
        entry["famous"] = famous

        subject_counts[subject] = subject_counts.get(subject, 0) + 1
        if famous:
            famous_count += 1

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"Enriched {len(catalog)} entries -> {CATALOG_PATH}")
    print(f"\nSubject distribution: {subject_counts}")
    print(f"Famous works:         {famous_count}")


if __name__ == "__main__":
    main()
