#!/usr/bin/env python3
"""Build leonardo-da-vinci/catalog.json.

Two parts:
  1. Curated painting list (~16 universally accepted paintings) with
     rich hand-entered metadata (date, medium, dimensions, location).
  2. Category crawl of Leonardo's drawings, codex folios, and manuscript
     pages via Commons category members (recursive, depth-limited).

Output: leonardo-da-vinci/catalog.json, wiki_works_raw.json
"""
import json, time, urllib.request, urllib.parse, re, html, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
COLL = os.path.dirname(HERE)
CATALOG = os.path.join(COLL, 'catalog.json')
RAW = os.path.join(COLL, 'wiki_works_raw.json')
COMMONS = 'https://commons.wikimedia.org/w/api.php'
UA = 'open-museum-leonardo/1.0 (https://github.com/nafSadh/open-museum; nafsadh@gmail.com)'

ISO_RE = re.compile(r'^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$')

# ── Part 1: curated paintings ────────────────────────────────────────────
CURATED = [
    {'title': 'Mona Lisa', 'title_original': 'La Gioconda', 'date': 'c. 1503–1519',
     'medium': 'Oil on poplar panel', 'dimensions': '77 × 53 cm',
     'current_location': 'Louvre, Paris', 'type': 'painting', 'era': 'late',
     'subject': 'portrait', 'attribution': 'accepted',
     'commons_filename': 'Mona_Lisa,_by_Leonardo_da_Vinci,_from_C2RMF_retouched.jpg',
     'wiki_slug': 'Mona_Lisa', 'famous': True},
    {'title': 'The Last Supper', 'title_original': 'Il Cenacolo', 'date': 'c. 1495–1498',
     'medium': 'Tempera on gesso, pitch and mastic', 'dimensions': '460 × 880 cm',
     'current_location': 'Santa Maria delle Grazie, Milan', 'type': 'painting', 'era': 'middle',
     'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Última_Cena_-_Da_Vinci_5.jpg',
     'wiki_slug': 'The_Last_Supper_(Leonardo)', 'famous': True},
    {'title': 'Virgin of the Rocks (Louvre version)', 'title_original': 'La Vergine delle rocce',
     'date': 'c. 1483–1486', 'medium': 'Oil on panel, transferred to canvas',
     'dimensions': '199 × 122 cm', 'current_location': 'Louvre, Paris',
     'type': 'painting', 'era': 'middle', 'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Leonardo_Da_Vinci_-_Vergine_delle_Rocce_(Louvre).jpg',
     'wiki_slug': 'Virgin_of_the_Rocks', 'famous': True},
    {'title': 'Virgin of the Rocks (London version)', 'date': 'c. 1495–1508',
     'medium': 'Oil on panel', 'dimensions': '189.5 × 120 cm',
     'current_location': 'National Gallery, London', 'type': 'painting', 'era': 'middle',
     'subject': 'religious', 'attribution': 'accepted (partly workshop)',
     'commons_filename': 'Leonardo_da_Vinci_Virgin_of_the_Rocks_(National_Gallery_London).jpg',
     'wiki_slug': 'Virgin_of_the_Rocks', 'famous': True},
    {'title': 'Lady with an Ermine', 'title_original': "Dama con l'ermellino",
     'date': 'c. 1489–1491', 'medium': 'Oil on walnut panel', 'dimensions': '54 × 39 cm',
     'current_location': 'Czartoryski Museum, Kraków', 'type': 'painting', 'era': 'middle',
     'subject': 'portrait', 'attribution': 'accepted',
     'commons_filename': 'Lady_with_an_Ermine_-_Leonardo_da_Vinci_(adjusted_levels).jpg',
     'wiki_slug': 'Lady_with_an_Ermine', 'famous': True},
    {'title': "Ginevra de' Benci", 'date': 'c. 1474–1478',
     'medium': 'Oil on panel', 'dimensions': '38.1 × 37 cm',
     'current_location': 'National Gallery of Art, Washington', 'type': 'painting',
     'era': 'early', 'subject': 'portrait', 'attribution': 'accepted',
     'commons_filename': "Leonardo_da_Vinci_-_Ginevra_de'_Benci_-_Google_Art_Project.jpg",
     'wiki_slug': 'Ginevra_de%27_Benci', 'famous': True},
    {'title': 'Annunciation', 'title_original': 'Annunciazione', 'date': 'c. 1472–1475',
     'medium': 'Oil and tempera on panel', 'dimensions': '98 × 217 cm',
     'current_location': 'Uffizi, Florence', 'type': 'painting', 'era': 'early',
     'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Leonardo_da_Vinci_-_Annunciazione_-_Google_Art_Project.jpg',
     'wiki_slug': 'Annunciation_(Leonardo)', 'famous': True},
    {'title': 'Benois Madonna', 'date': 'c. 1478–1480',
     'medium': 'Oil on canvas, transferred from panel', 'dimensions': '48 × 31 cm',
     'current_location': 'Hermitage Museum, St Petersburg', 'type': 'painting', 'era': 'early',
     'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Madonna_benois_01.jpg',
     'wiki_slug': 'Benois_Madonna', 'famous': True},
    {'title': 'Saint John the Baptist', 'date': 'c. 1513–1516',
     'medium': 'Oil on walnut wood', 'dimensions': '69 × 57 cm',
     'current_location': 'Louvre, Paris', 'type': 'painting', 'era': 'late',
     'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Leonardo_da_Vinci_-_Saint_John_the_Baptist_C2RMF_retouched.jpg',
     'wiki_slug': 'Saint_John_the_Baptist_(Leonardo)', 'famous': True},
    {'title': 'Virgin and Child with Saint Anne', 'date': 'c. 1503–1519',
     'medium': 'Oil on poplar panel', 'dimensions': '168 × 130 cm',
     'current_location': 'Louvre, Paris', 'type': 'painting', 'era': 'late',
     'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Leonardo_da_Vinci_-_Virgin_and_Child_with_St_Anne_C2RMF_retouched.jpg',
     'wiki_slug': 'The_Virgin_and_Child_with_Saint_Anne_(Leonardo)', 'famous': True},
    {'title': 'Madonna of the Carnation', 'date': 'c. 1478–1480',
     'medium': 'Oil on panel', 'dimensions': '62 × 47 cm',
     'current_location': 'Alte Pinakothek, Munich', 'type': 'painting', 'era': 'early',
     'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Madonna_of_the_Carnation_-_Leonardo_da_Vinci.jpg',
     'wiki_slug': 'Madonna_of_the_Carnation', 'famous': False},
    {'title': 'La Belle Ferronnière', 'date': 'c. 1490–1497',
     'medium': 'Oil on walnut panel', 'dimensions': '62 × 44 cm',
     'current_location': 'Louvre, Paris', 'type': 'painting', 'era': 'middle',
     'subject': 'portrait', 'attribution': 'accepted',
     'commons_filename': 'La_belle_ferronnière,Leonardo_da_Vinci_-_Louvre.jpg',
     'wiki_slug': 'La_Belle_Ferronni%C3%A8re', 'famous': True},
    {'title': 'Portrait of a Musician', 'date': 'c. 1483–1487',
     'medium': 'Oil on walnut panel', 'dimensions': '43 × 31 cm',
     'current_location': 'Pinacoteca Ambrosiana, Milan', 'type': 'painting', 'era': 'middle',
     'subject': 'portrait', 'attribution': 'accepted (partly workshop)',
     'commons_filename': 'Leonardo_da_Vinci_-_Portrait_of_a_Musician_-_Pinacoteca_Ambrosiana.jpg',
     'wiki_slug': 'Portrait_of_a_Musician', 'famous': False},
    {'title': 'Saint Jerome in the Wilderness', 'date': 'c. 1480–1490',
     'medium': 'Oil and tempera on walnut panel', 'dimensions': '103 × 75 cm',
     'current_location': 'Vatican Pinacoteca', 'type': 'painting', 'era': 'early',
     'subject': 'religious', 'attribution': 'accepted (unfinished)',
     'commons_filename': 'Saint_Jerome_Leonardo_-_image_only_(Q972196).jpg',
     'wiki_slug': 'Saint_Jerome_in_the_Wilderness_(Leonardo)', 'famous': True},
    {'title': 'Adoration of the Magi', 'date': 'c. 1481–1482',
     'medium': 'Oil on panel', 'dimensions': '246 × 243 cm',
     'current_location': 'Uffizi, Florence', 'type': 'painting', 'era': 'early',
     'subject': 'religious', 'attribution': 'accepted (unfinished)',
     'commons_filename': 'Leonardo_da_Vinci_-_Adorazione_dei_Magi_-_Google_Art_Project.jpg',
     'wiki_slug': 'Adoration_of_the_Magi_(Leonardo)', 'famous': False},
    {'title': 'Madonna Litta', 'date': 'c. 1490',
     'medium': 'Tempera on canvas (transferred from panel)', 'dimensions': '42 × 33 cm',
     'current_location': 'Hermitage Museum, St Petersburg', 'type': 'painting', 'era': 'middle',
     'subject': 'religious', 'attribution': 'attributed (partly workshop)',
     'commons_filename': 'Leonardo_da_Vinci_attributed_-_Madonna_Litta.jpg',
     'wiki_slug': 'Madonna_Litta', 'famous': False},
    # Standout drawings / studies
    {'title': 'Vitruvian Man', 'title_original': "L'uomo vitruviano",
     'date': 'c. 1490', 'medium': 'Pen and ink on paper', 'dimensions': '34.4 × 25.5 cm',
     'current_location': "Gallerie dell'Accademia, Venice", 'type': 'drawing', 'era': 'middle',
     'subject': 'study', 'attribution': 'accepted',
     'commons_filename': 'Da_Vinci_Vitruve_Luc_Viatour.jpg',
     'wiki_slug': 'Vitruvian_Man', 'famous': True},
    {'title': 'Head of a Woman (La Scapigliata)', 'date': 'c. 1500–1510',
     'medium': 'Umber, green, and white pigments on panel', 'dimensions': '24.7 × 21 cm',
     'current_location': 'Galleria Nazionale, Parma', 'type': 'painting', 'era': 'late',
     'subject': 'study', 'attribution': 'accepted',
     'commons_filename': 'La_Scapigliata_di_Leonardo_Da_Vinci.jpg',
     'wiki_slug': 'La_Scapigliata', 'famous': True},
    {'title': 'Portrait of a Man in Red Chalk', 'date': 'c. 1512',
     'medium': 'Red chalk on paper', 'dimensions': '33.3 × 21.4 cm',
     'current_location': 'Royal Library, Turin', 'type': 'drawing', 'era': 'late',
     'subject': 'portrait', 'attribution': 'attributed',
     'commons_filename': 'Leonardo_da_Vinci_-_presumed_self-portrait_-_lossless.png',
     'wiki_slug': 'Portrait_of_a_Man_in_Red_Chalk', 'famous': True},
    {'title': 'Study of a Tuscan Landscape', 'date': '1473-08-05',
     'medium': 'Pen and ink on paper', 'dimensions': '19 × 28.5 cm',
     'current_location': 'Uffizi, Florence', 'type': 'drawing', 'era': 'early',
     'subject': 'landscape', 'attribution': 'accepted',
     'commons_filename': 'Paisagem_do_Arno_-_Leonardo_da_Vinci.jpg',
     'wiki_slug': 'Paesaggio_(Leonardo)', 'famous': True},
]

