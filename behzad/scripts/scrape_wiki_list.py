#!/usr/bin/env python3
"""
Scrape Behzad (Kamal ud-Din Bihzad) artworks from two sources:

  1. The Wikipedia article gallery (gallerybox HTML on the main article page)
  2. The Wikimedia Commons category tree "Kamal-ud-din Bihzad" and its
     subcategories (which contain many more files with metadata)

The Wikipedia gallery provides nice captions; the Commons category tree
provides broader coverage.  We merge deduplicated results.

Outputs: behzad/wiki_works_raw.json
"""

import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser

API_URL = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
PAGE_TITLE = "Kamāl ud-Dīn Behzād"
COMMONS_CATEGORY = "Category:Kamal-ud-din Bihzad"
OUTPUT_PATH = "behzad/wiki_works_raw.json"

# Subcategories known to contain paintings (not portraits of modern people, etc.)
SUBCATEGORIES = [
    "Category:Seduction of Yusuf",
    "Category:\"Dancing Dervishes\", Folio from a Divan of Hafiz",
    "Category:Garrett Zafarnama",
    "Category:Bustan of Sa'di, 1488, Herat (National Library of Egypt, Adab Farisi 22)",
    "Category:Hasht-Bihisht, 1496, Herat (Topkapı Palace Museum Library, H.676)",
    "Category:Zafarnama, 1528 (Golestan, MS 708)",
    "Category:Jam'i Jam (The Cup of Jamshid), 1459-60, Herat",
]

# Files to skip — duplicates, cropped details, signatures, portraits of Behzad himself
SKIP_PATTERNS = [
    r'\(cropped',
    r'\(detail',
    r'detail\d*\)',
    r'detail\d*\.jpg',
    r'portrait detail',
    r'Signature of Beh',
    r'Depiction of Ustad',
    r'Portrait of miniaturist',
    r'Behzad Original und Kopie',
    r'Behzad Vorbild und Nachahmung',
    r'Cover of manuscript',
    r'\(left-half\)',
    r'\(right-half\)',
    r'\(left\)\.jpg',
    r'\(right\)\.jpg',
    r'\bruler detail\b',
    r'Husayn Bayqara detail',
    r'inscription\.png',
    r'\.tif$',
]


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


def fetch_commons_category_files(category: str) -> list:
    """Fetch all file members of a Commons category (with continuation)."""
    files = []
    cmcontinue = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmtype": "file",
            "cmlimit": "50",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        url = f"{COMMONS_API}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "open-museum/1.0 (art catalog project)"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
        members = data.get("query", {}).get("categorymembers", [])
        files.extend(members)
        cont = data.get("continue", {})
        if "cmcontinue" in cont:
            cmcontinue = cont["cmcontinue"]
        else:
            break
    return files


class GalleryExtractor(HTMLParser):
    """Extract artworks from Wikipedia gallery boxes (same pattern as degas)."""

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


def should_skip(filename: str) -> bool:
    """Check if a file should be skipped (details, crops, non-art)."""
    for pat in SKIP_PATTERNS:
        if re.search(pat, filename, re.IGNORECASE):
            return True
    return False


def parse_gallery_caption(raw: str, links: list) -> dict:
    """Parse a gallery caption from the Wikipedia article into structured data."""
    work = {}
    text = raw.strip().replace(" | ", ", ")

    # Try to extract date patterns
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
        parts = [p.strip() for p in after_date.split(",") if p.strip()]
        location_parts = []
        for part in parts:
            pl = part.lower()
            if any(kw in pl for kw in ["oil", "ink", "tempera", "gouache", "watercolor", "opaque"]):
                work["technique"] = part.strip()
            elif re.search(r'\d+\.?\d*\s*[x×]\s*\d+', part):
                work["dimensions"] = part.strip()
            elif "cm" in pl or "in." in pl or "mm" in pl:
                work["dimensions"] = part.strip()
            else:
                location_parts.append(part.strip())
        if location_parts:
            work["current_location"] = ", ".join(location_parts)

    work["wikipedia_url"] = extract_wikipedia_url(links)
    return work


def title_from_filename(filename: str) -> str:
    """
    Derive a human-readable title from a Commons filename.
    e.g. "Kamal-ud-din_Bihzad_-_Construction_of_the_fort_of_Kharnaq.jpg"
      -> "Construction of the fort of Kharnaq"
    """
    # Strip extension
    name = re.sub(r'\.(jpg|jpeg|png|tif|tiff|svg)$', '', filename, flags=re.IGNORECASE)

    # Remove common prefixes
    name = re.sub(r'^(?:Behzad|Bihzad|Bihhzad|Kamal[_-]ud[_-]din[_ ]Bihzad)\s*[-_–]\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^(?:File:|MET\s+)', '', name, flags=re.IGNORECASE)

    # Replace underscores with spaces
    name = name.replace('_', ' ')

    # Clean up multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()

    # Remove trailing parenthetical identifiers like (H 676), (FGA F1937.27)
    name = re.sub(r'\s*\([A-Z]{1,5}\s+[A-Z0-9.]+\)\s*$', '', name)

    return name


