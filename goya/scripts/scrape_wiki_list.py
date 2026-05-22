#!/usr/bin/env python3
"""
Scrape the Wikipedia "List of works by Francisco Goya" page and extract
structured artwork data from paintings and prints tables.

Paintings sections map to eras:
  - Paintings (1763–1774) -> early
  - Paintings (1775–1792) -> court
  - Paintings (1793–1807) -> crisis
  - Paintings (1808–1818) -> war
  - Paintings (1819–1828) -> late

Print sections map to series:
  - Prints (Los Caprichos) -> caprichos (1797-1799)
  - Prints (Disasters of War) -> disasters_of_war (1810-1820)
  - Prints (La Tauromaquia) -> tauromaquia (1815-1816)
  - Prints (Los disparates) -> disparates (1815-1824)
  - Prints (Bulls of Bordeaux) -> bulls_of_bordeaux (1825)
  - Prints (Other prints) -> other_prints

Outputs: goya/wiki_works_raw.json
"""

import json
import os
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser

API_URL = "https://en.wikipedia.org/w/api.php"
PAGE_TITLE = "List of works by Francisco Goya"

HERE = os.path.dirname(os.path.abspath(__file__))
COLL_DIR = os.path.dirname(HERE)
OUTPUT_PATH = os.path.join(COLL_DIR, "wiki_works_raw.json")

USER_AGENT = "open-museum/1.0 goya-build (https://github.com/nafSadh/open-museum)"


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
        data = json.loads(resp.read().decode("utf-8"))
    return data["parse"]["text"]["*"]


class TableExtractor(HTMLParser):
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


def extract_commons_filename(links: list, images: list) -> str:
    # First look at links for File:...
    for link in links:
        if link.startswith("/wiki/File:"):
            fn = link[11:]
            return urllib.parse.unquote(fn).replace(" ", "_")

    # Fallback: check img src
    for src in images:
        m = re.search(r"/commons/thumb/[0-9a-f]/[0-9a-f]{2}/([^/]+)/\d+px-", src)
        if m:
            return urllib.parse.unquote(m.group(1)).replace(" ", "_")
        m = re.search(r"/commons/[0-9a-f]/[0-9a-f]{2}/([^/]+)$", src)
        if m:
            return urllib.parse.unquote(m.group(1)).replace(" ", "_")
    return ""


def extract_title_wiki_link(links: list) -> str:
    for link in links:
        if link.startswith("/wiki/") and not link.startswith("/wiki/File:"):
            return f"https://en.wikipedia.org{link}"
    return ""


def parse_date_triplet(raw: str):
    """
    Return (date_display, year_start, year_end, circa).
    Handles:
      "c. 1771"        → ("c. 1771", 1771, 1771, True)
      "1786–1787"      → ("1786–1787", 1786, 1787, False)
      "1819–1823"      → ("1819–1823", 1819, 1823, False)
      "1820"           → ("1820", 1820, 1820, False)
      ""               → ("", None, None, False)
    """
    if not raw:
        return "", None, None, False
    s = raw.strip()
    circa = bool(re.search(r"\bc\.|\bcirca\b|\bca\.", s, re.I))
    s_clean = re.sub(r"\bc\.\s*|\bcirca\s*|\bca\.\s*", "", s, flags=re.I)

    # Range like "1786-87" or "1786-1787" or "1786–87"
    m = re.search(r"(1[789]\d\d)\s*[–\-]\s*(\d{2,4})(?!\d)", s_clean)
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

    # Single year
    m = re.search(r"(1[789]\d\d)", s_clean)
    if m:
        y = int(m.group(1))
        return s, y, y, circa

    return s, None, None, circa


def get_column_mapping(headers: list[str]) -> dict:
    """Map headers to logical fields: image_title, title, date, location, size, method."""
    mapping = {}
    for idx, h in enumerate(headers):
        hl = h.lower().replace(" ", "").replace("'", "").replace("’", "").replace("|", "")
        if "imagetitle" in hl or ("image" in hl and "title" in hl):
            mapping["image_title"] = idx
        elif "image" in hl:
            mapping["image"] = idx
        elif "title" in hl:
            mapping["title"] = idx
        elif "date" in hl or "year" in hl:
            mapping["date"] = idx
        elif "location" in hl:
            mapping["location"] = idx
        elif "size" in hl or "dimensions" in hl:
            mapping["size"] = idx
        elif "method" in hl:
            mapping["method"] = idx
    return mapping


def clean_title(title: str) -> str:
    t = title.strip(" .,-–—\"'“”")
    # remove trailing [1] or [2] citations
    t = re.sub(r"\[\d+\]$", "", t)
    return t.strip()


def assign_paintings_era(section: str) -> str:
    s = section.lower()
    if "1763" in s:
        return "early"
    if "1775" in s:
        return "court"
    if "1793" in s:
        return "crisis"
    if "1808" in s:
        return "war"
    if "1819" in s:
        return "late"
    return "unknown"


