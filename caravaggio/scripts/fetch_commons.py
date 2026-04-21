#!/usr/bin/env python3
"""Generic artist-collection builder via Commons category crawl.

Usage: python3 fetch_artist.py <artist-slug>

Reads config from leonardo-da-vinci/scripts/fetch_commons.py's pattern —
each artist has seed categories, exclusion rules, optional curated list.
"""
import json, time, urllib.request, urllib.parse, re, html, os, sys

COMMONS = 'https://commons.wikimedia.org/w/api.php'
UA = 'open-museum-builder/1.0 (https://github.com/nafSadh/open-museum; nafsadh@gmail.com)'
ROOT = '/Users/nafsadh/src/open-museum'

ISO_RE = re.compile(r'^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$')
IMAGE_EXT = re.compile(r'\.(jpg|jpeg|png|tif|tiff|gif)$', re.I)

# Shared category-noise filter (details, copies, stamps, etc.)
CAT_EXCLUDE_BASE = (
    r'details?\s+of|copies?\s+of|copies?\s+after|copy\s+of|'
    r'photographs?\s+of|photos?\s+of|infrared|reflectograms?|'
    r'sculptures?\s+(?:of|after)|monuments?\s+to|bust\s+of|statue\s+of|'
    r'postage|stamps?\s+featuring|stamps?\s+of\s+|postcards?|replicas?|'
    r'followers?\s+of|school\s+of|studio\s+of|workshop\s+of|'
    r'(?:attributed\s+to|after)\s+\w+|'
    r'room\s+\d|gallery|museum\s+of|exhibition\s+of|'
    r'videos?\s+of|animations?\s+of|'
    r'birthplace\s+of|tomb\s+of|grave\s+of|'
    r'portraits?\s+of\s+\w+|'  # excludes "Portraits of Caravaggio" (photos of him)
    r'books?\s+by|books?\s+about'
)

FN_EXCLUDE_BASE = (
    r'detail|details|cropped_detail|close_up|'
    r'postage|stamp_|_stamp|'
    r'sculpture_of_|statue_of_|bust_of_|monument_to_|'
    r'_room_\d|_gallery_|_museum_|tomb_of|grave_of|'
    r'infrared|reflectogram|x-ray|xray|'
    r'postcard|poster_|'
    r'copy_after|copia_di|copie_d|école_de|schule_des|'
    r'school_of|studio_of|workshop_of|'
    r'birthplace|tombstone'
)

# Artist configs — each defines seed cats, custom exclusions,
# optional curated painting list, and metadata.
CONFIGS = {
    'mary-cassatt': {
        'artist_name': 'Mary Cassatt',
        'artist_name_key': 'cassatt',
        'born': 1844, 'died': 1926,
        'max_year': 1926,
        'seeds': [
            ('Mary Cassatt',                 None,        None,        2),
            ('Paintings by Mary Cassatt',    'painting',  None,        2),
            ('Prints by Mary Cassatt',       'print',     None,        2),
            ('Drawings by Mary Cassatt',     'drawing',   None,        2),
        ],
        'extra_cat_exclude': r'children_of_mary_cassatt|portraits_of_mary_cassatt',
        'extra_fn_exclude':  r'photograph_of|photo_of|mary_cassatt_\d{4}',
    },
    'caravaggio': {
        'artist_name': 'Caravaggio',
        'artist_name_key': 'caravaggio',
        'born': 1571, 'died': 1610,
        'max_year': 1615,
        'seeds': [
            ('Paintings by Caravaggio',      'painting',  None,        2),
        ],
        # drop "portraits of Caravaggio" (photos of him), and any
        # "attributed to" or "follower of" subcats
        'extra_cat_exclude': r'portraits?\s+of\s+caravaggio|attributed\s+to\s+caravaggio',
        'extra_fn_exclude':  r'caravaggio_dipinto|_follower',
    },
    'abanindranath-tagore': {
        'artist_name': 'Abanindranath Tagore',
        'artist_name_key': 'tagore',
        'born': 1871, 'died': 1951,
        'max_year': 1951,
        'seeds': [
            ('Paintings by Abanindranath Tagore', 'painting', None,   2),
            ('Abanindranath Tagore',              None,       None,   2),
        ],
        'extra_cat_exclude': r'portraits?\s+of\s+abanindranath',
        'extra_fn_exclude':  r'photograph_of|photo_of|tagore_\d{4}',
    },
}


def api_get(params, retries=2):
    params = {**params, 'format': 'json'}
    url = f'{COMMONS}?{urllib.parse.urlencode(params)}'
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(5)


