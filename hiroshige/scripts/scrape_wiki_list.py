#!/usr/bin/env python3
"""
Scrape Hiroshige works from multiple Wikipedia pages:
  - The Fifty-three Stations of the Tokaido (55 prints)
  - One Hundred Famous Views of Edo (119 prints)
  - The Sixty-nine Stations of the Kiso Kaido (71 prints, mixed with Eisen)
  - Famous Views of the Sixty-odd Provinces (70 prints)
  - Thirty-six Views of Mount Fuji (Hiroshige) (two series)
  - Hiroshige main article (gallery items for misc works)

Each page has a different table/gallery structure, so we handle each
with its own column-mapping logic.

Outputs: hiroshige/wiki_works_raw.json
"""

import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser


API_URL = "https://en.wikipedia.org/w/api.php"
OUTPUT_PATH = "hiroshige/wiki_works_raw.json"

# Pages to scrape and their parsing modes
SERIES_PAGES = [
    {
        "title": "The Fifty-three Stations of the Tōkaidō",
        "series": "The Fifty-three Stations of the Tokaido",
        "mode": "table",
        "date_default": "1833-1834",
    },
    {
        "title": "One Hundred Famous Views of Edo",
        "series": "One Hundred Famous Views of Edo",
        "mode": "table",
        "date_default": "1856-1858",
    },
    {
        "title": "The Sixty-nine Stations of the Kiso Kaidō",
        "series": "The Sixty-nine Stations of the Kiso Kaido",
        "mode": "table",
        "date_default": "1834-1842",
    },
    {
        "title": "Famous Views of the Sixty-odd Provinces",
        "series": "Famous Views of the Sixty-odd Provinces",
        "mode": "table",
        "date_default": "1853-1856",
    },
    {
        "title": "Thirty-six Views of Mount Fuji (Hiroshige)",
        "series": "Thirty-six Views of Mount Fuji",
        "mode": "table",
        "date_default": "1852-1858",
    },
]

GALLERY_PAGE = {
    "title": "Hiroshige",
    "series": "Other works",
    "mode": "gallery",
}


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


# ── Table extractor ──────────────────────────────────────────────────
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
                # If the row is all headers, store as headers
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


# ── Gallery extractor ────────────────────────────────────────────────
class GalleryExtractor(HTMLParser):
    """Extract artworks from Wikipedia gallery boxes."""

    def __init__(self):
        super().__init__()
        self.works = []
        self.in_gallerybox = False
        self.in_thumb = False
        self.in_gallerytext = False
        self.in_figcaption = False
        self.current_images = []
        self.current_links = []
        self.current_text = ""
        self.in_sup = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")

        if tag == "sup":
            self.in_sup = True
            return

        if tag == "li" and "gallerybox" in cls:
            self.in_gallerybox = True
            self.current_images = []
            self.current_links = []
            self.current_text = ""
            return

        if not self.in_gallerybox:
            return

        if tag == "div" and "thumb" in cls:
            self.in_thumb = True
            return

        if tag == "div" and "gallerytext" in cls:
            self.in_gallerytext = True
            return

        if tag == "figcaption":
            self.in_figcaption = True
            return

        if (self.in_thumb or self.in_gallerybox) and tag == "img":
            src = attrs_dict.get("src", "")
            if src:
                self.current_images.append(src)

        if (self.in_gallerytext or self.in_figcaption) and tag == "a":
            href = attrs_dict.get("href", "")
            if href and not href.startswith("#"):
                self.current_links.append(href)

        if (self.in_gallerytext or self.in_figcaption) and tag == "br":
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
            self.in_figcaption = False
            return

        if tag == "div" and self.in_thumb:
            self.in_thumb = False
        if tag == "div" and self.in_gallerytext:
            self.in_gallerytext = False
        if tag == "figcaption":
            self.in_figcaption = False

    def handle_data(self, data):
        if (self.in_gallerytext or self.in_figcaption) and not self.in_sup:
            clean = data.replace('\xa0', ' ').replace('\n', ' ')
            self.current_text += clean


# ── Helpers ──────────────────────────────────────────────────────────
def extract_commons_filename(img_src: str) -> str:
    """Extract the Commons filename from a thumbnail URL."""
    match = re.search(
        r'/commons/thumb/[0-9a-f]/[0-9a-f]{2}/([^/]+)/\d+px-', img_src
    )
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


