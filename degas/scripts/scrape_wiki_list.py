#!/usr/bin/env python3
"""
Scrape the Edgar Degas Wikipedia article gallery sections.
Unlike other artists, Degas has no dedicated list page — works are in
<gallery> / gallerybox HTML on the main article page.

Three subsections: Paintings, Nudes, Sculptures (~57 works total).
Captions are free-text and parsed heuristically.

Outputs: degas/wiki_works_raw.json
"""

import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser

API_URL = "https://en.wikipedia.org/w/api.php"
PAGE_TITLE = "Edgar Degas"
OUTPUT_PATH = "degas/wiki_works_raw.json"


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
        self.depth = 0

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


def extract_commons_filename(img_src: str) -> str:
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


def parse_caption(raw: str, links: list) -> dict:
    """
    Parse a free-text gallery caption into structured fields.

    Typical formats:
      "The Bellelli Family, 1858-1867, Musée d'Orsay, Paris"
      "Degas - Self Portrait, c.1852"
      "The Dance Class, 1874, oil on canvas, 85×75 cm, Metropolitan Museum"
      "Portrait of a Man (1877), oil on canvas, 31 x 23 in., Clark Art Institute"
      "Marguerite de Gas 1853"
    """
    work = {}
    text = raw.strip()

    # Remove pipe separators from <br> tags
    text = text.replace(" | ", ", ")

    # Clean "Degas - " prefix early
    text = re.sub(r'^(?:Edgar\s+)?Degas\s*[-–,]\s*', '', text, flags=re.IGNORECASE)

    # Strategy 1: date in parentheses — "Title (XXXX)", "Title (c. XXXX-XXXX)"
    paren_match = re.search(
        r'\((\s*(?:c\.?\s*)?(?:modeled\s+)?(?:about\s+)?\d{4}(?:\s*[-–]\s*(?:c\.?\s*)?\d{2,4})?)\)',
        text
    )
    # Strategy 2: date after comma — "Title, XXXX"
    comma_match = re.search(
        r'(?:,\s*)((?:c\.?\s*)?(?:modeled\s+)?(?:about\s+)?\d{4}(?:\s*[-–]\s*(?:c\.?\s*)?\d{2,4})?'
        r'(?:\s*,\s*(?:reworked|cast|finished|completed)[^,]*)?)',
        text
    )
    # Strategy 3: date after space at end or before comma — "Title XXXX" or "Title XXXX, loc"
    space_match = re.search(
        r'\s((?:c\.?\s*)?(?:modeled\s+)?(?:about\s+)?\d{4}(?:\s*[-–]\s*(?:c\.?\s*)?\d{2,4})?)(?:\s*$|,)',
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
    elif space_match:
        work["date"] = space_match.group(1).strip()
        title_part = text[:space_match.start()].strip()
        after_date = text[space_match.end():].strip().lstrip(',').strip()
    else:
        title_part = text
        after_date = ""

    work["title"] = title_part.strip()

    # Parse the after-date portion for medium, dimensions, location
    if after_date:
        parts = [p.strip() for p in after_date.split(",")]
        medium_kw = ["oil", "pastel", "charcoal", "gouache", "watercolor", "essence",
                      "bronze", "wax", "tempera", "pencil", "ink", "monotype"]
        dim_pattern = re.compile(r'\d+\.?\d*\s*[x×]\s*\d+', re.IGNORECASE)
        # Also match fractional inch dimensions like "10 1/4 x 7 1/2 in."
        dim_pattern2 = re.compile(r'\d+\s+\d+/\d+\s*[x×]', re.IGNORECASE)

        location_parts = []
        for part in parts:
            pl = part.lower().strip()
            if any(kw in pl for kw in medium_kw):
                work["technique"] = part.strip()
            elif dim_pattern.search(part) or dim_pattern2.search(part):
                work["dimensions"] = part.strip()
            elif "in." in pl or "cm" in pl:
                work["dimensions"] = part.strip()
            elif part.strip():
                location_parts.append(part.strip())

        if location_parts:
            work["current_location"] = ", ".join(location_parts)

    work["wikipedia_url"] = extract_wikipedia_url(links)

    return work


def main():
    print(f"Fetching Wikipedia page: {PAGE_TITLE}")
    html = fetch_page_html(PAGE_TITLE)
    print(f"Got {len(html)} bytes of HTML")

    extractor = GalleryExtractor()
    extractor.feed(html)
    print(f"Found {len(extractor.works)} gallery items")

    all_works = []
    for item in extractor.works:
        work = parse_caption(item["raw_caption"], item["links"])

        # Extract image
        if item["images"]:
            fn = extract_commons_filename(item["images"][0])
            if fn:
                work["commons_filename"] = fn

        # Clean up empty values
        work = {k: v for k, v in work.items() if v}

        if work.get("title"):
            all_works.append(work)

    print(f"Total works extracted: {len(all_works)}")
    with_image = sum(1 for w in all_works if "commons_filename" in w)
    print(f"With Commons image: {with_image}")

    # Show a few samples
    for w in all_works[:3]:
        print(f"  {w.get('title', '?')} | {w.get('date', '?')} | {w.get('current_location', '?')}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