# ── Part 2: category crawl ───────────────────────────────────────────────
# Each entry: (category name, type label, subject, max_depth)
# max_depth limits recursion into sub-categories.
SEED_CATS = [
    # Paintings are handled entirely by the curated list above — Commons
    # painting categories are dominated by school-of / studio-of pieces
    # and multiple high-res scans of the same few works. Not useful here.
    ('Drawings by Leonardo da Vinci',               'drawing',      None,        2),
    ('Studies by Leonardo da Vinci',                'study',        'study',     2),
    ('Codex on the Flight of Birds',                'codex_folio',  'codex',     1),
    ('Manuscripts by Leonardo da Vinci',            'codex_folio',  'codex',     1),
]

IMAGE_EXT = re.compile(r'\.(jpg|jpeg|png|tif|tiff|gif)$', re.I)

# Category / filename exclusions — these subcategories and files are
# overwhelmingly noise (details, copies, follower works, gallery photos,
# and modern 3D reconstructions of Leonardo's invention sketches).
CAT_EXCLUDE = re.compile(
    r'\b(?:'
    r'details?\s+of|'
    r'copies?\s+of|copies?\s+after|copy\s+of|'
    r'photographs?\s+of|photos?\s+of|infrared|'
    r'sculptures?\s+(?:of|after)|'
    r'postage|stamps?\s+featuring|stamps?\s+of\s+|'
    r'postcards?|replicas?|'
    r'followers?\s+of|school\s+of|studio\s+of|workshop\s+of|'
    r'(?:attributed\s+to|after)\s+leonardo|'
    r'room\s+\d|gallery|museum\s+of|'
    r'lucan\s+portrait|'
    r'sala\s+delle|'
    r'videos?\s+of|animations?\s+of|drawings?\s+of\s+leonardo|'
    r'statues?\s+of\s+leonardo|'
    r'bust\s+of\s+leonardo|'
    # Modern reconstructions of Leonardo's inventions — not drawings by him
    r'models?\s+of\s+inventions|inventions?\s+of\s+leonardo|'
    # Subcategories of individual canonical works — we already have those curated
    r'vitruvian\s+man\s+by|last\s+supper\s+by|mona\s+lisa\s+by|'
    r'virgin\s+of\s+the\s+rocks\s+by|lady\s+with\s+an\s+ermine\s+by|'
    r'annunciation\s+by|adoration\s+of\s+the\s+magi\s+by|'
    r'so-called\s+self-portrait|presumed\s+self-portrait'
    r')\b', re.I)

