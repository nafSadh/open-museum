#!/usr/bin/env python3
"""
Final backfill pass for amrita-sher-gil and raja-ravi-varma catalogs.

Aggressive Commons fuzzy-matching for entries with empty image_url.
- Queries commons API list=search in File: namespace with several title variants.
- Verifies plausibility (token overlap >= 2, file type image, HEAD 200).
- Populates image_url, thumb_url, commons_filename, commons_page, image_width,
  image_height. Preserves existing key order and inserts the image keys in a
  sensible position.
- Sleeps 1s between requests.
- UA: open-museum/1.0 image-backfill
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from typing import Optional

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = (
    "open-museum/1.0 image-backfill "
    "(https://github.com/nafSadh/open-museum; nafsadh@gmail.com)"
)
SLEEP = 1.5
THUMB_WIDTH = 960

STOPWORDS = {
    "the", "of", "a", "an", "in", "on", "at", "to", "and", "with", "from",
    "for", "by", "de", "la", "le", "les", "du", "des", "un", "une",
    "is", "are", "as", "or", "but", "was", "were", "be", "been",
    "attribution", "needed", "attributed", "unknown", "unidentified",
    "circa", "ca", "c",
}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif", ".webp"}


def api_get(params: dict, timeout: float = 30.0) -> dict:
    qs = urllib.parse.urlencode(params)
    url = f"{COMMONS_API}?{qs}"
    # Retry on 429 with exponential backoff (up to 3 retries).
    for attempt in range(4):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                backoff = 5 * (2 ** attempt)
                print(f"    429 backoff {backoff}s (attempt {attempt + 1})")
                time.sleep(backoff)
                continue
            raise
    raise RuntimeError("api_get exhausted retries")


def head_ok(url: str, timeout: float = 20.0) -> bool:
    """HEAD check. upload.wikimedia.org often 429s HEADs on original files, so
    fall through to GET with a tiny Range header as a secondary check."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT}, method="HEAD"
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except Exception:
        pass
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Range": "bytes=0-1023"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 206)
    except Exception:
        return False


def tokens(text: str) -> set[str]:
    """Lowercase, drop punctuation, drop stopwords and tiny tokens.
    Keeps 4-digit years as tokens even though they are numeric."""
    text = text.lower()
    # strip bracketed tails like [attribution needed]
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"\([^\)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    raw = [t for t in text.split() if t]
    out = set()
    for t in raw:
        if t in STOPWORDS:
            continue
        if re.fullmatch(r"\d{4}", t):
            out.add(t)
        elif len(t) >= 3 and not t.isdigit():
            out.add(t)
    return out


def basename_no_ext(fname: str) -> str:
    # Strip extension
    if "." in fname:
        fname = fname.rsplit(".", 1)[0]
    return fname.replace("_", " ")


def search_commons(query: str, limit: int = 20) -> list[dict]:
    """Commons search in File: namespace. Returns list of dicts with 'title'."""
    try:
        data = api_get({
            "action": "query",
            "list": "search",
            "srnamespace": "6",
            "srsearch": query,
            "srlimit": str(limit),
            "format": "json",
        })
    except Exception as e:
        print(f"    search error: {e}")
        return []
    return data.get("query", {}).get("search", [])


def imageinfo(titles: list[str]) -> dict:
    """Batch imageinfo for a list of File: titles. Keys = filename with underscores."""
    if not titles:
        return {}
    joined = "|".join(titles)
    try:
        data = api_get({
            "action": "query",
            "titles": joined,
            "prop": "imageinfo",
            "iiprop": "url|size|mime",
            "iiurlwidth": str(THUMB_WIDTH),
            "format": "json",
        })
    except Exception as e:
        print(f"    imageinfo error: {e}")
        return {}
    out = {}
    for pid, page in data.get("query", {}).get("pages", {}).items():
        if int(pid) < 0:
            continue
        title = page.get("title", "")
        fname = title[5:] if title.startswith("File:") else title
        fname = fname.replace(" ", "_")
        iis = page.get("imageinfo") or []
        if not iis:
            continue
        ii = iis[0]
        out[fname] = {
            "image_url": ii.get("url", ""),
            "thumb_url": ii.get("thumburl", ""),
            "commons_page": ii.get("descriptionurl", ""),
            "width": ii.get("width"),
            "height": ii.get("height"),
            "mime": ii.get("mime", ""),
        }
    return out


