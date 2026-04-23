#!/usr/bin/env python3
"""
Scrape the Wikipedia "List of paintings by Paul Cézanne" page and extract
structured artwork data from the 4 chronological wikitable sections:

  * Paintings 1859–1870 (early)
  * Paintings 1871–1878 (impressionist)
  * Paintings 1878–1890 (constructive)
  * Paintings 1890–1906 (late)

Column schema (6 columns):
  0  Image      — <figure>/<a>/<img>
  1  Title      — usually <i>Title</i>
  2  Year       — e.g. "c. 1859", "1872-73", "1890"
  3  Dimensions — e.g. "65 x 81 cm"
  4  Location   — museum name / "Private collection" / etc.
  5  Cat. No.   — "V 3<br>R 1<br>FWN 560"  (Venturi / Rewald / Feilchenfeldt-
                 Nash-Warman). Any of the three may be missing.

Outputs: cezanne/wiki_works_raw.json
"""

import json
import os
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser

API_URL = "https://en.wikipedia.org/w/api.php"
PAGE_TITLE = "List of paintings by Paul Cézanne"

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(os.path.dirname(HERE), "wiki_works_raw.json")

USER_AGENT = "open-museum/1.0 cezanne-build"


def fetch_page_html(title: str) -> str:
    params = urllib.parse.urlencode({
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json",
    })
    url = f"{API_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    return data["parse"]["text"]["*"]


class TableExtractor(HTMLParser):
    """Extract rows from wikitable sections, remembering the nearest h2/h3
    heading as the section label."""

    def __init__(self):
        super().__init__()
        self.tables = []
        self.current_table = None
        self.current_row = None
        self.current_cell = None
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.cell_tag = None
        self.current_section = ""
        self.in_heading = False
        self.heading_text = ""
        self.cell_links = []
        self.cell_images = []
        self.cell_italic = []
        self.in_italic = False
        self.italic_buf = ""
        self.in_sup = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag in ("h2", "h3"):
            self.in_heading = True
            self.heading_text = ""
            return

        if tag == "sup":
            self.in_sup = True
            return

        if tag == "table" and "wikitable" in attrs_dict.get("class", ""):
            self.in_table = True
            self.current_table = {"section": self.current_section, "rows": [], "headers": []}
            return

        if not self.in_table:
            return

        if tag == "tr":
            self.in_row = True
            self.current_row = []
            return

        if tag in ("td", "th") and self.in_row:
            self.in_cell = True
            self.cell_tag = tag
            self.current_cell = ""
            self.cell_links = []
            self.cell_images = []
            self.cell_italic = []
            self.in_italic = False
            self.italic_buf = ""
            return

        if self.in_cell and tag == "a":
            href = attrs_dict.get("href", "")
            if href and not href.startswith("#"):
                self.cell_links.append(href)

        if self.in_cell and tag == "img":
            src = attrs_dict.get("src", "")
            if src:
                self.cell_images.append(src)

        if self.in_cell and tag == "i":
            self.in_italic = True
            self.italic_buf = ""

        if self.in_cell and tag == "br":
            self.current_cell += " | "

    def handle_endtag(self, tag):
        if tag in ("h2", "h3") and self.in_heading:
            self.in_heading = False
            self.current_section = re.sub(r"\[edit\]$", "", self.heading_text.strip()).strip()
            return

        if tag == "sup":
            self.in_sup = False
            return

        if tag == "table" and self.in_table:
            self.in_table = False
            if self.current_table and self.current_table["rows"]:
                self.tables.append(self.current_table)
            self.current_table = None
            return

        if not self.in_table:
            return

        if tag == "tr" and self.in_row:
            self.in_row = False
            if self.current_row and self.current_table is not None:
                if self.cell_tag == "th" and not self.current_table["headers"]:
                    self.current_table["headers"] = [c["text"] for c in self.current_row]
                else:
                    self.current_table["rows"].append(self.current_row)
            self.current_row = None
            return

        if tag in ("td", "th") and self.in_cell:
            self.in_cell = False
            cell = {
                "text": self.current_cell.strip(),
                "links": self.cell_links,
                "images": self.cell_images,
                "italics": [s.strip() for s in self.cell_italic if s.strip()],
            }
            if self.current_row is not None:
                self.current_row.append(cell)
            self.current_cell = None
            return

        if self.in_cell and tag == "i" and self.in_italic:
            self.in_italic = False
            if self.italic_buf.strip():
                self.cell_italic.append(self.italic_buf)
            self.italic_buf = ""

    def handle_data(self, data):
        if self.in_heading:
            self.heading_text += data
        if self.in_cell and not self.in_sup:
            clean = data.replace("\xa0", " ").replace("\n", " ")
            self.current_cell += clean
            if self.in_italic:
                self.italic_buf += clean