def find_image_in_row(row: list) -> str:
    """Find the commons filename from any cell in a row that has images."""
    for cell in row:
        if cell["images"]:
            fn = extract_commons_filename(cell["images"][0])
            if fn:
                return fn
    return ""


def find_header_index(headers: list, *keywords) -> int:
    """Find the column index matching any of the keywords (case-insensitive)."""
    for i, h in enumerate(headers):
        hl = h.lower().strip()
        for kw in keywords:
            if kw in hl:
                return i
    return -1


def cell_text(row: list, idx: int) -> str:
    """Safely get text from a row cell by index."""
    if 0 <= idx < len(row):
        return row[idx]["text"].strip()
    return ""


def cell_links(row: list, idx: int) -> list:
    """Safely get links from a row cell by index."""
    if 0 <= idx < len(row):
        return row[idx]["links"]
    return []


# ── Page-specific processors ────────────────────────────────────────

def process_tokaido(tables: list, series: str, date_default: str) -> list:
    """
    The Fifty-three Stations of the Tokaido.
    Table columns: No., Woodcut print, Station no. and English name,
    Japanese, Transliteration.
    """
    works = []
    for table in tables:
        headers = [h.lower() for h in table.get("headers", [])]
        if not headers:
            continue

        # Find key columns
        name_idx = find_header_index(headers, "english name", "station")
        if name_idx < 0:
            continue

        for row in table["rows"]:
            if len(row) < 3:
                continue

            title = cell_text(row, name_idx)
            # Clean up: "1. Shinagawa-juku" -> extract properly
            # The station name is the main title
            if not title:
                continue

            # Remove leading number/period if present
            title = re.sub(r'^\d+\.\s*', '', title)

            work = {
                "title": title,
                "series": series,
                "date": date_default,
                "commons_filename": find_image_in_row(row),
                "provenance_url": extract_provenance_url(
                    cell_links(row, name_idx)
                ),
            }

            # Get Japanese name
            jp_idx = find_header_index(headers, "japanese")
            if jp_idx >= 0:
                jp = cell_text(row, jp_idx)
                if jp:
                    work["japanese_title"] = jp

            # Get transliteration
            tr_idx = find_header_index(headers, "transliteration", "romaji")
            if tr_idx >= 0:
                tr = cell_text(row, tr_idx)
                if tr:
                    work["transliteration"] = tr

            work = {k: v for k, v in work.items() if v}
            if work.get("title"):
                works.append(work)

    return works


def process_edo_views(tables: list, series: str, date_default: str) -> list:
    """
    One Hundred Famous Views of Edo.
    Table columns: No., Title, Depicted, Remarks, Date, Location, Image.
    """
    works = []
    for table in tables:
        headers = [h.lower() for h in table.get("headers", [])]
        if not headers:
            continue

        title_idx = find_header_index(headers, "title")
        if title_idx < 0:
            continue

        date_idx = find_header_index(headers, "date")
        depicted_idx = find_header_index(headers, "depicted")
        remarks_idx = find_header_index(headers, "remarks")
        location_idx = find_header_index(headers, "location")

        for row in table["rows"]:
            if len(row) < 3:
                continue

            title = cell_text(row, title_idx)
            if not title:
                continue

            # Clean title: remove pipe separators, take first part as main title
            title_parts = title.split(" | ")
            main_title = title_parts[0].strip()

            work = {
                "title": main_title,
                "series": series,
                "date": cell_text(row, date_idx) if date_idx >= 0 else date_default,
                "commons_filename": find_image_in_row(row),
                "provenance_url": extract_provenance_url(
                    cell_links(row, title_idx)
                ),
            }

            if depicted_idx >= 0:
                dep = cell_text(row, depicted_idx)
                if dep:
                    work["depicted"] = dep

            if remarks_idx >= 0:
                rem = cell_text(row, remarks_idx)
                if rem:
                    work["remarks"] = rem

            if not work.get("date") or not work["date"].strip():
                work["date"] = date_default

            work = {k: v for k, v in work.items() if v}
            if work.get("title"):
                works.append(work)

    return works


