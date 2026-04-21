#!/usr/bin/env python3
"""
Scrape Hokusai works from multiple Wikipedia pages:
  1. "Thirty-six Views of Mount Fuji" — wikitable with 46 prints
  2. "A Tour of the Waterfalls of the Provinces" — gallery with 8 prints
  3. "Oceans of Wisdom" — gallery with 10 prints
  4. "One Hundred Views of Mount Fuji" — gallery with illustrations
  5. "Hokusai" main article — "Selected works" gallery

Hokusai has no single "List of works" page, so we combine multiple sources.

Outputs: hokusai/wiki_works_raw.json
"""

import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser


API_URL = "https://en.wikipedia.org/w/api.php"
OUTPUT_PATH = "hokusai/wiki_works_raw.json"


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
    req = urllib.request.Request(url, headers={
        "User-Agent": "open-museum/1.0 (art catalog project)"
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    return data["parse"]["text"]["*"]


# ── Commons filename extraction ──────────────────────────────────────

def extract_commons_filename(img_src: str) -> str:
    """Extract the Commons filename from a thumbnail URL."""
    match = re.search(r'/commons/thumb/[0-9a-f]/[0-9a-f]{2}/([^/]+)/\d+px-', img_src)
    if match:
        return urllib.parse.unquote(match.group(1))
    match = re.search(r'/commons/[0-9a-f]/[0-9a-f]{2}/([^/]+)$', img_src)
    if match:
        return urllib.parse.unquote(match.group(1))
    return ""


def extract_provenance_url(links: list) -> str:
    """Find the first Wikipedia article link from a list of hrefs."""
    for link in links:
        if link.startswith("/wiki/") and not link.startswith("/wiki/File:"):
            return f"https://en.wikipedia.org{link}"
    return ""


# ── Table extractor (for Thirty-six Views) ───────────────────────────

class TableExtractor(HTMLParser):
    """Extract data from HTML wikitables."""

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
            clean_data = data.replace('\xa0', ' ').replace('\n', ' ')
            self.current_cell += clean_data


# ── Gallery extractor (for main article + series pages) ──────────────

class GalleryExtractor(HTMLParser):
    """Extract artworks from Wikipedia gallery boxes."""

    def __init__(self):
        super().__init__()
        self.works = []
        self.in_gallerybox = False
        self.in_thumb = False
        self.in_gallerytext = False
        self.current_images = []
        self.current_links = []
        self.current_text = ""
        self.in_italic = False
        self.in_sup = False
        # Also capture figure-based galleries (used in some pages)
        self.in_figure = False
        self.in_figcaption = False
        self.figure_images = []
        self.figure_links = []
        self.figure_text = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")

        if tag == "sup":
            self.in_sup = True
            return

        # Gallery box pattern
        if tag == "li" and "gallerybox" in cls:
            self.in_gallerybox = True
            self.current_images = []
            self.current_links = []
            self.current_text = ""
            return

        if self.in_gallerybox:
            if tag == "div" and "thumb" in cls:
                self.in_thumb = True
                return
            if tag == "div" and "gallerytext" in cls:
                self.in_gallerytext = True
                return
            if self.in_thumb and tag == "img":
                src = attrs_dict.get("src", "")
                if src:
                    self.current_images.append(src)
            if self.in_gallerytext and tag == "a":
                href = attrs_dict.get("href", "")
                if href and not href.startswith("#"):
                    self.current_links.append(href)
            if self.in_gallerytext and tag == "i":
                self.in_italic = True
            if self.in_gallerytext and tag == "br":
                self.current_text += " | "

    def handle_endtag(self, tag):
        if tag == "sup":
            self.in_sup = False
            return

        if tag == "li" and self.in_gallerybox:
            self.in_gallerybox = False
            if self.current_text.strip() or self.current_images:
                self.works.append({
                    "raw_caption": self.current_text.strip(),
                    "images": self.current_images,
                    "links": self.current_links,
                })
            self.in_thumb = False
            self.in_gallerytext = False
            return

        if tag == "div" and self.in_thumb:
            self.in_thumb = False
        if tag == "div" and self.in_gallerytext:
            self.in_gallerytext = False
        if tag == "i":
            self.in_italic = False

    def handle_data(self, data):
        if self.in_gallerytext and not self.in_sup:
            clean = data.replace('\xa0', ' ').replace('\n', ' ')
            self.current_text += clean


# ── Thirty-six Views processor ───────────────────────────────────────

def process_36_views_table(table: dict) -> list:
    """Convert the Thirty-six Views wikitable into structured records."""
    works = []

    for row in table["rows"]:
        if len(row) < 3:
            continue

        work = {}
        work["series"] = "Thirty-six Views of Mount Fuji"
        work["date"] = "c. 1830-1832"

        # The table has columns: No. | Image | English title | Japanese title
        # But some rows may have different cell counts

        # Find image cell (one with images)
        image_cell = None
        title_cell = None

        for cell in row:
            if cell["images"] and not image_cell:
                image_cell = cell
            elif cell["text"] and not cell["images"]:
                # Skip the number column (purely numeric)
                text = cell["text"].strip()
                if text and not text.isdigit() and not title_cell:
                    title_cell = cell

        if image_cell and image_cell["images"]:
            fname = extract_commons_filename(image_cell["images"][0])
            if fname:
                work["commons_filename"] = fname

        if title_cell:
            work["title"] = title_cell["text"].strip()
            work["provenance_url"] = extract_provenance_url(title_cell["links"])
        else:
            continue  # skip rows without a title

        # Try to get Japanese title from remaining cells
        for cell in row:
            if cell is not title_cell and cell is not image_cell:
                text = cell["text"].strip()
                if text and not text.isdigit() and text != work.get("title", ""):
                    work["japanese_title"] = text
                    break

        work["current_location"] = "Various collections"
        work["technique"] = "Woodblock print (nishiki-e)"

        work = {k: v for k, v in work.items() if v}
        if work.get("title"):
            works.append(work)

    return works


# ── Gallery caption parser ───────────────────────────────────────────

def parse_gallery_caption(raw: str, links: list, series: str = "") -> dict:
    """Parse a gallery caption into structured fields."""
    work = {}
    text = raw.strip()

    # Remove pipe separators from <br> tags
    text = text.replace(" | ", ", ")

    # Try to extract date in parentheses
    paren_match = re.search(
        r'\((\s*(?:c\.?\s*)?(?:about\s+)?\d{4}(?:\s*[-–]\s*(?:c\.?\s*)?\d{2,4})?)\)',
        text
    )
    comma_match = re.search(
        r'(?:,\s*)((?:c\.?\s*)?(?:about\s+)?\d{4}(?:\s*[-–]\s*(?:c\.?\s*)?\d{2,4})?)',
        text
    )

    if paren_match:
        work["date"] = paren_match.group(1).strip()
        title_part = text[:paren_match.start()].strip().rstrip(',').strip()
        after_date = text[paren_match.end():].strip().lstrip(',').strip()
    elif comma_match:
        work["date"] = comma_match.group(1).strip()
        title_part = text[:comma_match.start()].strip().rstrip(',').strip()
        after_date = text[comma_match.end():].strip().lstrip(',').strip()
    else:
        title_part = text
        after_date = ""

    work["title"] = title_part.strip()

    if after_date:
        parts = [p.strip() for p in after_date.split(",")]
        location_parts = []
        for part in parts:
            pl = part.lower().strip()
            if any(kw in pl for kw in ["woodblock", "print", "ink", "color", "colour", "nishiki"]):
                work["technique"] = part.strip()
            elif part.strip():
                location_parts.append(part.strip())
        if location_parts:
            work["current_location"] = ", ".join(location_parts)

    if series:
        work["series"] = series

    work["provenance_url"] = extract_provenance_url(links)
    work["technique"] = work.get("technique", "Woodblock print")

    return work


# ── Main scraping logic ──────────────────────────────────────────────

def scrape_36_views() -> list:
    """Scrape the Thirty-six Views of Mount Fuji page (wikitable)."""
    print("Fetching: Thirty-six Views of Mount Fuji")
    html = fetch_page_html("Thirty-six Views of Mount Fuji")
    print(f"  Got {len(html)} bytes")

    extractor = TableExtractor()
    extractor.feed(html)
    print(f"  Found {len(extractor.tables)} tables")

    all_works = []
    for table in extractor.tables:
        works = process_36_views_table(table)
        print(f"  Extracted {len(works)} works from table")
        all_works.extend(works)

    return all_works


def scrape_gallery_page(page_title: str, series: str, default_date: str = "") -> list:
    """Scrape a gallery-based Wikipedia page."""
    print(f"Fetching: {page_title}")
    html = fetch_page_html(page_title)
    print(f"  Got {len(html)} bytes")

    extractor = GalleryExtractor()
    extractor.feed(html)
    print(f"  Found {len(extractor.works)} gallery items")

    all_works = []
    for item in extractor.works:
        work = parse_gallery_caption(item["raw_caption"], item["links"], series)

        if item["images"]:
            fn = extract_commons_filename(item["images"][0])
            if fn:
                work["commons_filename"] = fn

        if default_date and not work.get("date"):
            work["date"] = default_date

        work = {k: v for k, v in work.items() if v}
        if work.get("title") or work.get("commons_filename"):
            # If no title but has image, use filename as title
            if not work.get("title") and work.get("commons_filename"):
                fname = work["commons_filename"]
                # Clean filename to title
                title = fname.rsplit('.', 1)[0].replace('_', ' ')
                title = re.sub(r'\s*\(.*?\)\s*', ' ', title).strip()
                work["title"] = title
            all_works.append(work)

    return all_works


def scrape_hokusai_main() -> list:
    """Scrape the main Hokusai article Selected works gallery."""
    print("Fetching: Hokusai (main article)")
    html = fetch_page_html("Hokusai")
    print(f"  Got {len(html)} bytes")

    extractor = GalleryExtractor()
    extractor.feed(html)
    print(f"  Found {len(extractor.works)} gallery items")

    all_works = []
    for item in extractor.works:
        work = parse_gallery_caption(item["raw_caption"], item["links"])

        if item["images"]:
            fn = extract_commons_filename(item["images"][0])
            if fn:
                work["commons_filename"] = fn

        work = {k: v for k, v in work.items() if v}
        if work.get("title") or work.get("commons_filename"):
            if not work.get("title") and work.get("commons_filename"):
                fname = work["commons_filename"]
                title = fname.rsplit('.', 1)[0].replace('_', ' ')
                title = re.sub(r'\s*\(.*?\)\s*', ' ', title).strip()
                work["title"] = title
            all_works.append(work)

    return all_works


def deduplicate(works: list) -> list:
    """Remove duplicate works based on commons_filename or title similarity."""
    seen_filenames = set()
    seen_titles = set()
    unique = []

    for w in works:
        fn = w.get("commons_filename", "")
        if fn:
            if fn in seen_filenames:
                continue
            seen_filenames.add(fn)

        title = w.get("title", "").lower().strip()
        # Normalize for comparison
        norm_title = re.sub(r'[^a-z0-9\s]', '', title).strip()
        norm_title = re.sub(r'\s+', ' ', norm_title)

        if norm_title and norm_title in seen_titles and not fn:
            continue

        if norm_title:
            seen_titles.add(norm_title)
        unique.append(w)

    return unique


def main():
    all_works = []

    # 1. Thirty-six Views (the main series, with structured table)
    works_36 = scrape_36_views()
    all_works.extend(works_36)

    # 2. A Tour of the Waterfalls of the Provinces
    works_waterfalls = scrape_gallery_page(
        "A Tour of the Waterfalls of the Provinces",
        series="A Tour of the Waterfalls of the Provinces",
        default_date="c. 1833"
    )
    all_works.extend(works_waterfalls)

    # 3. Oceans of Wisdom
    works_oceans = scrape_gallery_page(
        "Oceans of Wisdom",
        series="Oceans of Wisdom",
        default_date="c. 1833"
    )
    all_works.extend(works_oceans)

    # 4. One Hundred Views of Mount Fuji
    works_100 = scrape_gallery_page(
        "One Hundred Views of Mount Fuji",
        series="One Hundred Views of Mount Fuji",
        default_date="1834-1847"
    )
    all_works.extend(works_100)

    # 5. Selected works from main Hokusai article
    works_main = scrape_hokusai_main()
    all_works.extend(works_main)

    # Deduplicate
    print(f"\nTotal before dedup: {len(all_works)}")
    all_works = deduplicate(all_works)
    print(f"Total after dedup: {len(all_works)}")

    with_image = sum(1 for w in all_works if "commons_filename" in w)
    print(f"With Commons image: {with_image}")

    for w in all_works[:5]:
        print(f"  {w.get('title', '?')} | {w.get('date', '?')} | {w.get('series', '?')}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
