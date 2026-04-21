#!/usr/bin/env python3
"""
Scrape Xu Beihong artworks from Wikimedia Commons categories and
the Wikipedia article gallery.

Unlike Western painters, Xu Beihong has no dedicated Wikipedia list page.
Works are gathered from:
  1. Category:Paintings by Xu Beihong (+ subcategory: horses)
  2. Category:Xu Beihong (main, filtering for artwork files)
  3. Gallery section of the "Xu Beihong" Wikipedia article

File metadata from Commons (title, description, date, categories)
is used to build structured records. Auction preview photos and
non-artwork files are filtered out heuristically.

Outputs: xu-beihong/wiki_works_raw.json
"""

import json
import re
import time
import urllib.request
import urllib.parse
from html.parser import HTMLParser

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WIKI_API = "https://en.wikipedia.org/w/api.php"
OUTPUT_PATH = "xu-beihong/wiki_works_raw.json"
USER_AGENT = "open-museum/1.0 (art catalog project)"

# Commons categories to scrape
CATEGORIES = [
    "Category:Paintings by Xu Beihong",
    "Category:Paintings of horses by Xu Beihong",
    "Category:Xu Beihong",
]

# Patterns that indicate auction/exhibition photos rather than artwork reproductions
AUCTION_PATTERNS = [
    r"Bonhams",
    r"Sotheby",
    r"Christie",
    r"HKCEC",
    r"Auction",
    r"preview",
    r"拍賣",
    r"預展",
    r"拍卖",
]

# Patterns that indicate non-artwork files (photos of places, people, etc.)
NON_ARTWORK_PATTERNS = [
    r"Former Residence",
    r"Grave of",
    r"Babaoshan",
    r"纪念馆",
    r"全家福",
    r"全体会议",
    r"Yangshou",
    r"DP2Q",
    r"Hu Shih with",
    r"classmates",
    r"classroom",
    r"group October",
    r"Xu Beihong, Liangyou",
    r"Xu Beihong and Jiang Biwei\.jpg",
    r"Xu Beihong, Wang Ying, and painting",
    r"畫家徐悲鴻夫婦合影",
    r"\.webm$",
    r"Xubeihongguju-m\.jpg",
    r"\(cat extract\)",  # crop of another image, not a separate work
    r"Wang Ying in Put Down Your Whip crop",  # crop of Put Down Your Whip
]


def is_artwork_file(filename: str) -> bool:
    """Filter out auction photos and non-artwork files."""
    for pat in AUCTION_PATTERNS:
        if re.search(pat, filename, re.IGNORECASE):
            return False
    for pat in NON_ARTWORK_PATTERNS:
        if re.search(pat, filename, re.IGNORECASE):
            return False
    # Must be an image file
    if not re.search(r'\.(jpg|jpeg|png|tif|tiff)$', filename, re.IGNORECASE):
        return False
    return True


def fetch_category_files(category: str) -> list:
    """Fetch all file members from a Commons category."""
    files = []
    cmcontinue = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmtype": "file",
            "cmlimit": "500",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        url = f"{COMMONS_API}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())

        for member in data.get("query", {}).get("categorymembers", []):
            title = member.get("title", "")
            if title.startswith("File:"):
                fname = title[5:]
                if is_artwork_file(fname):
                    files.append(fname)

        cont = data.get("continue", {})
        if "cmcontinue" in cont:
            cmcontinue = cont["cmcontinue"]
            time.sleep(0.3)
        else:
            break

    return files