def process_kiso_kaido(tables: list, series: str, date_default: str) -> list:
    """
    The Sixty-nine Stations of the Kiso Kaido.
    Table columns: No., Woodcut print, English name, Author, Japanese name,
    Transliteration.
    Only include works by Hiroshige (not Eisen).
    """
    works = []
    for table in tables:
        headers = [h.lower() for h in table.get("headers", [])]
        if not headers:
            continue

        name_idx = find_header_index(headers, "english name", "english")
        if name_idx < 0:
            continue

        author_idx = find_header_index(headers, "author")
        jp_idx = find_header_index(headers, "japanese")
        tr_idx = find_header_index(headers, "transliteration", "romaji")

        for row in table["rows"]:
            if len(row) < 3:
                continue

            # Check author — skip Eisen works
            if author_idx >= 0:
                author = cell_text(row, author_idx).lower()
                if "eisen" in author and "hiroshige" not in author:
                    continue

            title = cell_text(row, name_idx)
            if not title:
                continue

            work = {
                "title": title,
                "series": series,
                "date": date_default,
                "commons_filename": find_image_in_row(row),
                "provenance_url": extract_provenance_url(
                    cell_links(row, name_idx)
                ),
            }

            if jp_idx >= 0:
                jp = cell_text(row, jp_idx)
                if jp:
                    work["japanese_title"] = jp

            if tr_idx >= 0:
                tr = cell_text(row, tr_idx)
                if tr:
                    work["transliteration"] = tr

            work = {k: v for k, v in work.items() if v}
            if work.get("title"):
                works.append(work)

    return works


def process_sixty_provinces(tables: list, series: str, date_default: str) -> list:
    """
    Famous Views of the Sixty-odd Provinces.
    Table columns: No., Province, Depicted, Date, Location, Image.
    """
    works = []
    for table in tables:
        headers = [h.lower() for h in table.get("headers", [])]
        if not headers:
            continue

        prov_idx = find_header_index(headers, "province")
        if prov_idx < 0:
            continue

        depicted_idx = find_header_index(headers, "depicted")
        date_idx = find_header_index(headers, "date")

        for row in table["rows"]:
            if len(row) < 3:
                continue

            province = cell_text(row, prov_idx)
            depicted = cell_text(row, depicted_idx) if depicted_idx >= 0 else ""

            if not province and not depicted:
                continue

            # Build a meaningful title
            title = province
            if depicted:
                title = f"{province}: {depicted}" if province else depicted

            work = {
                "title": title,
                "series": series,
                "date": cell_text(row, date_idx) if date_idx >= 0 else date_default,
                "commons_filename": find_image_in_row(row),
                "provenance_url": extract_provenance_url(
                    cell_links(row, prov_idx)
                ),
            }

            if not work.get("date") or not work["date"].strip():
                work["date"] = date_default

            work = {k: v for k, v in work.items() if v}
            if work.get("title"):
                works.append(work)

    return works


def process_fuji(tables: list, series: str, date_default: str) -> list:
    """
    Thirty-six Views of Mount Fuji (Hiroshige).
    Table columns: No., Image, Japanese title, Translated title, Location, Notes.
    Two series: 1852 and 1858.
    """
    works = []
    for table in tables:
        headers = [h.lower() for h in table.get("headers", [])]
        if not headers:
            continue

        title_idx = find_header_index(headers, "translated title", "translated")
        if title_idx < 0:
            title_idx = find_header_index(headers, "title")
        if title_idx < 0:
            continue

        jp_idx = find_header_index(headers, "japanese")
        loc_idx = find_header_index(headers, "location")
        notes_idx = find_header_index(headers, "notes")

        for row in table["rows"]:
            if len(row) < 3:
                continue

            title = cell_text(row, title_idx)
            if not title:
                continue

            work = {
                "title": title,
                "series": series,
                "date": date_default,
                "commons_filename": find_image_in_row(row),
                "provenance_url": extract_provenance_url(
                    cell_links(row, title_idx)
                ),
            }

            if jp_idx >= 0:
                jp = cell_text(row, jp_idx)
                if jp:
                    work["japanese_title"] = jp

            if loc_idx >= 0:
                loc = cell_text(row, loc_idx)
                if loc:
                    work["current_location"] = loc

            work = {k: v for k, v in work.items() if v}
            if work.get("title"):
                works.append(work)

    return works


