#!/usr/bin/env python3
"""
Enrich utamaro/catalog.json with derived fields:
  era     -> "early" (pre-1790) | "mature" (1790-1800) | "late" (post-1800)
  subject -> "bijin" | "nature" | "erotica" | "other"
  famous  -> bool

Reads/writes utamaro/catalog.json in place.
Uses title-keyword heuristics for classification.
"""

import json
import os
import re

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "catalog.json",
)

# -- Known famous works (normalized lowercase) --
FAMOUS_TITLES = {
    "three beauties of the present day",
    "toji san bijin",
    "three beauties",
    "beauty looking back",
    "ase o fuku onna",
    "woman wiping sweat",
    "fukaku shinobu koi",
    "deeply hidden love",
    "pensive love",
    "love that rarely meets",
    "revealed love",
    "utamakura",
    "poem of the pillow",
    "ten physiognomic types of women",
    "ten studies in female physiognomy",
    "ten learned studies of women",
    "ten types",
    "coquettish type",
    "woman with a comb",
    "kushi",
    "hairdresser",
    "kamiyui",
    "needlework",
    "hari shigoto",
    "hari-shigoto",
    "mother and child",
    "yamauba and kintaro",
    "yamauba",
    "kintaro",
    "five shades of ink in the northern quarter",
    "hokkoku goshiki zumi",
    "hokkoku goshiki-zumi",
    "snow moon and flowers of the green houses",
    "shinagawa no tsuki",
    "yoshiwara no hana",
    "fukagawa no yuki",
    "moonlight revelry at dozo sagami",
    "anthology of poems the love section",
    "kasen koi no bu",
    "twelve hours of the green houses",
    "seiro junitoki",
    "seiro junitoki",
    "renowned beauties from the six best houses",
    "komei bijin rokkasen",
    "flourishing beauties of the present day",
    "array of supreme beauties of the present day",
    "an array of passionate lovers",
    "naniwaya o kita",
    "naniwaya okita",
    "takashima ohisa",
    "two beauties with bamboo",
    "sugatami shichinin kesho",
    "seven women applying make up",
    "courtesan ichikawa",
    "courtesan hanaogi",
    "hinakoto the courtesan",
    "two geishas and a tipsy client",
    "couple with a standing screen",
    "women playing with the mirror",
    "women making dresses",
    "bathing in cold water",
    "gin sekai",
    "the silver world",
    "ehon mushi erami",
    "picture book of selected insects",
    "cherry blossom viewing",
    "young lady blowing on a poppin",
    "girl blowing a glass toy",
    "musashino",
    "woman drinking wine",
}

# -- Japanese bijin-related terms for classification --
# Many titles are in romanized Japanese; these terms indicate bijin-ga prints
BIJIN_JAPANESE_KW = [
    "fujin",      # woman/women
    "musume",     # young woman/daughter
    "joryu",      # female
    "bijin",      # beautiful person
    "yujo",       # courtesan
    "oiran",      # high-ranking courtesan
    "tayuu",      # highest courtesan
    "geigi",      # geisha
    "tomari",     # lodging (pleasure quarter context)
    "seiro",      # green house / pleasure house
    "danjo",      # man and woman
    "kesho",      # make-up/cosmetics
    "sugata",     # figure/appearance
    "ninso",      # physiognomy
    "sogaku",     # physiognomy study
    "kasumi-ori", # fabric/weaving (women's work)
    "rokkasen",   # six immortal poets (beauty series)
    "goshiki",    # five colors/shades
    "komei",      # renowned
    "hana ",      # flower (in beauty context)
]

# -- Subject keywords --
BIJIN_KW = [
    "beauty", "beauties", "bijin", "woman", "women", "courtesan",
    "geisha", "girl", "lady", "female", "portrait", "physiognomy",
    "physiognomic", "hairdresser", "needlework", "handicraft",
    "mirror", "comb", "bathing", "dressing", "make-up", "makeup",
    "kesho", "kamiyui", "hari-shigoto", "mother", "prostitute",
    "oiran", "kimono", "lovers", "love", "okita", "ohisa",
    "hanaogi", "ichikawa", "hinakoto", "karagoto", "shizuuta",
    "yamauba", "kintaro", "fashion", "femme", "seated",
    "standing", "ritratt", "cortigian", "donne", "deux femmes",
    "couple", "dancer", "dancing", "party", "revelry",
    "sundial", "elegance", "morning", "stili femminili",
    "guida", "tipsy", "client", "costume", "poppin",
    "renown", "drying clothes", "sashimi", "fortune",
    "niwaka", "rice plant",
] + BIJIN_JAPANESE_KW

NATURE_KW = [
    "insect", "bird", "flower", "plant", "shell", "fish",
    "butterfly", "dragonfly", "crane", "sparrow", "owl",
    "quail", "wisteria", "cherry", "plum", "pine", "bamboo",
    "nature", "ehon mushi", "mushi erami", "snow", "moon",
    "cat", "dog", "animal", "cicada", "firefly", "frog",
    "goldfish", "carp", "lotus", "chrysanthemum",
    "vink", "specht", "duif",  # Dutch bird names (Rijksmuseum)
    "bloem", "vlinder",        # Dutch: flower, butterfly
]

EROTICA_KW = [
    "shunga", "erotica", "erotic", "utamakura",
    "pillow", "lubricat", "sexual", "embrace",
]


def parse_year(date_str: str):
    """Extract the first 4-digit year from a date string."""
    if not date_str:
        return None
    m = re.search(r"\d{4}", date_str)
    if m:
        year = int(m.group())
        # Sanity check: Utamaro worked c.1775-1806
        if 1750 <= year <= 1810:
            return year
    return None


def try_extract_date(entry: dict) -> str:
    """Try to extract a date from the title or filename if no date field exists."""
    if entry.get("date"):
        return entry["date"]

    # Check title for embedded dates like "(1793)" or "1801-04"
    title = entry.get("title", "")
    m = re.search(r'\((\d{4}(?:\s*[-\u2013]\s*\d{2,4})?)\)', title)
    if m:
        return m.group(1)
    m = re.search(r'(\d{4}(?:\s*[-\u2013]\s*\d{2,4})?)', title)
    if m:
        year = int(m.group(1)[:4])
        if 1750 <= year <= 1810:
            return m.group(1)

    # Check commons_filename
    fn = entry.get("commons_filename", "")
    m = re.search(r'(\d{4})', fn)
    if m:
        year = int(m.group(1))
        if 1750 <= year <= 1810:
            return m.group(1)

    return ""


def assign_era(year) -> str:
    if year is None:
        return "unknown"
    if year < 1790:
        return "early"
    if year <= 1800:
        return "mature"
    return "late"


def assign_subject(title: str) -> str:
    tl = title.lower()

    # Priority: erotica > nature > bijin > other
    for kw in EROTICA_KW:
        if kw in tl:
            return "erotica"
    for kw in NATURE_KW:
        if kw in tl:
            return "nature"
    for kw in BIJIN_KW:
        if kw in tl:
            return "bijin"
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
        # Try to fill in missing dates from title/filename
        date_str = try_extract_date(entry)
        if date_str and not entry.get("date"):
            entry["date"] = date_str
        year = parse_year(date_str)

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