def main():
    print(f"Fetching Wikipedia page: {PAGE_TITLE}")
    html = fetch_page_html(PAGE_TITLE)
    print(f"Got {len(html):,} bytes of HTML")

    extractor = TableExtractor()
    extractor.feed(html)
    print(f"Found {len(extractor.tables)} wikitables")

    all_works = []

    for tbl in extractor.tables:
        section = tbl["section"]
        headers = tbl["headers"]
        rows = tbl["rows"]

        print(f"\nProcessing section: {section!r}")
        print(f"Headers: {headers}")

        col_map = get_column_mapping(headers)
        print(f"Column Mapping: {col_map}")

        # Check if this is a paintings section or print section
        is_paintings = "Paintings" in section
        is_prints = "Prints" in section

        if not is_paintings and not is_prints:
            print(f"Skipping non-art section: {section}")
            continue

        item_type = "painting" if is_paintings else "print"
        era = assign_paintings_era(section) if is_paintings else ""

        # Map print series
        series = ""
        series_date_triplet = (None, None, None, False)
        if is_prints:
            if "Caprichos" in section:
                series = "caprichos"
                series_date_triplet = ("1797–1799", 1797, 1799, False)
            elif "Disasters of War" in section or "Desastres" in section:
                series = "disasters_of_war"
                series_date_triplet = ("1810–1820", 1810, 1820, False)
            elif "Tauromaquia" in section:
                series = "tauromaquia"
                series_date_triplet = ("1815–1816", 1815, 1816, False)
            elif "disparates" in section:
                series = "disparates"
                series_date_triplet = ("1815–1824", 1815, 1824, False)
            elif "Bulls of Bordeaux" in section:
                series = "bulls_of_bordeaux"
                series_date_triplet = ("1825", 1825, 1825, False)
            else:
                series = "other_prints"

        section_count = 0
        for r_idx, r in enumerate(rows):
            # Safe column check
            cell_count = len(r)
            if cell_count == 0:
                continue

            # Determine title & image sources
            title = ""
            commons_fn = ""
            wiki_url = ""

            # 1. Image and Title extraction
            if "image_title" in col_map:
                idx = col_map["image_title"]
                if idx < cell_count:
                    cell = r[idx]
                    # Title is the plain text of the cell (often inside figcaption)
                    # Let's clean it up
                    title = clean_title(cell["text"])
                    if not title and cell.get("italics"):
                        title = clean_title(cell["italics"][0])

                    # Extract file
                    commons_fn = extract_commons_filename(cell.get("links", []), cell.get("images", []))
                    # Extract wikipedia link for the artwork
                    wiki_url = extract_title_wiki_link(cell.get("links", []))
            else:
                # Separate Image and Title
                if "image" in col_map:
                    idx = col_map["image"]
                    if idx < cell_count:
                        cell = r[idx]
                        commons_fn = extract_commons_filename(cell.get("links", []), cell.get("images", []))
                if "title" in col_map:
                    idx = col_map["title"]
                    if idx < cell_count:
                        cell = r[idx]
                        title = clean_title(cell["text"])
                        if not title and cell.get("italics"):
                            title = clean_title(cell["italics"][0])
                        wiki_url = extract_title_wiki_link(cell.get("links", []))

            if not title:
                # If no title extracted, skip or try to fallback to any text
                continue

            work = {
                "type": item_type,
                "title": title,
                "section": section,
            }

            if era:
                work["era"] = era
            if series:
                work["series"] = series

            if commons_fn:
                work["commons_filename"] = commons_fn
            if wiki_url:
                work["wikipedia_url"] = wiki_url

            # 2. Date / Year extraction
            if "date" in col_map:
                idx = col_map["date"]
                if idx < cell_count:
                    raw_date = r[idx]["text"].strip()
                    d_disp, y_start, y_end, circa = parse_date_triplet(raw_date)
                    work["date"] = d_disp
                    work["year_start"] = y_start
                    work["year_end"] = y_end
                    work["circa"] = circa
            elif series_date_triplet[0]:
                work["date"] = series_date_triplet[0]
                work["year_start"] = series_date_triplet[1]
                work["year_end"] = series_date_triplet[2]
                work["circa"] = series_date_triplet[3]

            # 3. Location extraction
            if "location" in col_map:
                idx = col_map["location"]
                if idx < cell_count:
                    work["current_location"] = r[idx]["text"].strip()

            # 4. Dimensions / Size extraction
            if "size" in col_map:
                idx = col_map["size"]
                if idx < cell_count:
                    work["dimensions"] = r[idx]["text"].strip()

            # 5. Method extraction (print medium)
            if "method" in col_map:
                idx = col_map["method"]
                if idx < cell_count:
                    work["medium"] = r[idx]["text"].strip()
            elif is_paintings:
                work["medium"] = "oil on canvas"  # Default for Goya paintings unless specific

            # Clean empty strings and nulls
            work = {k: v for k, v in work.items() if v not in ("", None)}
            all_works.append(work)
            section_count += 1

        print(f"Extracted {section_count} works from section {section!r}")

    print(f"\nTotal Goya works extracted: {len(all_works)}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)
    print(f"Written raw scrape to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