def fetch_file_metadata(filenames: list) -> dict:
    """Fetch extended metadata for files from Commons API."""
    results = {}
    batch_size = 50
    total_batches = (len(filenames) + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        start = batch_num * batch_size
        end = start + batch_size
        batch = filenames[start:end]

        titles = "|".join(f"File:{fn}" for fn in batch)
        params = urllib.parse.urlencode({
            "action": "query",
            "titles": titles,
            "prop": "imageinfo|categories",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": "800",
            "cllimit": "50",
            "format": "json",
        })
        url = f"{COMMONS_API}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            print(f"  API error: {e}")
            continue

        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if int(page_id) < 0:
                continue
            title = page_data.get("title", "")
            fname = title[5:].replace(" ", "_") if title.startswith("File:") else title

            ii = page_data.get("imageinfo", [{}])[0]
            extmeta = ii.get("extmetadata", {})

            # Extract description
            desc_data = extmeta.get("ImageDescription", {}).get("value", "")
            # Strip HTML tags
            desc = re.sub(r'<[^>]+>', '', desc_data).strip()

            # Extract date
            date_str = extmeta.get("DateTimeOriginal", {}).get("value", "")
            if not date_str:
                date_str = extmeta.get("DateTime", {}).get("value", "")
            date_str = re.sub(r'<[^>]+>', '', date_str).strip()

            # Extract object name / title
            obj_name = extmeta.get("ObjectName", {}).get("value", "")
            obj_name = re.sub(r'<[^>]+>', '', obj_name).strip()

            # Extract categories
            cats = [c.get("title", "").replace("Category:", "")
                    for c in page_data.get("categories", [])]

            results[fname] = {
                "description": desc,
                "date_raw": date_str,
                "object_name": obj_name,
                "categories": cats,
                "width": ii.get("width"),
                "height": ii.get("height"),
            }

        if batch_num < total_batches - 1:
            time.sleep(0.5)

    return results


def parse_title_from_filename(fname: str) -> str:
    """Heuristically extract a readable title from a Commons filename."""
    # Remove extension
    name = re.sub(r'\.(jpg|jpeg|png|tif|tiff)$', '', fname, flags=re.IGNORECASE)
    # Remove common prefixes
    name = re.sub(r'^(?:Xu[_\s-]?Bei[Hh]ong[_\s-]?[-_]?\s*)', '', name)
    name = re.sub(r'^(?:徐悲鴻[_\s]?)', '', name)
    name = re.sub(r'^(?:徐悲鸿[_\s]?)', '', name)
    name = re.sub(r'^(?:Xubeihong[_\s]?)', '', name, flags=re.IGNORECASE)
    # Replace underscores and hyphens with spaces
    name = name.replace('_', ' ').replace('-', ' ').strip()
    # Split CamelCase (e.g., "MalayDancers" -> "Malay Dancers")
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    # Clean up "Painting " prefix
    name = re.sub(r'^Painting\s+', '', name, flags=re.IGNORECASE)
    return name.strip() if name.strip() else fname


def parse_date(raw: str, fname: str = "") -> str:
    """Extract a date/year string from raw metadata or filename."""
    if raw:
        # Try to find a year pattern
        m = re.search(r'(\d{4})', raw)
        if m:
            year = int(m.group(1))
            if 1890 <= year <= 1960:
                # Check for date range
                range_m = re.search(r'(\d{4})\s*[-–]\s*(\d{4})', raw)
                if range_m:
                    return f"{range_m.group(1)}-{range_m.group(2)}"
                # Check for circa
                if re.search(r'(?:c\.?|circa|about|ca\.?)\s*' + str(year), raw, re.IGNORECASE):
                    return f"c. {year}"
                return str(year)

    # Try filename for year
    m = re.search(r'[,_\s](\d{4})', fname)
    if m:
        year = int(m.group(1))
        if 1890 <= year <= 1960:
            return str(year)

    return ""


# Known title corrections for files with poor auto-generated titles
TITLE_CORRECTIONS = {
    "Paimai (6).jpg": "Galloping Horse",
    "XuBeiHongMalayDancers.jpg": "Malay Dancers",
    "XuBeiHongMalayOrchids.jpg": "Malay Orchids",
    "XuBeiHongChristina.jpg": "Portrait of Young Lady (Christina Li)",
    "XuBeiHongJenny.jpg": "Portrait of Ms Jenny",
    "XuBeiHongMdmCheng.jpg": "Portrait of Madam Cheng",
    "XuBeiHongLimLoh.jpg": "Portrait of Lim Loh",
    "XuBeihong.jpg": "Galloping Horse (ink painting)",
    "Xubeihongguju-m.jpg": "Former Residence Museum (exterior)",
    "Xubeihong Jiuju.jpg": "Jiuju (Nine Steeds)",
    "Xubeihong liyinquan.jpg": "Portrait of Li Yinquan",
    "Liao_Jingwen.jpg": "Liao Jingwen",
    "徐悲鴻 三駿圖 1941.jpg": "Three Steeds",
    "徐悲鴻 貓 1934.jpg": "Cat",
    "徐悲鴻 馬 1943.jpg": "Horse",
    "徐悲鸿 康有为像.jpg": "Portrait of Kang Youwei",
    "徐悲鸿 康有为夫人像.jpg": "Portrait of Madam Kang Youwei",
    "徐悲鸿虎图轴.jpg": "Tiger",
    "楊仲子全家福, by Xu Beihong.jpg": "Yang Zhongzi Family Portrait",
    "Xu-Beihong-1925-Painting-Jiang-Biwei-by-a-table.jpg": "Portrait of Jiang Biwei at a Table",
    "Xu-Beihong-Painting-Jiang-Biwei-in-cheongsam.jpg": "Portrait of Jiang Biwei in Cheongsam",
    "Xu-Beihong-sketch-drawing-Jiang-Biwei.jpg": "Sketch of Jiang Biwei",
    "Tree and man(selfportrait) Xu Beihong. Guimet.jpg": "Tree and Man (Self-Portrait)",
    "Xu beihong Painting Tianheng's five hundreds heroes.jpg": "Tian Heng and Five Hundred Heroes",
    "Zhensanli bw.jpg": "Zhensanli (B&W reproduction)",
}


def build_work_from_file(fname: str, meta: dict) -> dict:
    """Build a structured work entry from a file and its metadata."""
    work = {"commons_filename": fname}

    # Title: use correction if available, then object_name, description, filename
    if fname in TITLE_CORRECTIONS:
        title = TITLE_CORRECTIONS[fname]
    else:
        title = meta.get("object_name", "")
        if not title or title == fname:
            desc = meta.get("description", "")
            if desc and len(desc) < 200:
                title = desc
            else:
                title = parse_title_from_filename(fname)

    # Clean up title
    title = re.sub(r'\s*by\s+Xu\s+Beihong.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\(Xu\s+Beihong\).*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r',\s*\d{4}\s*$', '', title)  # remove trailing year
    # Remove Wikidata label artifacts like 'label QS:Len,"..."' or 'Chinese:...'
    title = re.sub(r'label\s+QS:L\w+,"[^"]*"', '', title)
    title = re.sub(r'^(?:Chinese|English):\s*', '', title, flags=re.IGNORECASE)
    # Remove 《》 brackets
    title = re.sub(r'[《》]', '', title)
    # Remove "Xu Beihong" / "Xu beihong" prefixes from titles
    title = re.sub(r'^Xu[\s_-]*Beihong[\s_-]*(?:Painting[\s_-]*)?', '', title, flags=re.IGNORECASE)
    # Remove "(selfportrait)" artifact in middle of title, clean Guimet
    title = re.sub(r'\(selfportrait\)', '(Self-Portrait)', title, flags=re.IGNORECASE)
    title = re.sub(r'\.\s*Guimet\s*$', '', title)
    # Replace hyphens used as word separators in filenames
    if re.match(r'^[A-Za-z]+-[A-Za-z]+-', title):
        title = title.replace('-', ' ')
    # Clean up "(orched)" typo from Wikipedia caption
    title = re.sub(r'\s*\(orched\)\s*', ' ', title)
    title = title.strip().strip(',').strip().strip('.')
    # Capitalize title if it's all lowercase
    if title and title == title.lower():
        title = title.title()
    work["title"] = title

    # Date
    date = parse_date(meta.get("date_raw", ""), fname)
    if date:
        work["date"] = date

    return work


# ── Wikipedia article gallery extraction ──

class GalleryExtractor(HTMLParser):
    """Extract artworks from Wikipedia gallery boxes (same as degas pattern)."""

    def __init__(self):
        super().__init__()
        self.works = []
        self.in_gallerybox = False
        self.in_thumb = False
        self.in_gallerytext = False
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

        if self.in_thumb and tag == "img":
            src = attrs_dict.get("src", "")
            if src:
                self.current_images.append(src)

        if self.in_gallerytext and tag == "a":
            href = attrs_dict.get("href", "")
            if href and not href.startswith("#"):
                self.current_links.append(href)

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


def extract_provenance_url(links: list) -> str:
    for link in links:
        if link.startswith("/wiki/") and not link.startswith("/wiki/File:"):
            return f"https://en.wikipedia.org{link}"
    return ""


def parse_gallery_caption(raw: str, links: list) -> dict:
    """Parse a gallery caption into structured fields."""
    work = {}
    text = raw.strip().replace(" | ", ", ")

    # Try to extract date
    paren_match = re.search(
        r'\((\s*(?:c\.?\s*)?\d{4}(?:\s*[-–]\s*(?:c\.?\s*)?\d{2,4})?)\)', text
    )
    comma_match = re.search(
        r'(?:,\s*)((?:c\.?\s*)?\d{4}(?:\s*[-–]\s*(?:c\.?\s*)?\d{2,4})?)', text
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

    work["title"] = title_part.strip()

    # Parse after-date for medium, dimensions, location
    if after:
        parts = [p.strip() for p in after.split(",")]
        medium_kw = ["oil", "ink", "watercolor", "gouache", "pencil", "charcoal",
                      "paper", "canvas", "ceramics", "board", "silk"]
        dim_pattern = re.compile(r'\d+\.?\d*\s*[x×]\s*\d+', re.IGNORECASE)
        location_parts = []
        for part in parts:
            pl = part.lower().strip()
            if any(kw in pl for kw in medium_kw):
                work["technique"] = part.strip()
            elif dim_pattern.search(part):
                work["dimensions"] = part.strip()
            elif "cm" in pl:
                work["dimensions"] = part.strip()
            elif part.strip():
                location_parts.append(part.strip())
        if location_parts:
            work["current_location"] = ", ".join(location_parts)

    work["provenance_url"] = extract_provenance_url(links)

    # Clean title
    title = work.get("title", "")
    title = re.sub(r'\s*\(orched\)\s*', ' ', title)
    title = title.strip()
    if title:
        work["title"] = title

    return work


def fetch_wikipedia_gallery() -> list:
    """Fetch artworks from the Xu Beihong Wikipedia article gallery."""
    params = urllib.parse.urlencode({
        "action": "parse",
        "page": "Xu Beihong",
        "prop": "text",
        "format": "json",
        "disabletoc": "true",
    })
    url = f"{WIKI_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    html = data["parse"]["text"]["*"]

    extractor = GalleryExtractor()
    extractor.feed(html)

    works = []
    for item in extractor.works:
        work = parse_gallery_caption(item["raw_caption"], item["links"])
        if item["images"]:
            fn = extract_commons_filename(item["images"][0])
            if fn:
                work["commons_filename"] = fn
        work = {k: v for k, v in work.items() if v}
        if work.get("title"):
            works.append(work)

    return works


def main():
    all_filenames = set()

    # Step 1: Gather files from Commons categories
    for cat in CATEGORIES:
        print(f"Fetching category: {cat}")
        files = fetch_category_files(cat)
        print(f"  Found {len(files)} artwork files (after filtering)")
        all_filenames.update(files)
        time.sleep(0.3)

    print(f"\nTotal unique artwork files from Commons: {len(all_filenames)}")

    # Step 2: Fetch metadata for all files
    print("\nFetching file metadata from Commons...")
    filenames_list = sorted(all_filenames)
    metadata = fetch_file_metadata(filenames_list)
    print(f"Got metadata for {len(metadata)} files")

    # Step 3: Build work entries from Commons files
    commons_works = []
    seen_filenames = set()
    for fname in filenames_list:
        meta = metadata.get(fname, {})
        work = build_work_from_file(fname, meta)
        if work.get("title") and fname not in seen_filenames:
            commons_works.append(work)
            seen_filenames.add(fname)

    print(f"Built {len(commons_works)} works from Commons")

    # Step 4: Fetch Wikipedia article gallery
    print("\nFetching Wikipedia article gallery...")
    wiki_works = fetch_wikipedia_gallery()
    print(f"Found {len(wiki_works)} works in Wikipedia gallery")

    # Step 5: Merge - add Wikipedia gallery works that aren't already in Commons set
    for ww in wiki_works:
        fn = ww.get("commons_filename", "")
        if fn and fn not in seen_filenames:
            commons_works.append(ww)
            seen_filenames.add(fn)
        elif fn and fn in seen_filenames:
            # Merge Wikipedia data into existing entry
            for cw in commons_works:
                if cw.get("commons_filename") == fn:
                    if ww.get("date") and not cw.get("date"):
                        cw["date"] = ww["date"]
                    if ww.get("title") and len(ww["title"]) > len(cw.get("title", "")):
                        cw["title"] = ww["title"]
                    if ww.get("technique") and not cw.get("technique"):
                        cw["technique"] = ww["technique"]
                    if ww.get("current_location") and not cw.get("current_location"):
                        cw["current_location"] = ww["current_location"]
                    if ww.get("provenance_url") and not cw.get("provenance_url"):
                        cw["provenance_url"] = ww["provenance_url"]
                    break

    all_works = commons_works

    # Step 6: Deduplicate by commons_filename (normalize spaces/underscores)
    deduped = {}
    def norm_fn(f):
        return f.replace(" ", "_").lower()
    for w in all_works:
        fn = norm_fn(w.get("commons_filename", ""))
        if fn in deduped:
            # Merge: keep the entry with more data
            existing = deduped[fn]
            if w.get("date") and not existing.get("date"):
                existing["date"] = w["date"]
            if w.get("title") and len(w["title"]) > len(existing.get("title", "")):
                existing["title"] = w["title"]
            if w.get("technique") and not existing.get("technique"):
                existing["technique"] = w["technique"]
            if w.get("current_location") and not existing.get("current_location"):
                existing["current_location"] = w["current_location"]
            if w.get("provenance_url") and not existing.get("provenance_url"):
                existing["provenance_url"] = w["provenance_url"]
        else:
            deduped[fn] = w

    all_works = list(deduped.values())
    print(f"\nTotal works after merge & dedup: {len(all_works)}")

    with_image = sum(1 for w in all_works if "commons_filename" in w)
    print(f"With Commons filename: {with_image}")

    # Show samples
    for w in all_works[:5]:
        print(f"  {w.get('title', '?')} | {w.get('date', '?')}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_works, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
