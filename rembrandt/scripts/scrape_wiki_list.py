#!/usr/bin/env python3
"""
Scrape Wikipedia list pages for Rembrandt:
  - List of paintings by Rembrandt  (cols: Image, Title, Year, Technique, Dimensions, Gallery, Number, Commentary)
  - List of etchings by Rembrandt   (cols: Image, Bartsch, States, Title, Year)
  - List of drawings by Rembrandt   (cols: Image, Title, Year, Technique, Dimensions, Gallery, Commentary)

Outputs: rembrandt/wiki_works_raw.json
"""

import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser

API_URL = "https://en.wikipedia.org/w/api.php"
OUTPUT_PATH = "rembrandt/wiki_works_raw.json"

PAGES = [
    {"title": "List of paintings by Rembrandt", "medium": "painting"},
    {"title": "List of etchings by Rembrandt",  "medium": "etching"},
    {"title": "List of drawings by Rembrandt",  "medium": "drawing"},
]


def fetch_page_html(title: str) -> str:
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
        self.cell_links = []
        self.cell_images = []
        self.in_sup = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "sup":
            self.in_sup = True
            return

        if tag == "table" and "wikitable" in attrs_dict.get("class", ""):
            self.in_table = True
            self.current_table = {"rows": [], "headers": []}
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
        if self.in_cell and not self.in_sup:
            clean = data.replace('\xa0', ' ').replace('\n', ' ')
            self.current_cell += clean


def extract_commons_filename(img_src: str) -> str:
    match = re.search(r'/commons/thumb/[0-9a-f]/[0-9a-f]{2}/([^/]+)/\d+px-', img_src)
    if match:
        return urllib.parse.unquote(match.group(1))
    match = re.search(r'/commons/[0-9a-f]/[0-9a-f]{2}/([^/]+)$', img_src)
    if match:
        return urllib.parse.unquote(match.group(1))
    return ""


def extract_provenance_url(links: list) -> str:
    for link in links:
        if link.startswith("/wiki/") and not link.startswith("/wiki/File:"):
            return f"https://en.wikipedia.org{link}"
    return ""


def process_paintings_table(table: dict) -> list:
    """Process the paintings table: Image, Title, Year, Technique, Dimensions, Gallery, Number, Commentary"""
    works = []
    for row in table["rows"]:
        if len(row) < 4:
            continue
        work = {"medium": "painting"}

        # Col 0: Image
        if row[0]["images"]:
            fn = extract_commons_filename(row[0]["images"][0])
            if fn:
                work["commons_filename"] = fn

        # Col 1: Title
        work["title"] = row[1]["text"].strip()
        work["provenance_url"] = extract_provenance_url(row[1]["links"])

        # Col 2: Year
        work["date"] = row[2]["text"].strip()

        # Col 3: Technique (medium detail)
        if len(row) > 3:
            work["technique"] = row[3]["text"].strip()

        # Col 4: Dimensions
        if len(row) > 4:
            work["dimensions"] = row[4]["text"].strip()

        # Col 5: Gallery / current location
        if len(row) > 5:
            work["current_location"] = row[5]["text"].strip()

        work = {k: v for k, v in work.items() if v}
        if work.get("title"):
            works.append(work)
    return works


def process_etchings_table(table: dict) -> list:
    """Process the etchings table: Image, Bartsch, States, Title, Year"""
    works = []
    for row in table["rows"]:
        if len(row) < 4:
            continue
        work = {"medium": "etching"}

        # Col 0: Image
        if row[0]["images"]:
            fn = extract_commons_filename(row[0]["images"][0])
            if fn:
                work["commons_filename"] = fn

        # Col 1: Bartsch catalogue number
        if len(row) > 1:
            work["catalogue_number"] = row[1]["text"].strip()

        # Col 2: States (print states count) — skip for our purposes

        # Col 3: Title
        if len(row) > 3:
            work["title"] = row[3]["text"].strip()
            work["provenance_url"] = extract_provenance_url(row[3]["links"])

        # Col 4: Year
        if len(row) > 4:
            work["date"] = row[4]["text"].strip()

        work = {k: v for k, v in work.items() if v}
        if work.get("title"):
            works.append(work)
    return works


def process_drawings_table(table: dict) -> list:
    """Process the drawings table: Image, Title, Year, Technique, Dimensions, Gallery, Commentary"""
    works = []
    for row in table["rows"]:
        if len(row) < 3:
            continue
        work = {"medium": "drawing"}

        # Col 0: Image
        if row[0]["images"]:
            fn = extract_commons_filename(row[0]["images"][0])
            if fn:
                work["commons_filename"] = fn

        # Col 1: Title
        work["title"] = row[1]["text"].strip()
        work["provenance_url"] = extract_provenance_url(row[1]["links"])

        # Col 2: Year
        work["date"] = row[2]["text"].strip()

        # Col 3: Technique
        if len(row) > 3:
            work["technique"] = row[3]["text"].strip()

        # Col 4: Dimensions
        if len(row) > 4:
            work["dimensions"] = row[4]["text"].strip()

        # Col 5: Gallery
        if len(row) > 5:
            work["current_location"] = row[5]["text"].strip()

        work = {k: v for k, v in work.items() if v}
        if work.get("title"):
            works.append(work)
    return works


def main():
    all_works = []

    for page_info in PAGES:
        title = page_info["title"]
        medium = page_info["medium"]
        print(f"\nFetching: {title}")
        html = fetch_page_html(title)
        print(f"  Got {len(html)} bytes")

        extractor = TableExtractor()
        extractor.feed(html)
        print(f"  Found {len(extractor.tables)} table(s)")

        for table in extractor.tables:
            if medium == "painting":
                works = process_paintings_table(table)
            elif medium == "etching":
                works = process_etchings_table(table)
            else:
                works = process_drawings_table(table)
            print(f"  Extracted {len(works)} {medium}s")
            all_works.extend(works)

    print(f"\nTotal works: {len(all_works)}")
    with_image = sum(1 for w in all_works if "commons_filename" in w)
    print(f"With Commons image: {with_image}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)
    print(f"Written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