def process_gallery_page(html: str) -> list:
    """Extract gallery items from the main Hiroshige article."""
    extractor = GalleryExtractor()
    extractor.feed(html)

    works = []
    for item in extractor.works:
        caption = item["raw_caption"].strip()
        if not caption and not item["images"]:
            continue

        # Skip items that are Van Gogh copies or follower works
        caption_lower = caption.lower()
        if "van gogh" in caption_lower:
            continue
        if "follower" in caption_lower:
            continue
        if "copy" in caption_lower and "hiroshige" not in caption_lower:
            continue

        work = parse_gallery_caption(caption, item["links"])

        if item["images"]:
            fn = extract_commons_filename(item["images"][0])
            if fn:
                work["commons_filename"] = fn

        work["series"] = "Other works"
        work = {k: v for k, v in work.items() if v}

        if work.get("title"):
            works.append(work)

    return works


def parse_gallery_caption(raw: str, links: list) -> dict:
    """Parse a free-text gallery caption into structured fields."""
    work = {}
    text = raw.strip().replace(" | ", ", ")

    # Try to extract date in parentheses: "Title (XXXX)"
    paren_match = re.search(
        r'\((\s*(?:c\.?\s*)?(?:about\s+)?\d{4}(?:\s*[-–]\s*(?:c\.?\s*)?\d{2,4})?)\)',
        text
    )
    # Date after comma: "Title, XXXX"
    comma_match = re.search(
        r'(?:,\s*)((?:c\.?\s*)?(?:about\s+)?\d{4}(?:\s*[-–]\s*(?:c\.?\s*)?\d{2,4})?)',
        text
    )

    if paren_match:
        work["date"] = paren_match.group(1).strip()
        title_part = text[:paren_match.start()].strip().rstrip(',').strip()
        after = text[paren_match.end():].strip().lstrip(',').strip()
    elif comma_match:
        work["date"] = comma_match.group(1).strip()
        title_part = text[:comma_match.start()].strip().rstrip(',').strip()
        after = text[comma_match.end():].strip().lstrip(',').strip()
    else:
        title_part = text
        after = ""

    work["title"] = title_part
    if after:
        work["current_location"] = after.strip().rstrip('.')

    work["provenance_url"] = extract_provenance_url(links)
    return work


# ── Main ─────────────────────────────────────────────────────────────
def main():
    all_works = []

    # Process each series page (table-based)
    processors = {
        "The Fifty-three Stations of the Tokaido": process_tokaido,
        "One Hundred Famous Views of Edo": process_edo_views,
        "The Sixty-nine Stations of the Kiso Kaido": process_kiso_kaido,
        "Famous Views of the Sixty-odd Provinces": process_sixty_provinces,
        "Thirty-six Views of Mount Fuji": process_fuji,
    }

    for page_info in SERIES_PAGES:
        title = page_info["title"]
        series = page_info["series"]
        date_default = page_info["date_default"]
        processor = processors[series]

        print(f"\nFetching: {title}")
        html = fetch_page_html(title)
        print(f"  Got {len(html)} bytes")

        extractor = TableExtractor()
        extractor.feed(html)
        print(f"  Found {len(extractor.tables)} tables")

        if extractor.tables:
            for table in extractor.tables:
                hdrs = table.get("headers", [])
                print(f"    Table headers: {hdrs[:6]}")

        works = processor(extractor.tables, series, date_default)
        print(f"  Extracted {len(works)} works for '{series}'")
        all_works.extend(works)

    # Process main article gallery
    print(f"\nFetching: Hiroshige (gallery)")
    html = fetch_page_html(GALLERY_PAGE["title"])
    print(f"  Got {len(html)} bytes")
    gallery_works = process_gallery_page(html)
    print(f"  Extracted {len(gallery_works)} gallery works")
    all_works.extend(gallery_works)

    # De-duplicate by commons_filename where possible
    seen_filenames = set()
    deduped = []
    for w in all_works:
        fn = w.get("commons_filename", "")
        if fn:
            if fn in seen_filenames:
                continue
            seen_filenames.add(fn)
        deduped.append(w)

    print(f"\nTotal works before dedup: {len(all_works)}")
    print(f"Total works after dedup:  {len(deduped)}")

    with_image = sum(1 for w in deduped if "commons_filename" in w)
    print(f"With Commons image: {with_image}")

    # Series breakdown
    series_counts = {}
    for w in deduped:
        s = w.get("series", "unknown")
        series_counts[s] = series_counts.get(s, 0) + 1
    print(f"Series breakdown: {series_counts}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
