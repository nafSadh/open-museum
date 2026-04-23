#!/usr/bin/env python3
"""Enrich date / year_start / year_end / circa for the 743 Royal Collection
Windsor Leonardo drawings that lack dates in leonardo-da-vinci/catalog.json.

Strategy (in order):
  1. Extract a date token from the existing `title` or `commons_filename`.
     Most Commons-side titles already encode dates like "c.1513-18".
  2. For entries where (1) yields nothing, scrape col.rct.uk — the
     Royal Collection's collection subdomain serves RCIN-keyed pages
     without the Cloudflare block that www.rct.uk has.
  3. If col.rct.uk can't be reached (rate-limit/403), fall back to the
     Commons category decade hints documented in the task spec.

Writes back to catalog.json with a trailing newline.
"""
import json, re, sys, time, urllib.request, urllib.error, urllib.parse, os

HERE = os.path.dirname(os.path.abspath(__file__))
COLL = os.path.dirname(HERE)
CATALOG = os.path.join(COLL, 'catalog.json')
UA = 'open-museum/1.0 leonardo-dates'
COL_BASE = 'https://col.rct.uk/collection/'
REQ_SLEEP = 1.0  # polite 1 req/s
CACHE = os.path.join(HERE, '_rcin_cache.json')

RCIN_RE = re.compile(r'\bRCIN\s*(\d{4,6})\b', re.I)
# Match date-like tokens anywhere in a string: "c.1513-18", "c. 1505", "1488", "1470-80", "1480s"
DATE_TOKEN_RE = re.compile(
    r'(?:\bc\.\s*|\bcirca\s*|\bca\.\s*|\bprobably\s+|\bperhaps\s+)?'
    r'1[45]\d\d(?:s|\s*[-\u2013\u2014]\s*\d{1,4})?',
    re.I,
)
CENTURY_RE = re.compile(
    r'((?:early|mid|late|first\s+half\s+of(?:\s+the)?|second\s+half\s+of(?:\s+the)?)\s+)?'
    r'(1[45]|15th|16th)(?:th)?[\s-]*century',
    re.I,
)
RANGE_SHORT = re.compile(r'^\s*(1[45]\d\d)\s*[-/]\s*(\d{1,2})\s*$')
RANGE_FULL = re.compile(r'^\s*(1[45]\d\d)\s*[-/]\s*(1[45]\d\d)\s*$')
DECADE_RE = re.compile(r'^\s*(1[45]\d\d)s\s*$')
SINGLE_RE = re.compile(r'^\s*(1[45]\d\d)\s*$')
UNDATED_RE = re.compile(r'^(undated|date\s+unknown|unknown|n\.?\s?d\.?|no\s+date)\.?$', re.I)