# ─────────────────────────────────────────────────────────────────────
def extract_commons_filename(img_src: str) -> str:
    m = re.search(r"/commons/thumb/[0-9a-f]/[0-9a-f]{2}/([^/]+)/\d+px-", img_src)
    if m:
        return urllib.parse.unquote(m.group(1))
    m = re.search(r"/commons/[0-9a-f]/[0-9a-f]{2}/([^/]+)$", img_src)
    if m:
        return urllib.parse.unquote(m.group(1))
    return ""


def extract_title_wiki_link(links: list) -> str:
    """Pick the first /wiki/... link that isn't File: — used as a per-work
    Wikipedia article when one exists (most Cézanne rows won't have one)."""
    for link in links:
        if link.startswith("/wiki/") and not link.startswith("/wiki/File:"):
            return f"https://en.wikipedia.org{link}"
    return ""


CAT_RE = re.compile(
    r"(?:^|\W)(V|R|FWN)\s*([A-Za-z0-9\-]+(?:\s*[-–/]\s*[A-Za-z0-9]+)?)",
    re.IGNORECASE,
)


def parse_catalog_numbers(text: str) -> dict:
    """Extract the three catalogue-raisonné numbers from a Cat. No. cell.
    Venturi (V), Rewald (R), and Feilchenfeldt-Nash-Warman (FWN).

    Cell text looks like "V 3 | R 1 | FWN 560" after <br> → " | ". Any of
    the three codes may be absent.
    """
    result = {}
    if not text:
        return result
    # Tokenise by pipes and newlines to avoid cross-token bleed
    for chunk in re.split(r"\s*\|\s*|\n", text):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.match(r"(V|R|FWN)\s*(.+)$", chunk, re.I)
        if m:
            code = m.group(1).upper()
            value = m.group(2).strip().rstrip(",;:")
            if code == "V":
                result["v_number"] = f"V.{value}"
            elif code == "R":
                result["r_number"] = f"R.{value}"
            elif code == "FWN":
                result["fwn_number"] = f"FWN.{value}"
    # raw copy for debugging
    result["raw_cat_no"] = text
    return result


def assign_era(section: str) -> str:
    s = section.lower()
    if "1859" in s:
        return "early"
    if "1871" in s:
        return "impressionist"
    if "1878" in s:
        return "constructive"
    if "1890" in s:
        return "late"
    return "unknown"


SERIES_KEYWORDS = {
    "mont-sainte-victoire": ["mont sainte-victoire", "mont ste-victoire", "sainte-victoire", "saint-victoire"],
    "bathers": ["bathers", "baigneur", "baigneuse", "baigneurs", "baigneuses"],
    "card-players": ["card player", "card-player", "card players", "cardplayer", "cardplayers", "players at cards"],
    "apples": ["apples", "basket of apples", "still life with apples"],
    "mount-marseille": ["l'estaque", "gulf of marseille", "gulf of marseilles"],
    "harlequin-pierrot": ["harlequin", "pierrot", "mardi gras"],
    "self-portrait": ["self-portrait", "self portrait"],
}


def detect_series(title: str) -> str:
    t = (title or "").lower()
    for series, keys in SERIES_KEYWORDS.items():
        for k in keys:
            if k in t:
                return series
    return ""


SUBJECT_KEYWORDS = {
    "mountain": ["mont sainte-victoire", "mont ste-victoire", "sainte-victoire", "saint-victoire", "mountain"],
    "bather": ["bather", "baigneur", "baigneuse"],
    "cardplayer": ["card player", "cardplayer", "card-player", "players at cards"],
    "still_life": [
        "still life", "still-life", "apples", "fruit", "compotier", "pomme",
        "pears", "vase of", "vase with", "bowl of", "bouquet", "flowers",
        "skull", "kitchen table", "onions", "peppermint bottle",
    ],
    "portrait": [
        "portrait", "self-portrait", "self portrait", "madame cézanne",
        "madame cezanne", "the artist's wife", "harlequin", "pierrot",
        "uncle dominique", "boy in a red", "peasant", "smoker",
    ],
    "landscape": [
        "landscape", "view of", "road", "river", "bridge", "pond", "lake",
        "house", "houses", "village", "rocks", "rochers", "quarry", "bibémus",
        "château", "chateau", "forest", "wood", "fields", "chestnut", "pine",
        "tree", "valley", "gardanne", "estaque", "auvers", "aix", "provence",
    ],
}


def detect_subject(title: str) -> str:
    t = (title or "").lower()
    for subj, keys in SUBJECT_KEYWORDS.items():
        for k in keys:
            if k in t:
                return subj
    return "other"


