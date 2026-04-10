#!/usr/bin/env python3
"""
Scrape the Wikipedia "List of paintings by Claude Monet" page
and extract structured artwork data from the HTML tables.

Outputs: monet/wiki_works_raw.json
"""

import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser

API_URL = "https://en.wikipedia.org/w/api.php"
PAGE_TITLE = "List of paintings by Claude Monet"
OUTPUT_PATH = "monet/wiki_works_raw.json"


def fetch_page_html(title: str) -> str:
    """Fetch parsed HTML of a Wikipedia page via the API."""
    params = urllib.parse.urlencode({
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json",
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
            # Clean spaces
            clean_data = data.replace('\xa0', ' ').replace('\n', ' ')
            self.current_cell += clean_data


def extract_commons_filename(img_src: str) -> str:
    """Extract the Commons filename from a thumbnail URL."""
    match = re.search(r'/commons/thumb/[0-9a-f]/[0-9a-f]{2}/([^/]+)/\d+px-', img_src)
    if match:
        return urllib.parse.unquote(match.group(1))
    match = re.search(r'/commons/[0-9a-f]/[0-9a-f]{2}/([^/]+)$', img_src)
    if match:
        return urllib.parse.unquote(match.group(1))
    return ""


def extract_wikipedia_url(links: list) -> str:
    for link in links:
        if link.startswith("/wiki/") and not link.startswith("/wiki/File:"):
            return f"https://en.wikipedia.org{link}"
    return ""


def parse_w_number_medium(text: str) -> dict:
    """Extract W.X number and medium from the 5th column text."""
    result = {"raw_cat_medium": text}
    # Match W. number which could be like W.1, W. 9, W.5a, W. 1234
    w_match = re.search(r'W\.\s*(\d+[a-zA-Z]?)', text)
    if w_match:
        result["w_number"] = f"W.{w_match.group(1).lower()}"
        # Medium is whatever is after the W number
        end_pos = w_match.end()
        medium_text = text[end_pos:].strip()
        if medium_text:
            result["medium"] = medium_text
    return result


def determine_series(title: str, section: str) -> str:
    """Assign a series name if title or section matches prominent ones."""
    t = title.lower()
    s = section.lower()
    
    series_map = {
        "water lilies": ["water lilies", "nymphéas", "water-lilies"],
        "haystacks": ["haystacks", "meules"],
        "rouen cathedral": ["rouen cathedral", "cathédrale de rouen"],
        "poplars": ["poplars", "les peupliers"],
        "houses of parliament": ["houses of parliament", "le parlement"],
        "charing cross bridge": ["charing cross bridge"],
        "waterloo bridge": ["waterloo bridge"],
        "venice": ["venice", "grand canal", "san giorgio maggiore"],
        "japanese bridge": ["japanese bridge", "bridge over a pond of water lilies", "japanese footbridge"],
        "argenteuil": ["argenteuil"],
        "vétheuil": ["vétheuil"],
        "bordighera": ["bordighera"],
        "pourville": ["pourville"],
        "étretat": ["étretat"]
    }
    
    for canon, keys in series_map.items():
        if any(k in t or k in s for k in keys):
            return canon
    return "other"


def process_table(table: dict) -> list:
    works = []
    section = table["section"]
    
    for row in table["rows"]:
        if len(row) < 5:
            continue
            
        work = {
            "section": section
        }

        # Col 0: Image and Title
        first_cell = row[0]
        work["title"] = first_cell["text"].strip()
        work["wikipedia_url"] = extract_wikipedia_url(first_cell["links"])
        if first_cell["images"]:
            fname = extract_commons_filename(first_cell["images"][0])
            if fname:
                work["commons_filename"] = fname

        # Col 1: Year
        work["date"] = row[1]["text"].strip()

        # Col 2: Location
        work["current_location"] = row[2]["text"].strip()

        # Col 3: Dimensions
        work["dimensions"] = row[3]["text"].strip()

        # Col 4: Cat. no.Medium
        cat_data = parse_w_number_medium(row[4]["text"])
        work.update(cat_data)
        
        # Series
        work["series"] = determine_series(work.get("title", ""), work.get("section", ""))

        # Clean empty
        work = {k: v for k, v in work.items() if v}
        
        if work.get("title") and work.get("w_number"):
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
        print(f"  Section '{table['section']}': {len(works)} works")
        all_works.extend(works)

    print(f"\nTotal works extracted: {len(all_works)}")

    with_image = sum(1 for w in all_works if "commons_filename" in w)
    with_w = sum(1 for w in all_works if "w_number" in w)
    
    series_counts = {}
    for w in all_works:
        s = w.get("series", "other")
        series_counts[s] = series_counts.get(s, 0) + 1

    print(f"With Commons image: {with_image}")
    print(f"With W number: {with_w}")
    print(f"Series breakdown: {json.dumps(series_counts, indent=2)}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
