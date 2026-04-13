#!/usr/bin/env python3
"""
Scrape Raja Ravi Varma artworks from:
  1. The Wikipedia "Raja Ravi Varma" article — gallery boxes + list of major works
  2. Wikimedia Commons categories — to discover additional paintings with images

There is no dedicated "List of paintings" page for Ravi Varma, so we combine
the Wikipedia article gallery (like degas/) with a Commons category walk to
maximise coverage.

Outputs: raja-ravi-varma/wiki_works_raw.json
"""

import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser


API_URL = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
PAGE_TITLE = "Raja Ravi Varma"
OUTPUT_PATH = "raja-ravi-varma/wiki_works_raw.json"

# Commons categories to walk for paintings
COMMONS_CATEGORIES = [
    "Category:Depiction of Hindu Gods and Goddesses by Raja Ravi Varma",
    "Category:Depiction of scenes from the Mahabharata by Raja Ravi Varma",
    "Category:Depiction of scenes from the Ramayana by Raja Ravi Varma",
    "Category:Paintings of women of India by Raja Ravi Varma",
    "Category:Paintings of men of India by Raja Ravi Varma",
    "Category:Musicians by Raja Ravi Varma",
    "Category:Landscape paintings by Raja Ravi Varma",
    "Category:Google Art Project works by Raja Ravi Varma",
    "Category:Paintings of Damayanti by Raja Ravi Varma",
    "Category:Paintings of Draupadi by Raja Ravi Varma",
    "Category:Paintings by Raja Ravi Varma",
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
    req = urllib.request.Request(url, headers={
        "User-Agent": "open-museum/1.0 (art catalog project)"
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    return data["parse"]["text"]["*"]


def fetch_commons_category(cat_title: str) -> list:
    """Fetch all file members of a Commons category."""
    files = []
    cmcontinue = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": cat_title,
            "cmtype": "file",
            "cmlimit": "500",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        url = f"{COMMONS_API}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "open-museum/1.0 (art catalog project)"
        })
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


# ── Wikipedia gallery extractor (same pattern as degas/) ─────────────


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


# ── List-of-major-works extractor ────────────────────────────────────


class MajorWorksListExtractor(HTMLParser):
    """Extract titles from the 'List of major works' section (div-col ul)."""

    def __init__(self):
        super().__init__()
        self.titles = []
        self.in_div_col = False
        self.in_li = False
        self.in_italic = False
        self.current_text = ""
        self.current_links = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")

        if tag == "div" and "div-col" in cls:
            self.in_div_col = True
            return

        if not self.in_div_col:
            return

        if tag == "li":
            self.in_li = True
            self.current_text = ""
            self.current_links = []
            return

        if self.in_li and tag == "a":
            href = attrs_dict.get("href", "")
            if href and not href.startswith("#"):
                self.current_links.append(href)

        if self.in_li and tag == "i":
            self.in_italic = True

    def handle_endtag(self, tag):
        if tag == "div" and self.in_div_col:
            self.in_div_col = False
            return

        if tag == "li" and self.in_li:
            self.in_li = False
            title = self.current_text.strip()
            if title:
                self.titles.append({
                    "title": title,
                    "links": self.current_links,
                })
            return

        if tag == "i":
            self.in_italic = False

    def handle_data(self, data):
        if self.in_li:
            self.current_text += data.replace('\xa0', ' ').replace('\n', ' ')


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


def extract_wikipedia_url(links: list) -> str:
    """Find the first Wikipedia article link from a list of hrefs."""
    for link in links:
        if link.startswith("/wiki/") and not link.startswith("/wiki/File:"):
            return f"https://en.wikipedia.org{link}"
    return ""


def filename_to_title(filename: str) -> str:
    """Convert a Commons filename into a readable title.

    Handles patterns like:
        "Raja_Ravi_Varma,_Galaxy_of_Musicians.jpg" -> "Galaxy of Musicians"
        "Shakuntala_2.jpg" -> "Shakuntala"
        "Ravi_Varma-Descent_of_Ganga.jpg" -> "Descent of Ganga"
    """
    # Remove extension
    name = re.sub(r'\.\w+$', '', filename)
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    # Remove common prefixes
    name = re.sub(
        r'^(?:Raja\s+)?Ravi\s+Varma\s*[-–,]\s*', '', name, flags=re.IGNORECASE
    )
    name = re.sub(r'^File:\s*', '', name, flags=re.IGNORECASE)
    # Remove trailing attributions: ", by Raja Ravi Varma" etc.
    name = re.sub(
        r',?\s*(?:by\s+)?(?:Raja\s+)?Ravi\s+Varma\b.*$', '', name,
        flags=re.IGNORECASE
    )
    # Remove trailing "by RRV" pattern
    name = re.sub(r'\s+by\s+RRV\b', '', name, flags=re.IGNORECASE)
    # Remove trailing numbers like " 2", " 1" (duplicate indicators)
    name = re.sub(r'\s+\d+$', '', name)
    # Remove parenthetical suffixes like "(crop)", "(cropped)", "(duplicate)"
    name = re.sub(
        r'\s*\((?:crop(?:ped)?|duplicate|edit|crop\s*\d*)\)\s*$', '', name,
        flags=re.IGNORECASE
    )
    # Remove Wellcome/chromolithograph metadata suffixes
    name = re.sub(
        r'\s*(?:Chromolithograph|Wellcome|from The Modern Review).*$', '',
        name, flags=re.IGNORECASE
    )
    # Clean up whitespace and trailing punctuation
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.rstrip(' ,-.')
    return name


def parse_caption(raw: str, links: list) -> dict:
    """Parse a free-text gallery caption into structured fields."""
    work = {}
    text = raw.strip()
    text = text.replace(" | ", ", ")

    # Try to extract date in parentheses: "Title (1890)"
    paren_match = re.search(
        r'\((\s*(?:c\.?\s*)?(?:about\s+)?\d{4}'
        r'(?:\s*[-–]\s*(?:c\.?\s*)?\d{2,4})?)\)',
        text
    )
    comma_match = re.search(
        r'(?:,\s*)((?:c\.?\s*)?(?:about\s+)?\d{4}'
        r'(?:\s*[-–]\s*(?:c\.?\s*)?\d{2,4})?)',
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

    # Parse after-date for medium, dimensions, location
    if after_date:
        parts = [p.strip() for p in after_date.split(",")]
        medium_kw = [
            "oil", "pastel", "watercolor", "watercolour", "lithograph",
            "oleograph", "chromolithograph",
        ]
        dim_pattern = re.compile(r'\d+\.?\d*\s*[x×]\s*\d+', re.IGNORECASE)

        location_parts = []
        for part in parts:
            pl = part.lower().strip()
            if any(kw in pl for kw in medium_kw):
                work["technique"] = part.strip()
            elif dim_pattern.search(part):
                work["dimensions"] = part.strip()
            elif "cm" in pl or "in." in pl:
                work["dimensions"] = part.strip()
            elif part.strip():
                location_parts.append(part.strip())

        if location_parts:
            work["current_location"] = ", ".join(location_parts)

    work["wikipedia_url"] = extract_wikipedia_url(links)
    return work


def extract_date_from_filename(filename: str) -> str:
    """Try to extract a date from a Commons filename."""
    m = re.search(r'\((\d{4})\)', filename)
    if m:
        return m.group(1)
    # Look for bare year at end before extension
    m = re.search(r'[-_ ](\d{4})[-_ .]', filename)
    if m:
        year = int(m.group(1))
        if 1860 <= year <= 1910:
            return str(year)
    return ""


def normalize_key(title: str) -> str:
    """Normalize a title for deduplication."""
    t = title.lower().strip()
    t = re.sub(r'^(the|a|an)\s+', '', t)
    t = re.sub(r'\s*\(.*?\)\s*', ' ', t)
    # Remove "by raja ravi varma" and "by RRV" suffixes
    t = re.sub(r',?\s*(?:by\s+)?(?:raja\s+)?ravi\s+varma\b', '', t)
    t = re.sub(r'\s+by\s+rrv\b', '', t)
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def main():
    # ── 1. Scrape Wikipedia article gallery ──────────────────────────
    print(f"Fetching Wikipedia page: {PAGE_TITLE}")
    html = fetch_page_html(PAGE_TITLE)
    print(f"Got {len(html)} bytes of HTML")

    # Gallery boxes
    gallery_ext = GalleryExtractor()
    gallery_ext.feed(html)
    print(f"Found {len(gallery_ext.works)} gallery items")

    # List of major works
    list_ext = MajorWorksListExtractor()
    list_ext.feed(html)
    print(f"Found {len(list_ext.titles)} titles in list of major works")

    # ── 2. Process gallery items ─────────────────────────────────────
    all_works = []
    seen_keys = set()

    for item in gallery_ext.works:
        work = parse_caption(item["raw_caption"], item["links"])
        if item["images"]:
            fn = extract_commons_filename(item["images"][0])
            if fn:
                work["commons_filename"] = fn
        work = {k: v for k, v in work.items() if v}
        if work.get("title"):
            key = normalize_key(work["title"])
            if key not in seen_keys:
                seen_keys.add(key)
                work["source"] = "wikipedia_gallery"
                all_works.append(work)

    print(f"  Gallery: {len(all_works)} unique works")

    # ── 3. Process list of major works ───────────────────────────────
    list_count = 0
    for item in list_ext.titles:
        title = item["title"].strip()
        key = normalize_key(title)
        if key not in seen_keys:
            seen_keys.add(key)
            work = {
                "title": title,
                "wikipedia_url": extract_wikipedia_url(item["links"]),
                "source": "wikipedia_list",
            }
            work = {k: v for k, v in work.items() if v}
            all_works.append(work)
            list_count += 1

    print(f"  List of major works added: {list_count}")

    # ── 4. Walk Commons categories for additional images ─────────────
    print("\nWalking Wikimedia Commons categories...")
    commons_files = {}  # filename -> set of categories
    for cat in COMMONS_CATEGORIES:
        print(f"  {cat}")
        files = fetch_commons_category(cat)
        print(f"    {len(files)} files")
        for f in files:
            title = f.get("title", "")
            if title.startswith("File:"):
                fname = title[5:].replace(" ", "_")
                if fname not in commons_files:
                    commons_files[fname] = set()
                commons_files[fname].add(cat)

    print(f"\nTotal unique Commons files: {len(commons_files)}")

    # Filter out non-painting files
    skip_patterns = [
        r'portrait.*of.*raja.*ravi.*varma',  # photos of the artist himself
        r'signature',
        r'\.svg$',
        r'self.portrait',
        r'photo.*of',
        r'photograph',
        r'mecca|masjid|medina',  # not paintings
        r'sacred.cow',
        r'studio',
        r'palace.*painting',  # photos of paintings in situ
    ]

    commons_added = 0
    for fname, cats in commons_files.items():
        fname_lower = fname.lower()
        # Skip non-painting files
        if any(re.search(pat, fname_lower) for pat in skip_patterns):
            continue

        title = filename_to_title(fname)
        if not title or len(title) < 3:
            continue

        key = normalize_key(title)
        if key in seen_keys:
            # Already have this work — but maybe we can add the image
            for w in all_works:
                if normalize_key(w.get("title", "")) == key:
                    if "commons_filename" not in w:
                        w["commons_filename"] = fname
                    break
            continue

        seen_keys.add(key)
        date = extract_date_from_filename(fname)
        work = {
            "title": title,
            "commons_filename": fname,
            "source": "commons_category",
        }
        if date:
            work["date"] = date
        all_works.append(work)
        commons_added += 1

    print(f"  Added from Commons: {commons_added} new works")

    # ── 5. Save ──────────────────────────────────────────────────────
    print(f"\nTotal works extracted: {len(all_works)}")
    with_image = sum(1 for w in all_works if "commons_filename" in w)
    print(f"With Commons image: {with_image}")

    for w in all_works[:5]:
        print(
            f"  {w.get('title', '?')} | "
            f"{w.get('date', '?')} | "
            f"{w.get('commons_filename', 'no image')[:40]}"
        )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