def parse_date(raw):
    """Parse a date string into (year_start, year_end, circa).

    Returns (None, None, circa) if unparseable but a circa marker was found,
    else (None, None, False).
    """
    if not raw:
        return None, None, False
    s = str(raw).strip()
    s = s.replace('\u2013', '-').replace('\u2014', '-').replace('\u2212', '-')
    if UNDATED_RE.match(s):
        return None, None, False
    circa = bool(re.search(r'\bc\.|\bcirca\b|\bca\.|\bprobably\b|\bperhaps\b|\?', s, re.I))
    s_clean = re.sub(r'\b(c\.|circa|ca\.|probably|perhaps|about)\s*', '', s, flags=re.I)
    s_clean = re.sub(r'\s+', ' ', s_clean).strip()
    # decade
    m = DECADE_RE.match(s_clean)
    if m:
        b = int(m.group(1))
        return b, b + 9, circa
    # single year
    m = SINGLE_RE.match(s_clean)
    if m:
        y = int(m.group(1))
        return y, y, circa
    # full range
    m = RANGE_FULL.match(s_clean)
    if m:
        b, e = int(m.group(1)), int(m.group(2))
        return min(b, e), max(b, e), circa
    # short-tail range (e.g. 1513-18, 1492-4)
    m = RANGE_SHORT.match(s_clean)
    if m:
        b = int(m.group(1))
        tail = int(m.group(2))
        if len(m.group(2)) == 1:
            end = (b // 10) * 10 + tail
            if end < b:
                end += 10
        else:
            end = (b // 100) * 100 + tail
            if end < b:
                end += 100
        return b, end, circa
    # century: "15th century" / "early 16th century" / "late 15th century"
    cm = CENTURY_RE.search(s)
    if cm:
        qual = (cm.group(1) or '').strip().lower()
        c_num = cm.group(2)
        if c_num in ('15', '15th'):
            # Leonardo lived 1452-1519 so bound at 1500
            if 'early' in qual:
                return 1401, 1433, circa
            if 'mid' in qual:
                return 1434, 1466, circa
            if 'late' in qual:
                return 1467, 1500, circa
            if 'first' in qual:
                return 1401, 1450, circa
            if 'second' in qual:
                return 1451, 1500, circa
            return 1401, 1500, circa
        if c_num in ('16', '16th'):
            # Leonardo died 1519; for Leonardo collection cap at 1519
            if 'early' in qual:
                return 1501, 1519, circa
            if 'first' in qual:
                return 1501, 1519, circa
            # late/second half/mid of 16th is post-Leonardo so treat as literal
            if 'late' in qual:
                return 1567, 1600, circa
            if 'mid' in qual:
                return 1534, 1566, circa
            if 'second' in qual:
                return 1551, 1600, circa
            return 1501, 1600, circa
    # Fallback — any 14xx/15xx years
    years = [int(y) for y in re.findall(r'1[45]\d\d', s_clean)]
    if years:
        return min(years), max(years), circa
    return None, None, circa


def extract_date_token(text):
    """Return a date substring from text, if present, else None."""
    if not text:
        return None
    # Clean up: treat underscores as spaces (for filenames)
    t = text.replace('_', ' ')
    m = DATE_TOKEN_RE.search(t)
    if m:
        raw = m.group(0)
        start = m.start()
        # Preserve explicit "c." / "circa " / "probably " prefix if it sits
        # immediately before the match
        prefix = re.search(r'(c\.\s*|circa\s+|ca\.\s*|probably\s+|perhaps\s+)$',
                           t[:start + 1], re.I)
        if prefix:
            return prefix.group(0) + raw
        return raw
    # Century fallback
    cm = CENTURY_RE.search(t)
    if cm:
        return cm.group(0)
    return None


def extract_rcin(title, commons_filename, provenance_url):
    for s in (title, commons_filename, provenance_url):
        if s:
            m = RCIN_RE.search(s)
            if m:
                return m.group(1)
    return None


def fetch_rct_date(rcin, cache):
    """Return a raw date string from col.rct.uk, or None on failure.

    Uses the cache keyed by RCIN so reruns are idempotent.
    """
    if rcin in cache:
        return cache[rcin]
    url = COL_BASE + rcin
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9',
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        # Cache non-retryable failures so we don't keep hammering them
        cache[rcin] = None
        return None
    except Exception:
        return None
    # Primary: <span class="small">DATE</span> sitting in an <h2> above the image
    # e.g.  <h2>912379 R.jpg  <span class="small">c.1513-18</span></h2>
    small = re.findall(r'<span[^>]*class="[^"]*small[^"]*"[^>]*>([^<]{1,60})</span>', body)
    # First meaningful "small" span usually carries the date — look for one that
    # starts with a 14/15xx year or "c."
    for s in small:
        s = s.strip()
        if re.match(r'^(?:c\.|circa|ca\.|probably|perhaps)?\s*\(?\s*1[45]\d\d', s, re.I):
            cache[rcin] = s
            return s
    # Secondary: look in page title / meta description for a 14/15xx token
    og = re.search(r'<meta property="og:description" content="([^"]+)"', body)
    if og:
        tok = extract_date_token(og.group(1))
        if tok:
            cache[rcin] = tok
            return tok
    # Fall back: any 14/15xx year inside an <h2>
    for h2 in re.findall(r'<h2[^>]*>(.*?)</h2>', body, re.DOTALL):
        tok = extract_date_token(h2)
        if tok:
            cache[rcin] = tok
            return tok
    cache[rcin] = None
    return None


def load_cache():
    if os.path.exists(CACHE):
        try:
            with open(CACHE) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache):
    with open(CACHE, 'w') as f:
        json.dump(cache, f, indent=2, sort_keys=True)


def main():
    # Optional budget cap (minutes) from argv[1], default 45
    budget_min = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
    deadline = time.time() + budget_min * 60

    with open(CATALOG) as f:
        catalog = json.load(f)

    cache = load_cache()

    total_rc = 0
    already_dated = 0
    resolved_from_title = 0
    resolved_from_rct = 0
    unresolved_no_rcin = []  # titles with no RCIN extraction
    unresolved_other = []
    raw_dates = []  # (id, source, raw, parsed)
    rct_fetches = 0
    rct_blocked = False

    # Pass 1: title / filename parsing
    for e in catalog:
        if 'Royal Collection' not in (e.get('harvest_method') or ''):
            continue
        total_rc += 1
        if e.get('year_start') is not None:
            already_dated += 1
            continue
        title = e.get('title') or ''
        fn = e.get('commons_filename') or ''
        tok = extract_date_token(title) or extract_date_token(fn)
        if tok:
            ys, ye, circa = parse_date(tok)
            if ys is not None:
                e['date'] = tok
                e['year_start'] = ys
                e['year_end'] = ye
                e['circa'] = circa
                resolved_from_title += 1
                raw_dates.append((e['id'], 'title', tok, (ys, ye, circa)))
                # Also update era for these (reuse existing era heuristic)
                era = 'unknown'
                if ys < 1485:
                    era = 'early'
                elif ys < 1500:
                    era = 'middle'
                else:
                    era = 'late'
                e['era'] = era

    print(f'Pass 1 (title/filename): resolved {resolved_from_title}/{total_rc - already_dated}')

    # Pass 2: col.rct.uk scraping for still-missing entries
    missing = [e for e in catalog
               if 'Royal Collection' in (e.get('harvest_method') or '')
               and e.get('year_start') is None]

    print(f'\nPass 2 (col.rct.uk): {len(missing)} entries to try (budget {budget_min:.0f} min)...')
    consecutive_fails = 0
    for i, e in enumerate(missing, 1):
        if time.time() > deadline:
            print(f'  ! budget exhausted at {i-1} / {len(missing)}')
            break
        if consecutive_fails >= 5 and rct_fetches > 0:
            print(f'  ! 5 consecutive fails -> pausing RCT scraping')
            rct_blocked = True
            break
        rcin = extract_rcin(e.get('title'), e.get('commons_filename'), e.get('provenance_url'))
        if not rcin:
            unresolved_no_rcin.append(e['id'])
            continue
        # Respect cache (populated on earlier runs)
        was_cached = rcin in cache
        raw = fetch_rct_date(rcin, cache)
        if not was_cached:
            rct_fetches += 1
            time.sleep(REQ_SLEEP)
            if i % 25 == 0:
                save_cache(cache)
            if raw is None:
                consecutive_fails += 1
            else:
                consecutive_fails = 0
        if not raw:
            unresolved_other.append((e['id'], rcin, 'rct-empty'))
            continue
        ys, ye, circa = parse_date(raw)
        if ys is None:
            unresolved_other.append((e['id'], rcin, f'rct-unparseable:{raw[:40]}'))
            continue
        e['date'] = raw
        e['year_start'] = ys
        e['year_end'] = ye
        e['circa'] = circa
        if ys < 1485:
            e['era'] = 'early'
        elif ys < 1500:
            e['era'] = 'middle'
        else:
            e['era'] = 'late'
        resolved_from_rct += 1
        raw_dates.append((e['id'], 'rct.uk', raw, (ys, ye, circa)))

    save_cache(cache)

    # Pass 3: any still-missing? Leave as-is (no useful commons category decade
    # hint is available — all these are in a single root category).
    still_missing = [e for e in catalog
                     if 'Royal Collection' in (e.get('harvest_method') or '')
                     and e.get('year_start') is None]

    # Write back
    with open(CATALOG, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
        f.write('\n')

    # Summary
    print('\n=== SUMMARY ===')
    print(f'  Total Royal Collection entries:   {total_rc}')
    print(f'  Already dated before:             {already_dated}')
    print(f'  Resolved from title/filename:     {resolved_from_title}')
    print(f'  Resolved from col.rct.uk:         {resolved_from_rct}')
    print(f'  Still missing:                    {len(still_missing)}')
    print(f'  RCT fetches this run:             {rct_fetches}')
    print(f'  RCT blocked/paused:               {rct_blocked}')
    print(f'  Entries with no extractable RCIN: {len(unresolved_no_rcin)}')
    if unresolved_no_rcin:
        print(f'    -> ids: {unresolved_no_rcin}')
    if unresolved_other:
        print(f'  Other failures ({len(unresolved_other)}):')
        for eid, rcin, reason in unresolved_other[:20]:
            print(f'    id={eid} rcin={rcin} reason={reason}')


if __name__ == '__main__':
    main()
