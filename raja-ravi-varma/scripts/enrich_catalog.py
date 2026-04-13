#!/usr/bin/env python3
"""
Enrich raja-ravi-varma/catalog.json with derived fields:
  era      -> "early" (pre-1880) | "mature" (1880-1900) | "late" (post-1900)
  subject  -> "mythology" | "portrait" | "landscape" | "other"
  famous   -> bool

Reads/writes raja-ravi-varma/catalog.json in place.
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
    # Mythological masterpieces
    "shakuntala",
    "shakuntala looking for dushyanta",
    "shakuntala patralekhan",
    "shakuntala writing a love letter",
    "damayanti talking to a swan",
    "damayanti",
    "nala and damayanti",
    "hansa damayanthi",
    "galaxy of musicians",
    "mohini on a swing",
    "radha in the moonlight",
    "radha waiting for krishna",
    "sita bhumipravesh",
    "sita taken by goddess earth",
    "draupadi vastraharan",
    "draupadi humiliated",
    "menaka and vishvamitra",
    "vishwamitra and menaka",
    "ganga and shantanu",
    "krishna as envoy",
    "sri krishna as envoy",
    "birth of krishna",
    "urvashi and pururavas",
    "mohini bhasmasura",
    "saraswati",
    "lakshmi",
    "keechaka and sairandhri",
    "arjuna and subhadra",
    "harishchandra",
    "satyavan savitri",
    "descent of ganga",
    # Famous portraits and genre scenes
    "nair lady adorning her hair",
    "village belle",
    "malabar beauty",
    "maharashtrian beauty",
    "lady with a mirror",
    "the milkmaid",
    "there comes papa",
    "lady giving alms at the temple",
    "the begum's bath",
    "expectation",
    "disappointing news",
    "lady going for pooja",
    "the coquette",
    "lady in the moonlight",
    "rishi kanya",
    "girl in sage kanwa's hermitage",
}

# ── Subject keywords ──────────────────────────────────────────────────
MYTHOLOGY_KW = [
    # Hindu deities
    "krishna", "radha", "vishnu", "shiva", "parvati", "ganesha", "ganesh",
    "lakshmi", "saraswati", "durga", "kali", "murugan", "subramanya",
    "shanmukha", "hanuman", "rama", "sita", "lakshmana", "ravana",
    # Epic characters
    "shakuntala", "damayanti", "nala", "draupadi", "arjuna", "bhima",
    "pandava", "duryodhana", "bhishma", "drona", "karna",
    "harishchandra", "savitri", "satyavan", "menaka", "vishwamitra",
    "vishvamitra", "urvashi", "pururavas", "mohini", "dushyanta",
    "keechaka", "sairandhri", "jatayu", "dashavatara",
    # Mythological concepts
    "mahabharata", "ramayana", "mythology", "mythological",
    "bhumipravesh", "avatar", "avatara", "deva", "devi",
    "ganga", "shantanu", "subhadra", "meghanada",
    "parashurama", "parashuram", "dattatreya", "markandeya",
    "bhasmasura", "kaliya", "varaha", "kurma", "vamana",
    "matsya", "narasimha",
    # Religious figures
    "meerabai", "meera", "dhruv", "prahlad",
    # General mythology terms
    "swan messenger", "hansa", "vanavasa", "bharat milap",
    "rishi kanya", "sage kanwa", "hermitage",
    "triplets", "panchakanya",
    "ahalya", "tilottama", "kadambari",
    "usha", "chitralekha",
]

PORTRAIT_KW = [
    "portrait", "maharani", "maharaja", "queen", "king", "princess",
    "rani", "raja", "nobleman", "durbar", "lord ampthill",
    "mrs.", "lady", "nair lady", "malabar", "malayali",
    "maharashtrian", "parsee", "beauty", "belle",
    "village belle", "milkmaid", "water carrier",
    "lady adorning", "lady with", "lady in", "lady going",
    "lady juggler", "lady playing", "lady resting",
    "woman holding", "woman with",
    "girl", "begum", "coquette", "bride", "decking",
    "expectation", "disappointing news", "there comes papa",
    "sleeping beauty", "moon light", "moonlight",
    "gypsies", "musicians", "galaxy of musicians",
    "giving alms", "pooja", "suckling", "mother",
    "jewels", "mirror", "fan", "fruit",
    "chimanbai", "tharabai", "subbamma",
]

LANDSCAPE_KW = [
    "landscape", "palace", "udaipur", "fair",
]

# Portrait-only overrides: if these match, always classify as portrait
# even if mythology keywords also match
PORTRAIT_OVERRIDE = [
    "nair lady adorning her hair",
    "malabar beauty",
    "malayali lady",
    "maharashtrian beauty",
    "village belle",
    "the milkmaid",
    "the begum's bath",
    "the coquette",
    "lady with a mirror",
    "lady in the moonlight",
    "lady going for pooja",
    "lady giving alms",
    "expectation",
    "disappointing news",
    "there comes papa",
    "galaxy of musicians",
    "sleeping beauty",
    "lady juggler",
    "lady playing",
    "water carrier",
    "gypsies",
    "the parsee lady",
    "the maharashtrian lady",
    "lady with jewels",
    "decking the bride",
    "the suckling child",
    "woman holding a fan",
    "woman holding a fruit",
    "portrait of a lady",
    "lady resting on the pillow",
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
    if year < 1880:
        return "early"
    if year <= 1900:
        return "mature"
    return "late"


def assign_subject(title: str) -> str:
    tl = title.lower()

    # Check portrait overrides first
    for kw in PORTRAIT_OVERRIDE:
        if kw in tl:
            return "portrait"

    # Check landscape
    for kw in LANDSCAPE_KW:
        if kw in tl:
            return "landscape"

    # Check mythology
    for kw in MYTHOLOGY_KW:
        if kw in tl:
            return "mythology"

    # Check portrait
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