def strip_articles(title: str) -> str:
    t = title.strip()
    for art in ("The ", "A ", "An "):
        if t.startswith(art):
            t = t[len(art):]
            break
    return t


def title_variants(title: str) -> list[str]:
    """Build a few variant forms of the title to try as search phrases."""
    # strip [brackets], (parens)
    base = re.sub(r"\[[^\]]*\]", "", title)
    base = re.sub(r"\([^\)]*\)", "", base)
    base = base.strip(" ,.;:-")
    variants = []
    seen = set()

    def add(v: str):
        v = re.sub(r"\s+", " ", v).strip(" ,.;:-")
        if v and v.lower() not in seen:
            seen.add(v.lower())
            variants.append(v)

    add(base)
    add(strip_articles(base))
    # hyphens/apostrophes
    add(base.replace("-", " "))
    add(base.replace("'", ""))
    add(base.replace("\u2019", ""))
    # common diacritic stripping (Zebegény -> Zebegeny)
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", base)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    add(ascii_only)
    return variants


BAD_ARTIST_MARKERS = {
    # Lowercase substrings. If any appears in a filename (normalized), the
    # candidate is rejected because it's a file about a DIFFERENT artist.
    # Only include artists very likely to pollute search results for ASG/RRV.
    "vermeer", "rembrandt", "monet", "degas", "munch", "cassatt", "caravaggio",
    "leonardo", "hiroshige", "hokusai", "utamaro", "kuniyoshi", "tagore",
    "xu_beihong", "xu beihong", "gogh", "van_gogh", "gribkov", "bonnard",
    "titian", "renoir", "cezanne", "manet", "picasso", "matisse",
    "gauguin", "toulouse", "klimt", "schiele", "sargent",
    "reynolds", "gainsborough", "turner", "constable", "whistler",
    "ducreux", "bilinska", "bilińska", "nadar", "curtis",
    "malczewski", "behzad", "gurney",
    "raphael", "michelangelo", "ingres", "delacroix",
    # Cross-contamination for ASG <-> RRV: don't want RRV files tagged to ASG
    # and vice-versa.
}


def normalize_for_compare(s: str) -> str:
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", s)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    return ascii_only.lower().replace("_", " ").replace("-", " ")


def artist_in_filename(artist_names: list[str], filename: str) -> bool:
    fn_n = normalize_for_compare(filename)
    # Build a set of artist forms to test. Each artist name plus variants.
    forms: set[str] = set()
    for a in artist_names:
        an = normalize_for_compare(a)
        forms.add(an)
        forms.add(an.replace(" ", ""))
    # Also accept last-name only for single-word matches
    for a in artist_names:
        parts = a.split()
        if parts:
            forms.add(normalize_for_compare(parts[-1]))
    for f in forms:
        if f and f in fn_n:
            return True
    return False


def contains_bad_artist(artist_names: list[str], filename: str) -> bool:
    fn_n = normalize_for_compare(filename)
    artist_norms = {normalize_for_compare(a) for a in artist_names}
    for m in BAD_ARTIST_MARKERS:
        if m in fn_n:
            # Only reject if it's a different artist than the target
            if not any(m in an for an in artist_norms):
                return True
    return False


def extract_year(s: str) -> Optional[int]:
    m = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", s)
    return int(m.group(1)) if m else None


