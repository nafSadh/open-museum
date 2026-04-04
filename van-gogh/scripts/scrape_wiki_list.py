#!/usr/bin/env python3
"""
Scrape the Wikipedia "List of works by Vincent van Gogh" page
and extract structured artwork data from the HTML tables.

Outputs: van-gogh/wiki_works_raw.json
"""

import json
import re
import sys
import urllib.request
import urllib.parse
from html.parser import HTMLParser


API_URL = "https://en.wikipedia.org/w/api.php"
PAGE_TITLE = "List of works by Vincent van Gogh"
OUTPUT_PATH = "van-gogh/wiki_works_raw.json"


def fetch_page_html(title: str) -> str:
    """Fetch parsed HTML of a Wikipedia page via the API."""
    params = urllib.parse.urlencode({
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json",
        "disabletoc": "true",
    })
    url = f"{API_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "open-museum/1.0 (art catalog project)"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    return data["parse"]["text"]["*"]


class TableExtractor(HTMLParser):
    """Extract data from HTML tables in the Wikipedia page."""

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
        self.depth = 0
        self.skip_depth = 0
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
            self.depth += 1
            return

        if tag in ("td", "th"):
            self.in_cell = True
            self.cell_tag = tag
            self.current_cell = ""
            self.cell_links = []
            self.cell_images = []
            return

        if self.in_cell and tag == "a":
            href = attrs_dict.get("href", "")
            if href and not href.startswith("#"):
                self.cell_links.append(href)

        if self.in_cell and tag == "img":
            src = attrs_dict.get("src", "")
            if src:
                self.cell_images.append(src)

        if self.in_cell and tag == "br":
            self.current_cell += " | "

    def handle_endtag(self, tag):
        if tag in ("h2", "h3") and self.in_heading:
            self.in_heading = False
            self.current_section = self.heading_text.strip()
            # Remove [edit] suffix
            self.current_section = re.sub(r'\[edit\]$', '', self.current_section).strip()
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
                    self.current_table["headers"] = [
                        c["text"] for c in self.current_row
                    ]
                else:
                    self.current_table["rows"].append(self.current_row)
            self.current_row = None
            return

        if tag in ("td", "th") and self.in_cell:
            self.in_cell = False
            cell_data = {
                "text": self.current_cell.strip(),
                "links": self.cell_links,
                "images": self.cell_images,
            }
            if self.current_row is not None:
                self.current_row.append(cell_data)
            self.current_cell = None
            return

    def handle_data(self, data):
        if self.in_heading:
            self.heading_text += data
        if self.in_cell and not self.in_sup:
            self.current_cell += data


def extract_commons_filename(img_src: str) -> str:
    """Extract the Commons filename from a thumbnail URL."""
    # Thumbnail URLs look like:
    # //upload.wikimedia.org/wikipedia/commons/thumb/a/ab/File.jpg/120px-File.jpg
    match = re.search(r'/commons/thumb/[0-9a-f]/[0-9a-f]{2}/(.+?)/\d+px-', img_src)
    if match:
        return urllib.parse.unquote(match.group(1))
    # Direct file URLs:
    # //upload.wikimedia.org/wikipedia/commons/a/ab/File.jpg
    match = re.search(r'/commons/[0-9a-f]/[0-9a-f]{2}/(.+?)$', img_src)
    if match:
        return urllib.parse.unquote(match.group(1))
    return ""


def parse_catalog_numbers(text: str) -> dict:
    """Parse F and JH catalog numbers from cell text."""
    result = {}
    # F number
    f_match = re.search(r'F\s*(\d+[a-z]?)', text)
    if f_match:
        result["f_number"] = f"F{f_match.group(1)}"
    # JH number
    jh_match = re.search(r'JH\s*(\d+)', text)
    if jh_match:
        result["jh_number"] = f"JH{jh_match.group(1)}"
    return result


def extract_wikipedia_url(links: list) -> str:
    """Find the first Wikipedia article link from a list of hrefs."""
    for link in links:
        if link.startswith("/wiki/") and not link.startswith("/wiki/File:"):
            return f"https://en.wikipedia.org{link}"
    return ""


def determine_type(section: str) -> str:
    """Determine the artwork type from the section name."""
    s = section.lower()
    if "painting" in s:
        return "painting"
    if "watercolour" in s or "watercolor" in s:
        return "watercolor"
    if "drawing" in s:
        return "drawing"
    if "lithograph" in s:
        return "lithograph"
    if "etching" in s:
        return "etching"
    if "letter sketch" in s:
        return "letter_sketch"
    if "print" in s:
        return "print"
    return "unknown"


