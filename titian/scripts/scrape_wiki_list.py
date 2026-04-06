#!/usr/bin/env python3
"""
Scrape the Wikipedia "List of works by Titian" page
and extract structured artwork data from the HTML tables.

Outputs: titian/wiki_works_raw.json
"""

import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser


API_URL = "https://en.wikipedia.org/w/api.php"
PAGE_TITLE = "List of works by Titian"
OUTPUT_PATH = "titian/wiki_works_raw.json"


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
        if self.in_cell and not self.in_sup:
            # Replace non-breaking spaces & clean newlines
            clean_data = data.replace('\xa0', ' ').replace('\n', ' ')
            self.current_cell += clean_data


def extract_commons_filename(img_src: str) -> str:
    """Extract the Commons filename from a thumbnail URL."""
    # Thumbnail URLs look like:
    # //upload.wikimedia.org/wikipedia/commons/thumb/a/ab/File.jpg/120px-File.jpg
    match = re.search(r'/commons/thumb/[0-9a-f]/[0-9a-f]{2}/([^/]+)/\d+px-', img_src)
    if match:
        return urllib.parse.unquote(match.group(1))
    # Direct file URLs:
    # //upload.wikimedia.org/wikipedia/commons/a/ab/File.jpg
    match = re.search(r'/commons/[0-9a-f]/[0-9a-f]{2}/([^/]+)$', img_src)
    if match:
        return urllib.parse.unquote(match.group(1))
    return ""


def extract_wikipedia_url(links: list) -> str:
    """Find the first Wikipedia article link from a list of hrefs."""
    for link in links:
        if link.startswith("/wiki/") and not link.startswith("/wiki/File:"):
            return f"https://en.wikipedia.org{link}"
    return ""


def process_table(table: dict) -> list:
    """Convert a raw table into structured artwork records."""
    works = []
    
    for row in table["rows"]:
        if len(row) < 5:
            continue

        work = {}
        
        # Col 0: Image
        image_cell = row[0]
        if image_cell["images"]:
            fname = extract_commons_filename(image_cell["images"][0])
            if fname:
                work["commons_filename"] = fname

        # Col 1: Title
        title_cell = row[1]
        raw_title = title_cell["text"]
        
        # Some titles have things in parentheses (like alternative names). We keep the full text.
        # But we also try to get the wikipedia link.
        work["title"] = raw_title.strip()
        work["wikipedia_url"] = extract_wikipedia_url(title_cell["links"])

        # Col 2: Date
        date_cell = row[2]
        work["date"] = date_cell["text"].strip()

        # Col 3: Dimensions
        dim_cell = row[3]
        work["dimensions"] = dim_cell["text"].strip()

        # Col 4: Collection
        collection_cell = row[4]
        work["current_location"] = collection_cell["text"].strip()

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
        print(f"  Extracted {len(works)} works")
        all_works.extend(works)

    print(f"\nTotal works extracted: {len(all_works)}")

    with_image = sum(1 for w in all_works if "commons_filename" in w)
    print(f"With Commons image: {with_image}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