def extract_date_from_title(title: str) -> str:
    """Try to extract a date from the title string."""
    # Match patterns like "c. 1494-1495", "1480", "circa 1500", "1488-1489"
    m = re.search(r'(?:c\.?\s*|circa\s+)?(\d{4})\s*(?:[-–]\s*(?:c\.?\s*)?(\d{2,4}))?', title)
    if m:
        year1 = m.group(1)
        year2 = m.group(2)
        if year2:
            date_str = f"c. {year1}–{year2}"
        else:
            date_str = f"c. {year1}"
        return date_str
    return ""


def extract_location_from_title(title: str) -> str:
    """Extract museum/location info from the title."""
    known_locations = {
        "British Library": "British Library, London",
        "British Museum": "British Museum, London",
        "Golestan": "Golestan Palace, Tehran",
        "Golestan Palace": "Golestan Palace, Tehran",
        "Topkapı": "Topkapi Palace Museum, Istanbul",
        "Topkapi": "Topkapi Palace Museum, Istanbul",
        "Cleveland Museum": "Cleveland Museum of Art",
        "Metropolitan Museum": "Metropolitan Museum of Art, New York",
        "MET": "Metropolitan Museum of Art, New York",
        "Dar al-kutub": "National Library of Egypt, Cairo",
        "National Library of Egypt": "National Library of Egypt, Cairo",
        "Freer": "Freer Gallery of Art, Washington DC",
        "Chester Beatty": "Chester Beatty Library, Dublin",
        "CBL": "Chester Beatty Library, Dublin",
    }
    for key, loc in known_locations.items():
        if key.lower() in title.lower():
            return loc
    return ""


def make_work_from_commons_file(filename: str) -> dict:
    """Create a work entry from a Commons filename."""
    title = title_from_filename(filename)
    if not title or len(title) < 3:
        return {}

    work = {
        "title": title,
        "commons_filename": filename,
    }

    date = extract_date_from_title(title)
    if date:
        work["date"] = date

    location = extract_location_from_title(filename)
    if location:
        work["current_location"] = location

    return work


def main():
    # ── Part 1: Scrape Wikipedia article gallery ──
    print(f"Fetching Wikipedia page: {PAGE_TITLE}")
    html = fetch_page_html(PAGE_TITLE)
    print(f"Got {len(html)} bytes of HTML")

    extractor = GalleryExtractor()
    extractor.feed(html)
    print(f"Found {len(extractor.works)} gallery items from Wikipedia article")

    gallery_works = []
    gallery_filenames = set()
    for item in extractor.works:
        work = parse_gallery_caption(item["raw_caption"], item["links"])
        if item["images"]:
            fn = extract_commons_filename(item["images"][0])
            if fn:
                work["commons_filename"] = fn
                gallery_filenames.add(fn.lower())
        work = {k: v for k, v in work.items() if v}
        if work.get("title"):
            gallery_works.append(work)

    print(f"  Parsed {len(gallery_works)} gallery works")

    # ── Part 2: Scrape Commons category tree ──
    print(f"\nFetching Commons category: {COMMONS_CATEGORY}")
    all_files = fetch_commons_category_files(COMMONS_CATEGORY)
    print(f"  Main category: {len(all_files)} files")

    for subcat in SUBCATEGORIES:
        try:
            sub_files = fetch_commons_category_files(subcat)
            print(f"  {subcat}: {len(sub_files)} files")
            all_files.extend(sub_files)
        except Exception as e:
            print(f"  {subcat}: error - {e}")

    # Deduplicate by filename
    seen_filenames = set()
    unique_files = []
    for f in all_files:
        title = f.get("title", "")
        fn = title.replace("File:", "") if title.startswith("File:") else title
        fn_lower = fn.lower()
        if fn_lower not in seen_filenames:
            seen_filenames.add(fn_lower)
            unique_files.append(fn)

    print(f"\n  Total unique Commons files: {len(unique_files)}")

    # Filter out unwanted files
    filtered_files = [fn for fn in unique_files if not should_skip(fn)]
    print(f"  After filtering: {len(filtered_files)} files")

    # Create work entries from Commons files not already in gallery
    commons_works = []
    for fn in filtered_files:
        if fn.lower() in gallery_filenames:
            continue
        work = make_work_from_commons_file(fn)
        if work.get("title"):
            commons_works.append(work)

    print(f"  New works from Commons: {len(commons_works)}")

    # ── Merge ──
    all_works = gallery_works + commons_works

    # Deduplicate by normalized title
    seen_titles = set()
    deduped = []
    for w in all_works:
        norm = re.sub(r'[^a-z0-9]', '', w["title"].lower())
        if norm and norm not in seen_titles:
            seen_titles.add(norm)
            deduped.append(w)

    all_works = deduped
    print(f"\nTotal works after dedup: {len(all_works)}")

    with_image = sum(1 for w in all_works if "commons_filename" in w)
    print(f"With Commons image: {with_image}")

    for w in all_works[:5]:
        print(f"  {w.get('title', '?')} | {w.get('date', '?')} | {w.get('commons_filename', '?')[:40]}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