# Filename exclusions — patterns in the filename that indicate it's a
# detail shot, gallery photo, reproduction, or "after Leonardo" work.
FN_EXCLUDE = re.compile(
    r'(?:^|[_\-\s])(?:'
    r'detail|details|cropped_detail|close_up|'
    r'postage|stamp_|_stamp|'
    r'sculpture_of_|statue_of_|bust_of_|monument_to_|'
    r'_room_\d|_gallery_|_museum_|'
    r'infrared|reflectogram|x-ray|xray|'
    r'postcard|poster_|'
    r'lucan_portrait|'
    r'all_works_of|paintings_\d+|'
    r'(?:koblenz|paris|firenze|milano|napoli)_\d|'
    r'copy_after|copia_di|copie_d|école_de|schule_des|'
    r'school_of|studio_of|after_leonardo|workshop_of|'
    r'da_vinci_workshop|vinci_machine|leonardo_machine'
    r')', re.I)


def api_get(params):
    params = {**params, 'format': 'json'}
    url = f'{COMMONS}?{urllib.parse.urlencode(params)}'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def crawl_category(cat, depth, max_depth, files, visited):
    if cat in visited or depth > max_depth:
        return
    # Skip exclusion-match subcategories (but allow the root seed through)
    if depth > 0 and CAT_EXCLUDE.search(cat):
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
                if IMAGE_EXT.search(fn) and not FN_EXCLUDE.search(fn):
                    files.setdefault(fn, cat)
            elif t.startswith('Category:') and depth < max_depth:
                crawl_category(t[9:], depth + 1, max_depth, files, visited)
        cont = resp.get('continue', {}).get('cmcontinue')
        if not cont:
            break
        time.sleep(0.3)


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
    if not s:
        return ''
    s = re.sub(r'<[^>]+>', '', s)
    s = html.unescape(s).strip()
    return s