def crawl_category(cat, depth, max_depth, files, visited, cat_exclude, fn_exclude, type_hint):
    if cat in visited or depth > max_depth:
        return
    if depth > 0 and cat_exclude.search(cat):
        return
    visited.add(cat)
    cont = None
    while True:
        params = {'action': 'query', 'list': 'categorymembers',
                  'cmtitle': f'Category:{cat}', 'cmlimit': '500',
                  'cmtype': 'file|subcat'}
        if cont:
            params['cmcontinue'] = cont
        try:
            resp = api_get(params)
        except Exception as e:
            print(f"  crawl error '{cat}': {e}", file=sys.stderr)
            return
        for m in resp.get('query', {}).get('categorymembers', []):
            t = m.get('title', '')
            if t.startswith('File:'):
                fn = t[5:].replace(' ', '_')
                if IMAGE_EXT.search(fn) and not fn_exclude.search(fn):
                    if fn not in files:
                        files[fn] = {'source_cat': cat, 'type_hint': type_hint}
            elif t.startswith('Category:') and depth < max_depth:
                crawl_category(t[9:], depth + 1, max_depth, files, visited,
                              cat_exclude, fn_exclude, type_hint)
        cont = resp.get('continue', {}).get('cmcontinue')
        if not cont:
            break
        time.sleep(0.2)


def fetch_imageinfo_batch(filenames):
    titles = '|'.join(f'File:{fn}' for fn in filenames)
    resp = api_get({
        'action': 'query', 'titles': titles,
        'prop': 'imageinfo',
        'iiprop': 'url|size|mime|extmetadata',
        'iiurlwidth': '800',
    })
    results = {}
    for pid, p in resp.get('query', {}).get('pages', {}).items():
        if int(pid) < 0:
            continue
        raw = p.get('title', '')[5:].replace(' ', '_')
        ii = (p.get('imageinfo') or [{}])[0]
        if not ii.get('url') or not ii.get('mime', '').startswith('image/'):
            continue
        ext = ii.get('extmetadata', {}) or {}
        results[raw] = {
            'image_url': ii['url'],
            'thumb_url': ii.get('thumburl', ''),
            'commons_page': ii.get('descriptionurl', ''),
            'image_width': ii.get('width'),
            'image_height': ii.get('height'),
            'mime': ii.get('mime', ''),
            '_date_raw': strip_html(
                (ext.get('DateTimeOriginal', {}) or {}).get('value', '') or
                (ext.get('DateTime', {}) or {}).get('value', '')),
            '_object_name': strip_html(
                (ext.get('ObjectName', {}) or {}).get('value', '')),
        }
    return results


def strip_html(s):
    if not s: return ''
    s = re.sub(r'<[^>]+>', '', s)
    return html.unescape(s).strip()


