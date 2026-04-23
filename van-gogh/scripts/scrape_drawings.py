#!/usr/bin/env python3
"""
Scrape the Wikipedia "List of drawings by Vincent van Gogh" page
and extract structured drawing records from the HTML tables.

Adapted from scrape_wiki_list.py. The drawings list uses a 6-column format:
  Image | Title | Date | Current location | Created in | Catalogue No.
(No dimensions column, unlike the paintings table.)

Outputs: van-gogh/wiki_drawings_raw.json
"""

import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser


API_URL = "https://en.wikipedia.org/w/api.php"
PAGE_TITLE = "List of drawings by Vincent van Gogh"
OUTPUT_PATH = "van-gogh/wiki_drawings_raw.json"


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
    req = urllib.request.Request(url, headers={"User-Agent": "open-museum/1.0 vg-drawings"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    return data["parse"]["text"]["*"]


class TableExtractor(HTMLParser):
    """Extract data from wikitable HTML tables, tracking section headings."""

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
    match = re.search(r'/commons/thumb/[0-9a-f]/[0-9a-f]{2}/(.+?)/\d+px-', img_src)
    if match:
        return urllib.parse.unquote(match.group(1))
    match = re.search(r'/commons/[0-9a-f]/[0-9a-f]{2}/(.+?)$', img_src)
    if match:
        return urllib.parse.unquote(match.group(1))
    return ""


def parse_catalog_numbers(text: str) -> dict:
    """Parse F and JH catalog numbers from cell text."""
    result = {}
    # F number — allow optional letter suffix (e.g. F 1654v)
    f_match = re.search(r'F\s*(\d+[a-z]?)', text)
    if f_match:
        result["f_number"] = f"F{f_match.group(1)}"
    jh_match = re.search(r'JH\s*(\d+)', text)
    if jh_match:
        result["jh_number"] = f"JH{jh_match.group(1)}"
    return result


def extract_provenance_url(links: list) -> str:
    """First Wikipedia article link (not a File: link)."""
    for link in links:
        if link.startswith("/wiki/") and not link.startswith("/wiki/File:"):
            return f"https://en.wikipedia.org{link}"
    return ""


def process_table(table: dict) -> list:
    """Convert a raw 6-col drawings table into structured records.

    Columns: [0] Image  [1] Title  [2] Date  [3] Current location  [4] Created in  [5] Catalog
    """
    section = table["section"]
    works = []
    for row in table["rows"]:
        if not row or len(row) < 2:
            continue

        work = {
            "section": section,
            "type": "drawing",
        }

        # [0] Image cell — holds the thumbnail
        img_cell = row[0]
        if img_cell["images"]:
            fname = extract_commons_filename(img_cell["images"][0])
            if fname:
                work["commons_filename"] = fname

        # [1] Title cell — may contain a wikilink to the drawing's article
        if len(row) > 1:
            title_cell = row[1]
            title_text = title_cell["text"].strip()
            # Drawings page sometimes wraps titles in <i>…</i>; HTMLParser has already
            # inlined the text content, so we get plain text. Trim trailing whitespace.
            work["title"] = title_text
            prov = extract_provenance_url(title_cell["links"])
            if prov:
                work["provenance_url"] = prov

        # [2] Date
        if len(row) > 2:
            work["date"] = row[2]["text"].strip()

        # [3] Current location
        if len(row) > 3:
            work["current_location"] = row[3]["text"].strip()

        # [4] Created in
        if len(row) > 4:
            work["created_in"] = row[4]["text"].strip()

        # [5] Catalog
        if len(row) > 5:
            work.update(parse_catalog_numbers(row[5]["text"]))

        # Drop empty-string fields to match paintings catalog style
        work = {k: v for k, v in work.items() if v not in (None, "", [])}

        if work.get("title"):
            works.append(work)

    return works


def main():
    print(f"Fetching Wikipedia page: {PAGE_TITLE}")
    html = fetch_page_html(PAGE_TITLE)
    print(f"Got {len(html)} bytes of HTML")

    extractor = TableExtractor()
    extractor.feed(html)
    print(f"Found {len(extractor.tables)} wikitables")

    all_works = []
    for table in extractor.tables:
        works = process_table(table)
        print(f"  Section '{table['section']}': {len(works)} drawings")
        all_works.extend(works)

    print(f"\nTotal drawings extracted: {len(all_works)}")

    with_image = sum(1 for w in all_works if w.get("commons_filename"))
    with_f = sum(1 for w in all_works if w.get("f_number"))
    with_jh = sum(1 for w in all_works if w.get("jh_number"))
    print(f"With Commons image: {with_image}")
    print(f"With F number: {with_f}")
    print(f"With JH number: {with_jh}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
