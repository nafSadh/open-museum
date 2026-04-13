#!/usr/bin/env python3
"""
Scrape Kitagawa Utamaro works from multiple Wikipedia & Commons sources.

There is no dedicated "List of works" page, so we combine:
  1. Gallery items from the Wikipedia "Utamaro" article.
  2. Wikipedia articles in Category:Works_by_Kitagawa_Utamaro.
  3. Files from Wikimedia Commons categories:
       - Category:Paintings_by_Kitagawa_Utamaro
       - Category:Google_Art_Project_works_by_Kitagawa_Utamaro
       - Category:Kitagawa_Utamaro_works_in_the_Tokyo_National_Museum
       - Category:Prints_by_Kitagawa_Utamaro
       - Category:Ehon_(picture_book)_by_Kitagawa_Utamaro
       - Category:Kitagawa_Utamaro  (top-level files only)

Outputs: utamaro/wiki_works_raw.json
"""

import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser

API_URL = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
PAGE_TITLE = "Utamaro"
OUTPUT_PATH = "utamaro/wiki_works_raw.json"


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


class GalleryExtractor(HTMLParser):
    """Extract artworks from Wikipedia gallery boxes (li.gallerybox)."""

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
    """Find the first Wikipedia article link from a list of hrefs."""
    for link in links:
        if link.startswith("/wiki/") and not link.startswith("/wiki/File:"):
            return f"https://en.wikipedia.org{link}"
    return ""