def clean_date(raw):
    """Strip Wikidata QS annotations + EXIF upload timestamps, cap at 1520."""
    if not raw:
        return ''
    s = str(raw).strip()
    s = re.sub(r'\s*date\s*QS[:=].*$', '', s, flags=re.I)
    s = re.sub(r'QS[:=]P\d+.*$', '', s)
    s = re.sub(r'\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\b', '', s)
    s = re.sub(r'https?://\S+', '', s)
    s = re.sub(r'[+]\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z/\d+', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    # Reject implausible dates (Leonardo died 1519; allow up to 1525 for posthumous)
    y = re.findall(r'1[45]\d\d|15[0-2]\d', s)
    if not y:
        return ''
    max_y = max(int(x) for x in y)
    if max_y > 1525:
        return ''
    return s


def parse_date(s):
    if not s:
        return None, None, False
    s = str(s).strip()
    if ISO_RE.match(s):
        y = int(ISO_RE.match(s).group(1))
        return y, y, False
    circa = bool(re.search(r'\bc\.|\bcirca\b|\bca\.', s.lower()))
    m = re.search(r'(1[45]\d\d)s\b', s)
    if m:
        b = int(m.group(1))
        return b, b + 9, circa
    s_clean = re.sub(r'\bc\.\s*|\bcirca\s*|\bca\.\s*', '', s, flags=re.I)
    m2 = re.search(r'(1[45]\d\d)\s*[–\-]\s*(\d{2})(?!\d)', s_clean)
    years = [int(y) for y in re.findall(r'1[45]\d\d', s_clean)]
    if m2:
        base = int(m2.group(1))
        end_full = (base // 100) * 100 + int(m2.group(2))
        if end_full < base:
            end_full += 100
        return min(years + [end_full]), max(years + [end_full]), circa
    if not years:
        return None, None, circa
    return min(years), max(years), circa


def derive_title(fn, object_name):
    """Build a readable title from the Commons filename or ObjectName."""
    if object_name and len(object_name) > 4 and len(object_name) < 140:
        return object_name
    # strip extension, replace underscores, strip Leonardo / da Vinci noise
    t = re.sub(IMAGE_EXT, '', fn).replace('_', ' ')
    t = re.sub(r'[-–]\s*Google Art Project\s*$', '', t, flags=re.I).strip()
    t = re.sub(r'\s*-?\s*WGA\d+\s*$', '', t).strip()
    t = re.sub(r'\s*\(Q\d+\)\s*', ' ', t).strip()
    t = re.sub(r'Leonardo(\s+Da|\s+da)?(\s+Vinci)?\s*[-–—:,]?\s*', '', t, flags=re.I).strip()
    t = re.sub(r'Da\s+Vinci\s*[-–—:,]?\s*', '', t, flags=re.I).strip()
    t = re.sub(r'\s{2,}', ' ', t)
    return t.strip(' -–—:,')


def subject_from_category(cat):
    c = cat.lower()
    if 'portrait' in c:
        return 'portrait'
    if 'religi' in c or 'madonna' in c or 'christ' in c or 'biblical' in c or 'saint' in c:
        return 'religious'
    if 'anat' in c:
        return 'study'
    if 'landscape' in c:
        return 'landscape'
    if 'horse' in c or 'animal' in c:
        return 'study'
    if 'codex' in c or 'manuscript' in c:
        return 'codex'
    if 'map' in c:
        return 'study'
    return 'study'


def era_from_date(y_s):
    if y_s is None:
        return 'unknown'
    if y_s < 1485:
        return 'early'
    if y_s < 1500:
        return 'middle'
    return 'late'


def main():
    # Part 1: build curated entries
    curated_fnames = {w['commons_filename'] for w in CURATED}

    print(f"Curated list: {len(CURATED)} entries")

    # Part 2: crawl categories
    print("\nCrawling Commons categories (recursive)...")
    files_with_source = {}  # fn -> source category
    file_type_hint = {}     # fn -> type label from seed category
    file_subject_hint = {}
    visited_cats = set()
    for cat, type_label, subject_hint, max_depth in SEED_CATS:
        before = len(files_with_source)
        crawl_category(cat, 0, max_depth, files_with_source, visited_cats)
        new = len(files_with_source) - before
        print(f"  {cat:<40} +{new} files (total so far: {len(files_with_source)})")
        # Assign type hints for files first discovered in this seed
        # (won't override earlier seeds)
        for fn, src in files_with_source.items():
            if fn not in file_type_hint:
                file_type_hint[fn] = type_label
                file_subject_hint[fn] = subject_hint

    # Drop curated filenames from the crawl (curated wins)
    crawl_fnames = [fn for fn in files_with_source if fn not in curated_fnames]
    print(f"\nTotal crawled files (minus curated): {len(crawl_fnames)}")

    # Part 3: batch metadata fetch for everything
    all_fnames = list(curated_fnames) + crawl_fnames
    print(f"\nFetching imageinfo for {len(all_fnames)} files in batches of 50...")
    info = {}
    for i in range(0, len(all_fnames), 50):
        batch = all_fnames[i:i + 50]
        try:
            info.update(fetch_imageinfo_batch(batch))
        except Exception as e:
            print(f"  batch {i}: {e}", file=sys.stderr)
        if (i // 50) % 5 == 0:
            print(f"  batch {i//50 + 1} ({i + len(batch)}/{len(all_fnames)})")
        time.sleep(0.8)
    print(f"Resolved {len(info)}/{len(all_fnames)} files")

    catalog = []
    idx = 1

    # Curated entries
    for w in CURATED:
        entry = dict(w)
        entry['id'] = idx
        idx += 1
        meta = info.get(w['commons_filename'].replace(' ', '_'))
        if meta:
            entry['image_url']   = meta['image_url']
            entry['thumb_url']   = meta['thumb_url']
            entry['commons_page']= meta['commons_page']
            entry['image_width'] = meta['image_width']
            entry['image_height']= meta['image_height']
            entry['mime']        = meta['mime']
        if w.get('wiki_slug'):
            entry['provenance_url'] = f"https://en.wikipedia.org/wiki/{w['wiki_slug']}"
        elif meta:
            entry['provenance_url'] = meta['commons_page']
        entry.pop('wiki_slug', None)
        # parse date
        d = entry.get('date', '')
        y_s, y_e, circa = parse_date(d)
        entry['year_start'] = y_s
        entry['year_end']   = y_e
        entry['circa']      = circa
        catalog.append(entry)

    # Crawled entries
    for fn in crawl_fnames:
        meta = info.get(fn)
        if not meta:
            continue
        raw_date = clean_date(meta.get('_date_raw', ''))
        y_s, y_e, circa = parse_date(raw_date) if raw_date else (None, None, False)
        type_hint = file_type_hint.get(fn, 'drawing')
        src_cat = files_with_source.get(fn, '')
        subj = file_subject_hint.get(fn) or subject_from_category(src_cat)
        entry = {
            'id': idx,
            'title': derive_title(fn, meta.get('_object_name', '')),
            'date': raw_date,
            'type': type_hint,
            'subject': subj,
            'era': era_from_date(y_s),
            'attribution': 'accepted' if 'Leonardo' in src_cat else 'attributed',
            'commons_filename': fn,
            'image_url': meta['image_url'],
            'thumb_url': meta['thumb_url'],
            'commons_page': meta['commons_page'],
            'provenance_url': meta['commons_page'],
            'image_width': meta['image_width'],
            'image_height': meta['image_height'],
            'mime': meta['mime'],
            'year_start': y_s,
            'year_end': y_e,
            'circa': circa,
            'famous': False,
            'harvest_method': f'commons_category:{src_cat}',
        }
        idx += 1
        catalog.append(entry)

    # Write output
    with open(RAW, 'w', encoding='utf-8') as f:
        json.dump({'curated': CURATED,
                   'crawled_sources': [c[0] for c in SEED_CATS]}, f,
                  ensure_ascii=False, indent=2)
    with open(CATALOG, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    # Summary
    with_img = sum(1 for e in catalog if e.get('image_url'))
    by_type = {}
    for e in catalog:
        t = e.get('type', '?')
        by_type[t] = by_type.get(t, 0) + 1
    print(f"\n=== Summary ===")
    print(f"  Total entries: {len(catalog)} ({with_img} with image)")
    for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t:<16} {n}")


if __name__ == '__main__':
    main()