def determine_location_created(section: str) -> str:
    """Extract the location from the section title for painting sections."""
    # Sections like "Paintings (Arles)" or "Paintings (Saint-Rémy)"
    match = re.search(r'\(([^)]+)\)', section)
    if match:
        return match.group(1)
    return ""


def process_table(table: dict) -> list:
    """Convert a raw table into structured artwork records."""
    section = table["section"]
    headers = [h.lower().strip() for h in table.get("headers", [])]
    artwork_type = determine_type(section)
    section_location = determine_location_created(section)

    works = []
    for row in table["rows"]:
        if not row:
            continue

        work = {
            "section": section,
            "type": artwork_type,
        }

        # The first cell is always Image/Title
        if len(row) > 0:
            first_cell = row[0]
            work["title"] = first_cell["text"].strip()
            work["wikipedia_url"] = extract_wikipedia_url(first_cell["links"])
            if first_cell["images"]:
                fname = extract_commons_filename(first_cell["images"][0])
                if fname:
                    work["commons_filename"] = fname

        # Map remaining cells based on header count
        num_cols = len(row)

        if num_cols >= 5:
            # Date is typically column 1
            work["date"] = row[1]["text"].strip() if len(row) > 1 else ""

            # Current location is typically column 2
            if len(row) > 2:
                work["current_location"] = row[2]["text"].strip()

            # Determine if we have "Created in" column (6-col variant)
            if num_cols >= 6:
                work["created_in"] = row[3]["text"].strip() if len(row) > 3 else ""
                # Medium/dimensions in col 4
                if len(row) > 4:
                    md_text = row[4]["text"]
                    parts = [p.strip() for p in md_text.split("|")]
                    if len(parts) >= 2:
                        work["medium"] = parts[0]
                        work["dimensions"] = parts[1]
                    else:
                        work["medium_dimensions"] = md_text.strip()
                # Catalog in col 5
                if len(row) > 5:
                    work.update(parse_catalog_numbers(row[5]["text"]))
            elif num_cols == 5:
                # Could be 5-col painting (no Created in) or 5-col watercolor (no Medium)
                if "painting" in section.lower():
                    # 5-col painting: Image/Title | Date | Location | Medium,Dim | Catalog
                    if len(row) > 3:
                        md_text = row[3]["text"]
                        parts = [p.strip() for p in md_text.split("|")]
                        if len(parts) >= 2:
                            work["medium"] = parts[0]
                            work["dimensions"] = parts[1]
                        else:
                            work["medium_dimensions"] = md_text.strip()
                    if len(row) > 4:
                        work.update(parse_catalog_numbers(row[4]["text"]))
                else:
                    # 5-col non-painting: Image/Title | Date | Location | Created in | Catalog
                    work["created_in"] = row[3]["text"].strip() if len(row) > 3 else ""
                    if len(row) > 4:
                        work.update(parse_catalog_numbers(row[4]["text"]))

        elif num_cols == 4:
            work["date"] = row[1]["text"].strip() if len(row) > 1 else ""
            work["current_location"] = row[2]["text"].strip() if len(row) > 2 else ""
            if len(row) > 3:
                work.update(parse_catalog_numbers(row[3]["text"]))

        # Fill in section-implied location if not set
        if section_location and "created_in" not in work:
            work["created_in"] = section_location

        # Clean up empty strings
        work = {k: v for k, v in work.items() if v}

        if work.get("title"):
            works.append(work)

    return works


def main():
    print(f"Fetching Wikipedia page: {PAGE_TITLE}")
    html = fetch_page_html(PAGE_TITLE)
    print(f"Got {len(html)} bytes of HTML")

    print("Parsing tables...")
    extractor = TableExtractor()
    extractor.feed(html)
    print(f"Found {len(extractor.tables)} tables")

    all_works = []
    for table in extractor.tables:
        works = process_table(table)
        print(f"  Section '{table['section']}': {len(works)} works (headers: {table.get('headers', [])})")
        all_works.extend(works)

    print(f"\nTotal works extracted: {len(all_works)}")

    # Summary stats
    types = {}
    with_image = 0
    with_f = 0
    with_jh = 0
    for w in all_works:
        t = w.get("type", "unknown")
        types[t] = types.get(t, 0) + 1
        if "commons_filename" in w:
            with_image += 1
        if "f_number" in w:
            with_f += 1
        if "jh_number" in w:
            with_jh += 1

    print(f"By type: {json.dumps(types, indent=2)}")
    print(f"With Commons image: {with_image}")
    print(f"With F number: {with_f}")
    print(f"With JH number: {with_jh}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