def plausibility(
    target_title: str,
    artist_names: list[str],
    file_title: str,
    date_hint: str = "",
) -> tuple[bool, int, str]:
    """Return (ok, score, reason). Strict checks:
    - Artist name MUST appear in filename.
    - Must not contain another known artist's name.
    - Year must match within +-1 year if both present.
    - At least 1 shared meaningful token between title and filename (on top of
      the artist-in-filename requirement).
    """
    fn_only = file_title[5:] if file_title.startswith("File:") else file_title
    fn_text = basename_no_ext(fn_only)
    if not artist_in_filename(artist_names, fn_only):
        return False, 0, "artist not in filename"
    if contains_bad_artist(artist_names, fn_only):
        return False, 0, "other artist in filename"
    # Year alignment
    target_year = extract_year(date_hint or "")
    file_year = extract_year(fn_text)
    if target_year and file_year and abs(target_year - file_year) > 1:
        return False, 0, f"year mismatch {target_year} vs {file_year}"
    # Token overlap (excluding the artist name tokens themselves)
    file_tokens = tokens(fn_text)
    title_tokens = tokens(target_title)
    if target_year:
        title_tokens.add(str(target_year))
    artist_tokens: set = set()
    for a in artist_names:
        artist_tokens |= tokens(a)
    shared = (file_tokens & title_tokens) - artist_tokens
    # Require >= 2 shared non-artist tokens (title + optional year count as
    # separate tokens). Bare single-word matches like {"woman"} or
    # {"mendicant"} are too loose for generic titles.
    if len(shared) < 2:
        return False, 0, f"only {len(shared)} shared non-artist tokens: {shared}"
    return True, len(shared), "ok"


def is_image_mime(mime: str, filename: str) -> bool:
    mime = (mime or "").lower()
    if mime.startswith("image/"):
        # exclude svg, and exclude djvu/pdf implicitly
        if "svg" in mime:
            return False
        return True
    # fallback by extension
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in IMAGE_EXTS


def queries_for(artist_names: list[str], title: str) -> list[str]:
    """Produce a series of search queries to try, in order of specificity."""
    variants = title_variants(title)
    queries = []
    seen = set()

    def add(q):
        q = re.sub(r"\s+", " ", q).strip()
        if q and q.lower() not in seen:
            seen.add(q.lower())
            queries.append(q)

    # Artist + title variants (most specific)
    for a in artist_names:
        for v in variants:
            add(f"{a} {v}")
    # Title only (fallback)
    for v in variants:
        add(v)
    return queries


def find_match(
    artist_names: list[str],
    title: str,
    date_hint: str = "",
    used_filenames: Optional[set] = None,
) -> Optional[dict]:
    queries = queries_for(artist_names, title)
    used_filenames = used_filenames or set()
    print(f"  queries: {len(queries)}")
    for q in queries:
        print(f"   -> {q!r}")
        hits = search_commons(q, limit=20)
        time.sleep(SLEEP)
        if not hits:
            continue
        # Filter by token overlap + extension + strict artist-in-filename
        candidates = []
        for h in hits:
            ft = h.get("title", "")
            fn_only = ft[5:] if ft.startswith("File:") else ft
            ext_low = fn_only.rsplit(".", 1)[-1].lower() if "." in fn_only else ""
            if ext_low in {"svg", "pdf", "djvu", "webm", "ogv", "ogg"}:
                continue
            ok, score, reason = plausibility(title, artist_names, ft, date_hint)
            if not ok:
                # quiet; comment out for verbose debugging:
                # print(f"    skip: {fn_only} ({reason})")
                continue
            candidates.append((ft, score))
        if not candidates:
            continue
        # Order: by score desc
        candidates.sort(key=lambda c: -c[1])
        titles = [c[0] for c in candidates[:5]]
        info = imageinfo(titles)
        time.sleep(SLEEP)
        for ft, score in candidates[:5]:
            fn_only = ft[5:] if ft.startswith("File:") else ft
            fn_key = fn_only.replace(" ", "_")
            if fn_key in used_filenames:
                print(f"    skip (already used): {fn_key}")
                continue
            meta = info.get(fn_key)
            if not meta:
                continue
            if not is_image_mime(meta.get("mime", ""), fn_only):
                continue
            image_url = meta.get("image_url", "")
            if not image_url:
                continue
            # Prefer HEAD-check on the thumb URL (upload.wikimedia.org 429s
            # original HEADs; thumbs are friendlier).
            verify_url = meta.get("thumb_url") or image_url
            if not head_ok(verify_url):
                print(f"    HEAD fail: {verify_url}")
                continue
            print(f"    MATCH ({score} shared): {fn_only}")
            return {
                "commons_filename": fn_key,
                "image_url": image_url,
                "thumb_url": meta.get("thumb_url") or image_url,
                "commons_page": meta.get("commons_page")
                or f"https://commons.wikimedia.org/wiki/File:{fn_key}",
                "image_width": meta.get("width"),
                "image_height": meta.get("height"),
            }
    return None