# ─────────────────────────────────────────────────────────────────────
def parse_date_triplet(raw: str):
    """Return (date_display, year_start, year_end, circa).

    Handles:
      "c. 1859"        → (raw, 1859, 1859, True)
      "1872-73"        → (raw, 1872, 1873, False)
      "1877-1879"      → (raw, 1877, 1879, False)
      "c. 1890-92"     → (raw, 1890, 1892, True)
      "1880"           → (raw, 1880, 1880, False)
      ""               → (raw, None, None, False)
    """
    if not raw:
        return raw, None, None, False
    s = raw.strip()
    circa = bool(re.search(r"\bc\.|\bcirca\b|\bca\.", s, re.I))
    s_clean = re.sub(r"\bc\.\s*|\bcirca\s*|\bca\.\s*", "", s, flags=re.I)

    # "1872-73" or "1872-1873" or "1872–73"
    m = re.search(r"(1[5-9]\d\d|20\d\d)\s*[–\-]\s*(\d{2,4})(?!\d)", s_clean)
    if m:
        start = int(m.group(1))
        end_raw = m.group(2)
        if len(end_raw) == 2:
            end_full = (start // 100) * 100 + int(end_raw)
            if end_full < start:
                end_full += 100
        else:
            end_full = int(end_raw)
        return s, start, end_full, circa

    # Single 4-digit year
    m = re.search(r"(1[5-9]\d\d|20\d\d)", s_clean)
    if m:
        y = int(m.group(1))
        return s, y, y, circa

    return s, None, None, circa


# ─────────────────────────────────────────────────────────────────────
def process_table(table: dict) -> list:
    works = []
    section = table["section"]
    era = assign_era(section)

    for row in table["rows"]:
        if len(row) < 6:
            continue
        img_cell, title_cell, year_cell, dim_cell, loc_cell, cat_cell = row[:6]

        # Title: prefer italic text, fall back to plain text
        title = ""
        if title_cell.get("italics"):
            title = title_cell["italics"][0]
        else:
            title = title_cell["text"]
        title = title.strip(" .,-–—")

        if not title:
            continue

        work = {
            "section": section,
            "era": era,
            "title": title,
        }

        # Optional per-work Wikipedia article (rare for Cézanne)
        wiki_link = extract_title_wiki_link(title_cell.get("links", []))
        if wiki_link:
            work["wikipedia_url"] = wiki_link

        # Image
        images = img_cell.get("images", [])
        if images:
            fname = extract_commons_filename(images[0])
            if fname:
                work["commons_filename"] = fname

        # Date triplet
        raw_date = year_cell["text"].strip()
        date_disp, y_s, y_e, circa = parse_date_triplet(raw_date)
        work["date"] = date_disp
        work["year_start"] = y_s
        work["year_end"] = y_e
        work["circa"] = circa

        # Dimensions
        work["dimensions"] = dim_cell["text"].strip()

        # Location
        work["current_location"] = loc_cell["text"].strip()

        # Catalogue numbers
        cat = parse_catalog_numbers(cat_cell["text"])
        for k, v in cat.items():
            if k != "raw_cat_no" or v:
                work[k] = v

        # Series & subject (from title)
        series = detect_series(title)
        if series:
            work["series"] = series
        work["subject"] = detect_subject(title)

        # Clean empty strings
        work = {k: v for k, v in work.items() if v not in ("", None)}

        works.append(work)

    return works


def main():
    print(f"Fetching Wikipedia page: {PAGE_TITLE}")
    html = fetch_page_html(PAGE_TITLE)
    print(f"Got {len(html):,} bytes of HTML")

    extractor = TableExtractor()
    extractor.feed(html)
    print(f"Found {len(extractor.tables)} wikitables")

    all_works = []
    for tbl in extractor.tables:
        works = process_table(tbl)
        print(f"  Section {tbl['section']!r}: {len(works)} works")
        all_works.extend(works)

    print(f"\nTotal works extracted: {len(all_works)}")

    with_image = sum(1 for w in all_works if w.get("commons_filename"))
    with_fwn = sum(1 for w in all_works if w.get("fwn_number"))
    with_v = sum(1 for w in all_works if w.get("v_number"))
    with_r = sum(1 for w in all_works if w.get("r_number"))
    with_date = sum(1 for w in all_works if w.get("year_start"))
    print(f"With commons_filename: {with_image}")
    print(f"With V/R/FWN: {with_v}/{with_r}/{with_fwn}")
    print(f"With year_start:       {with_date}")

    from collections import Counter
    print(f"\nSubjects: {Counter(w.get('subject', 'other') for w in all_works)}")
    print(f"Series:   {Counter(w.get('series', '') for w in all_works if w.get('series'))}")
    print(f"Eras:     {Counter(w.get('era', 'unknown') for w in all_works)}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