def clean_date(raw, max_year):
    if not raw: return ''
    s = str(raw).strip()
    s = re.sub(r'\s*date\s*QS[:=].*$', '', s, flags=re.I)
    s = re.sub(r'QS[:=]P\d+.*$', '', s)
    s = re.sub(r'\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\b', '', s)
    s = re.sub(r'https?://\S+', '', s)
    s = re.sub(r'[+]\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z/\d+', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    y = re.findall(r'1[4-9]\d\d|20\d\d', s)
    if not y: return ''
    if max(int(x) for x in y) > max_year + 5:
        return ''
    return s


def parse_date(s):
    if not s: return None, None, False
    s = str(s).strip()
    if ISO_RE.match(s):
        y = int(ISO_RE.match(s).group(1))
        return y, y, False
    circa = bool(re.search(r'\bc\.|\bcirca\b|\bca\.', s.lower()))
    m = re.search(r'(1[4-9]\d\d|20\d\d)s\b', s)
    if m:
        b = int(m.group(1)); return b, b+9, circa
    s_clean = re.sub(r'\bc\.\s*|\bcirca\s*|\bca\.\s*', '', s, flags=re.I)
    m2 = re.search(r'(1[4-9]\d\d|20\d\d)\s*[–\-]\s*(\d{2})(?!\d)', s_clean)
    years = [int(y) for y in re.findall(r'1[4-9]\d\d|20\d\d', s_clean)]
    if m2:
        base = int(m2.group(1))
        end_full = (base//100)*100 + int(m2.group(2))
        if end_full < base: end_full += 100
        return min(years+[end_full]), max(years+[end_full]), circa
    if not years: return None, None, circa
    return min(years), max(years), circa


def derive_title(fn, object_name, artist_name):
    if object_name and 4 < len(object_name) < 140:
        return object_name
    t = re.sub(IMAGE_EXT, '', fn).replace('_', ' ')
    t = re.sub(r'[-–]\s*Google Art Project\s*$', '', t, flags=re.I).strip()
    t = re.sub(r'\s*-?\s*WGA\d+\s*$', '', t).strip()
    t = re.sub(r'\s*\(Q\d+\)\s*', ' ', t).strip()
    # Strip artist name from title
    for tok in artist_name.split():
        if len(tok) >= 4:
            t = re.sub(rf'\b{re.escape(tok)}\b\s*[-–—:,]?\s*', '', t, flags=re.I).strip()
    t = re.sub(r'\s{2,}', ' ', t)
    return t.strip(' -–—:,').strip()


def era_from_date(y_s, born, died):
    if y_s is None: return 'unknown'
    career = died - born
    early_end = born + career // 3 + 20
    late_start = died - career // 3
    if y_s < early_end: return 'early'
    if y_s < late_start: return 'middle'
    return 'late'


def subject_from_category(cat):
    c = (cat or '').lower()
    if 'portrait' in c: return 'portrait'
    if 'religi' in c or 'madonna' in c or 'christ' in c or 'saint' in c or 'biblical' in c:
        return 'religious'
    if 'still_life' in c or 'still life' in c: return 'still_life'
    if 'landscape' in c: return 'landscape'
    if 'mother' in c or 'child' in c: return 'mother_child'
    if 'mytho' in c: return 'mythological'
    if 'print' in c: return 'print'
    return 'genre'


def build(artist_slug):
    cfg = CONFIGS[artist_slug]
    out_dir = os.path.join(ROOT, artist_slug)
    os.makedirs(out_dir, exist_ok=True)

    # Build filters
    cat_exc = re.compile(r'\b(?:' + CAT_EXCLUDE_BASE
        + (('|' + cfg.get('extra_cat_exclude','')) if cfg.get('extra_cat_exclude') else '')
        + r')\b', re.I)
    fn_exc = re.compile(r'(?:^|[_\-\s])(?:' + FN_EXCLUDE_BASE
        + (('|' + cfg.get('extra_fn_exclude','')) if cfg.get('extra_fn_exclude') else '')
        + r')', re.I)

    # Crawl
    print(f"[{artist_slug}] crawling Commons...")
    files = {}
    visited = set()
    for cat, type_label, subject_hint, max_depth in cfg['seeds']:
        before = len(files)
        crawl_category(cat, 0, max_depth, files, visited, cat_exc, fn_exc, type_label)
        print(f"  {cat:<45} +{len(files)-before} files (total {len(files)})")

    # Fetch metadata
    fnames = list(files.keys())
    print(f"\n[{artist_slug}] fetching imageinfo for {len(fnames)} files...")
    info = {}
    for i in range(0, len(fnames), 50):
        batch = fnames[i:i+50]
        try:
            info.update(fetch_imageinfo_batch(batch))
        except Exception as e:
            print(f"  batch {i}: {e}", file=sys.stderr)
        time.sleep(0.8)
    print(f"  resolved {len(info)}/{len(fnames)}")

    # Build catalog
    catalog = []
    idx = 1
    for fn, meta in files.items():
        inf = info.get(fn)
        if not inf: continue
        raw_date = clean_date(inf.get('_date_raw',''), cfg['max_year'])
        y_s, y_e, circa = parse_date(raw_date)
        entry = {
            'id': idx,
            'title': derive_title(fn, inf.get('_object_name',''), cfg['artist_name']),
            'date': raw_date,
            'type': meta.get('type_hint') or 'painting',
            'subject': subject_from_category(meta.get('source_cat')),
            'era': era_from_date(y_s, cfg['born'], cfg['died']),
            'attribution': 'accepted',
            'commons_filename': fn,
            'image_url': inf['image_url'],
            'thumb_url': inf['thumb_url'],
            'commons_page': inf['commons_page'],
            'provenance_url': inf['commons_page'],
            'image_width': inf['image_width'],
            'image_height': inf['image_height'],
            'mime': inf['mime'],
            'year_start': y_s,
            'year_end': y_e,
            'circa': circa,
            'famous': False,
            'harvest_method': f"commons_category:{meta.get('source_cat','')}",
        }
        idx += 1
        catalog.append(entry)

    # Add title_disambig for duplicates
    from collections import Counter
    titles = [e['title'].lower().strip() for e in catalog if e['title']]
    dup = {t for t,c in Counter(titles).items() if c > 1}
    for e in catalog:
        if e['title'].lower().strip() in dup:
            parts = []
            if e.get('year_start'):
                parts.append(str(e['year_start']) if e['year_start']==e['year_end'] else f"{e['year_start']}–{e['year_end']}")
            if e.get('commons_filename'):
                # use a short id suffix
                parts.append(f"#{e['id']}")
            if parts:
                e['title_disambig'] = ' · '.join(parts)

    with open(os.path.join(out_dir, 'catalog.json'), 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, 'wiki_works_raw.json'), 'w', encoding='utf-8') as f:
        json.dump({'seeds': [s[0] for s in cfg['seeds']]}, f, ensure_ascii=False, indent=2)

    # Summary
    from collections import Counter as C2
    by_type = C2(e.get('type') for e in catalog)
    by_era = C2(e.get('era') for e in catalog)
    print(f"\n[{artist_slug}] === Summary ===")
    print(f"  entries: {len(catalog)}")
    print(f"  by_type: {dict(by_type)}")
    print(f"  by_era:  {dict(by_era)}")


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in CONFIGS:
        print(f"Usage: {sys.argv[0]} <{'|'.join(CONFIGS)}>")
        sys.exit(1)
    build(sys.argv[1])