# Placement of new keys per existing schema patterns:
#   title ... date ... [commons_filename] ... image_url ... thumb_url ...
#   commons_page ... image_width image_height ... (rest)
IMG_FIELDS_ORDER = [
    "commons_filename",
    "image_url",
    "thumb_url",
    "commons_page",
    "image_width",
    "image_height",
]


def insert_image_fields(entry: dict, img: dict) -> dict:
    """
    Insert image fields, preserving existing key order.
    Put commons_filename right after 'title' if present, else after 'date';
    then image_url/thumb_url/commons_page; then image_width/image_height
    right before 'id' (if exists) or at end of core data block.
    """
    keys = list(entry.keys())
    new_entry: dict = {}

    # Build placement map: after which existing key each new key goes
    # strategy: one insertion point right after title for commons_filename +
    # image_url + thumb_url + commons_page + image_width + image_height.
    anchor = None
    if "title" in keys:
        anchor = "title"
    elif "date" in keys:
        anchor = "date"

    # Rebuild:
    inserted = False
    for k in keys:
        new_entry[k] = entry[k]
        if k == anchor and not inserted:
            for nk in IMG_FIELDS_ORDER:
                if nk in img and img[nk] is not None and img[nk] != "":
                    # skip width/height if None
                    new_entry[nk] = img[nk]
                elif nk in ("image_width", "image_height") and img.get(nk) is None:
                    continue
            inserted = True

    if not inserted:
        # fallback: append
        for nk in IMG_FIELDS_ORDER:
            if nk in img and img[nk] not in (None, ""):
                new_entry[nk] = img[nk]

    return new_entry


def process_catalog(path: str, artist_names: list[str]) -> tuple[int, list[str]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Track filenames already bound to entries so we don't reuse them.
    used_filenames: set = {
        e["commons_filename"]
        for e in data
        if e.get("commons_filename")
    }

    empty_idxs = [i for i, e in enumerate(data) if not e.get("image_url")]
    print(f"\n=== {path}: {len(empty_idxs)} empty entries ===")
    resolved = 0
    unresolved: list[str] = []

    for idx in empty_idxs:
        entry = data[idx]
        title = entry.get("title", "")
        date_hint = entry.get("date", "") or ""
        print(f"\n[{path}] id={entry.get('id')} title={title!r} date={date_hint!r}")
        try:
            match = find_match(artist_names, title, date_hint, used_filenames)
        except Exception as e:
            print(f"  ERROR: {e}")
            match = None
        if match:
            data[idx] = insert_image_fields(entry, match)
            used_filenames.add(match["commons_filename"])
            resolved += 1
        else:
            unresolved.append(title)
            print("  (no match)")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\n=== {path}: resolved {resolved}/{len(empty_idxs)}, wrote file ===")
    return resolved, unresolved


def main():
    import os
    # line-buffer stdout so progress is visible via `tee`
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    os.chdir("/Users/nafsadh/src/open-museum")
    asg_names = ["Amrita Sher-Gil", "Sher-Gil", "Amrita Sher Gil"]
    rrv_names = ["Raja Ravi Varma", "Ravi Varma"]

    asg_resolved, asg_unresolved = process_catalog(
        "amrita-sher-gil/catalog.json", asg_names
    )
    rrv_resolved, rrv_unresolved = process_catalog(
        "raja-ravi-varma/catalog.json", rrv_names
    )

    print("\n\n======== SUMMARY ========")
    print(f"ASG resolved: {asg_resolved}/37")
    print(f"RRV resolved: {rrv_resolved}/15")
    print("\nASG unresolved:")
    for t in asg_unresolved:
        print(f"  - {t}")
    print("\nRRV unresolved:")
    for t in rrv_unresolved:
        print(f"  - {t}")


if __name__ == "__main__":
    main()