def parse_caption(raw: str, links: list) -> dict:
    """
    Parse a free-text gallery caption into structured fields.

    Typical formats:
      "Women playing with the mirror, 1797"
      "Three Beauties of the Present Day c. 1793"
      "Hairdresser from the series Twelve types of women's handicraft"
      "Young lady blowing on a poppin"
    """
    work = {}
    text = raw.strip()

    # Replace pipe separators from <br> tags
    text = text.replace(" | ", ", ")

    # Remove "Utamaro" or "Kitagawa Utamaro" prefix
    text = re.sub(r'^(?:Kitagawa\s+)?Utamaro\s*[-\u2013,]\s*', '', text, flags=re.IGNORECASE)

    # Strategy 1: date in parentheses
    paren_match = re.search(
        r'\((\s*(?:c\.?\s*)?(?:about\s+)?\d{4}(?:\s*[-\u2013]\s*(?:c\.?\s*)?\d{2,4})?)\)',
        text
    )
    # Strategy 2: date after comma
    comma_match = re.search(
        r'(?:,\s*)((?:c\.?\s*)?(?:about\s+)?\d{4}(?:\s*[-\u2013]\s*(?:c\.?\s*)?\d{2,4})?)',
        text
    )
    # Strategy 3: date after space at end
    space_match = re.search(
        r'\s((?:c\.?\s*)?(?:about\s+)?\d{4}(?:\s*[-\u2013]\s*(?:c\.?\s*)?\d{2,4})?)(?:\s*$|,)',
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

    # Parse after-date portion for location info
    if after_date:
        parts = [p.strip() for p in after_date.split(",")]
        location_parts = []
        for part in parts:
            pl = part.lower().strip()
            dim_pattern = re.compile(r'\d+\.?\d*\s*[x\u00d7]\s*\d+', re.IGNORECASE)
            if dim_pattern.search(part):
                work["dimensions"] = part.strip()
            elif "cm" in pl or "in." in pl or "mm" in pl:
                work["dimensions"] = part.strip()
            elif part.strip():
                location_parts.append(part.strip())
        if location_parts:
            work["current_location"] = ", ".join(location_parts)

    work["wikipedia_url"] = extract_wikipedia_url(links)
    return work


def scrape_article_gallery() -> list:
    """Scrape gallery items from the main Wikipedia article."""
    print(f"Fetching Wikipedia page: {PAGE_TITLE}")
    html = fetch_page_html(PAGE_TITLE)
    print(f"  Got {len(html)} bytes of HTML")

    extractor = GalleryExtractor()
    extractor.feed(html)
    print(f"  Found {len(extractor.works)} gallery items")

    all_works = []
    for item in extractor.works:
        work = parse_caption(item["raw_caption"], item["links"])
        if item["images"]:
            fn = extract_commons_filename(item["images"][0])
            if fn:
                work["commons_filename"] = fn
        work = {k: v for k, v in work.items() if v}
        if work.get("title"):
            work["source"] = "wikipedia_gallery"
            all_works.append(work)

    return all_works


def fetch_category_members(cat_title: str, api_url: str = API_URL, cmtype: str = "page") -> list:
    """Fetch all members of a Wikipedia/Commons category."""
    members = []
    cmcontinue = ""
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": cat_title,
            "cmtype": cmtype,
            "cmlimit": "500",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        url = f"{api_url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "open-museum/1.0 (art catalog project)"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
        members.extend(data.get("query", {}).get("categorymembers", []))
        cont = data.get("continue", {}).get("cmcontinue")
        if not cont:
            break
        cmcontinue = cont
    return members


def scrape_wikipedia_category() -> list:
    """Get works from the Wikipedia Category:Works_by_Kitagawa_Utamaro."""
    print("Fetching Wikipedia category: Works_by_Kitagawa_Utamaro")
    members = fetch_category_members("Category:Works_by_Kitagawa_Utamaro")
    print(f"  Found {len(members)} article pages")

    all_works = []
    for m in members:
        title = m.get("title", "")
        if not title:
            continue
        # Clean up disambiguation suffixes
        clean_title = re.sub(r'\s*\(Utamaro\)\s*$', '', title)
        work = {
            "title": clean_title,
            "wikipedia_url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
            "source": "wikipedia_category",
        }
        all_works.append(work)
    return all_works


def clean_commons_title(filename: str) -> str:
    """
    Extract a human-readable title from a Commons filename.

    Handles patterns like:
      "Kitagawa Utamaro - BATHING IN COLD WATER - Google Art Project.jpg"
      "Hari-shigoto (Needlework) by Kitagawa Utamaro, Tokyo National Museum.jpg"
      "Two beauties under wisteria.jpg"
    """
    # Remove File: prefix
    name = filename
    if name.startswith("File:"):
        name = name[5:]

    # Remove extension
    name = re.sub(r'\.(jpe?g|png|tif|tiff|gif|svg)$', '', name, flags=re.IGNORECASE)

    # Remove Google Art Project suffix
    name = re.sub(r'\s*[-\u2013]\s*Google Art Project.*$', '', name)
    # Remove museum accession numbers
    name = re.sub(r'\s*[-\u2013]\s*\d+\.\d+\.\d+\s*[-\u2013]\s*.*$', '', name)
    # Remove MET prefix files
    if name.startswith("MET "):
        name = name  # keep as-is, will be merged later or filtered
    # Remove "by Kitagawa Utamaro" suffixes
    name = re.sub(r'\s*(?:by|de|van)\s+(?:K\.?\s*)?(?:Kitagawa\s+)?Utamaro.*$', '', name, flags=re.IGNORECASE)
    # Remove "Kitagawa Utamaro - " prefix
    name = re.sub(r'^(?:Kitagawa\s+)?(?:Utamaro\s+)?(?:I\s*,?\s*)?(?:published\s+by\s+[^-]+\s*-\s*)?', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^Kitagawa\s+Utamaro\s*[-\u2013]\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^Kitagawa\s+utamaro\s*,\s*', '', name, flags=re.IGNORECASE)
    # Remove trailing museum info patterns
    name = re.sub(r'\s*,\s*(?:Tokyo National Museum|Metropolitan Museum|musée|Mus[ée]e).*$', '', name, flags=re.IGNORECASE)

    # Clean up parenthetical alt text if it starts with (
    # but keep "(Needlework)" style annotations
    name = re.sub(r'\s*\((?:cropped[^)]*|detail[^)]*)\)', '', name, flags=re.IGNORECASE)

    # Remove leading/trailing punctuation
    name = name.strip(' -\u2013,')

    # Replace underscores with spaces
    name = name.replace('_', ' ')

    return name.strip()


def scrape_commons_categories() -> list:
    """Scrape files from Commons categories related to Utamaro."""
    categories = [
        "Category:Paintings_by_Kitagawa_Utamaro",
        "Category:Google_Art_Project_works_by_Kitagawa_Utamaro",
        "Category:Kitagawa_Utamaro_works_in_the_Tokyo_National_Museum",
        "Category:Prints_by_Kitagawa_Utamaro",
        "Category:Ehon_(picture_book)_by_Kitagawa_Utamaro",
        "Category:Kitagawa_Utamaro",
    ]

    seen_files = set()
    all_works = []

    for cat in categories:
        cat_short = cat.replace("Category:", "")
        print(f"  Fetching Commons: {cat_short}")
        members = fetch_category_members(cat, api_url=COMMONS_API, cmtype="file")
        print(f"    Got {len(members)} files")

        for m in members:
            title = m.get("title", "")
            if not title or title in seen_files:
                continue
            seen_files.add(title)

            # Extract filename from "File:xxx.jpg"
            filename = title[5:] if title.startswith("File:") else title

            # Skip non-image files and duplicates/reproductions
            if not re.search(r'\.(jpe?g|png|tif|tiff|gif)$', filename, re.IGNORECASE):
                continue
            # Skip "modern reproductions" or overly generic MET filenames
            if filename.startswith("MET ") and len(filename) < 20:
                continue

            clean_title = clean_commons_title(title)
            if not clean_title or len(clean_title) < 3:
                clean_title = filename

            work = {
                "title": clean_title,
                "commons_filename": filename.replace(' ', '_'),
                "source": "commons_category",
            }
            all_works.append(work)

    return all_works


def merge_works(gallery: list, wiki_cat: list, commons: list) -> list:
    """
    Merge works from all sources, deduplicating by title similarity.
    Priority: gallery > wiki_cat > commons (gallery has best metadata).
    """
    merged = []
    seen_titles = set()
    seen_filenames = set()

    def normalize(s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r'^(the|a|an)\s+', '', s)
        s = re.sub(r'[^a-z0-9\s]', ' ', s)
        return re.sub(r'\s+', ' ', s).strip()

    def is_duplicate(title: str, filename: str = "") -> bool:
        nt = normalize(title)
        if nt in seen_titles:
            return True
        if filename and filename in seen_filenames:
            return True
        # Also check for partial matches
        for st in seen_titles:
            if len(st) > 5 and len(nt) > 5:
                if st in nt or nt in st:
                    return True
        return False

    # Add gallery works first (best metadata)
    for w in gallery:
        nt = normalize(w.get("title", ""))
        fn = w.get("commons_filename", "")
        if nt:
            seen_titles.add(nt)
        if fn:
            seen_filenames.add(fn)
        merged.append(w)

    # Add wiki category works (may have article links)
    for w in wiki_cat:
        if not is_duplicate(w.get("title", "")):
            nt = normalize(w.get("title", ""))
            if nt:
                seen_titles.add(nt)
            merged.append(w)

    # Add commons works (have image files)
    for w in commons:
        fn = w.get("commons_filename", "")
        title = w.get("title", "")
        if not is_duplicate(title, fn):
            nt = normalize(title)
            if nt:
                seen_titles.add(nt)
            if fn:
                seen_filenames.add(fn)
            merged.append(w)

    return merged


def enrich_from_wiki_category(merged: list, wiki_cat: list):
    """
    Try to match wiki_cat entries (which have wikipedia_url) with
    commons entries (which have commons_filename but no wikipedia_url).
    """
    def normalize(s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r'^(the|a|an)\s+', '', s)
        s = re.sub(r'[^a-z0-9\s]', ' ', s)
        return re.sub(r'\s+', ' ', s).strip()

    wiki_map = {}
    for w in wiki_cat:
        nt = normalize(w.get("title", ""))
        if nt:
            wiki_map[nt] = w

    for work in merged:
        if work.get("wikipedia_url"):
            continue
        nt = normalize(work.get("title", ""))
        if nt in wiki_map:
            work["wikipedia_url"] = wiki_map[nt]["wikipedia_url"]


def main():
    print("=== Scraping Kitagawa Utamaro works ===\n")

    gallery = scrape_article_gallery()
    print(f"  -> {len(gallery)} works from article gallery\n")

    wiki_cat = scrape_wikipedia_category()
    print(f"  -> {len(wiki_cat)} works from Wikipedia category\n")

    print("Fetching Commons categories...")
    commons = scrape_commons_categories()
    print(f"  -> {len(commons)} unique files from Commons\n")

    print("Merging and deduplicating...")
    merged = merge_works(gallery, wiki_cat, commons)
    enrich_from_wiki_category(merged, wiki_cat)
    print(f"  -> {len(merged)} total unique works")

    with_image = sum(1 for w in merged if "commons_filename" in w)
    print(f"  -> {with_image} with Commons image")

    # Show samples
    for w in merged[:5]:
        print(f"  {w.get('title', '?')} | {w.get('date', '?')} | {w.get('source', '?')}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
