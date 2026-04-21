#!/usr/bin/env python3
"""Build leonardo-da-vinci/catalog.json from a curated list of works.

Leonardo's painted output is small (~15 uncontested) and heavily
disputed for the rest; a simple list scrape produces noise. This
script instead uses a hand-curated list of widely-accepted works
plus famous drawings, and resolves Commons metadata for each.

Outputs: leonardo-da-vinci/catalog.json
Also writes wiki_works_raw.json with the curated source list for
reproducibility.
"""
import json, time, urllib.request, urllib.parse, re, html, os

CATALOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'catalog.json')
RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'wiki_works_raw.json')
COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
UA = 'open-museum-leonardo/1.0 (https://github.com/nafSadh/open-museum; nafsadh@gmail.com)'

# Canonical Leonardo paintings + famous drawings.
# Each entry: commons_filename (exact, as on Commons) + Wikipedia article slug.
# Attribution classifications follow Zöllner, *Leonardo da Vinci: Complete
# Paintings and Drawings* (2019).
WORKS = [
    # --- Paintings (attribution: accepted) ---
    {'id': 1, 'title': 'Mona Lisa', 'title_original': 'La Gioconda', 'date': 'c. 1503–1519',
     'medium': 'Oil on poplar panel', 'dimensions': '77 × 53 cm',
     'current_location': 'Louvre, Paris', 'type': 'painting', 'era': 'late',
     'subject': 'portrait', 'attribution': 'accepted',
     'commons_filename': 'Mona_Lisa,_by_Leonardo_da_Vinci,_from_C2RMF_retouched.jpg',
     'wiki_slug': 'Mona_Lisa'},
    {'id': 2, 'title': 'The Last Supper', 'title_original': 'Il Cenacolo', 'date': 'c. 1495–1498',
     'medium': 'Tempera on gesso, pitch and mastic', 'dimensions': '460 × 880 cm',
     'current_location': 'Santa Maria delle Grazie, Milan', 'type': 'painting', 'era': 'middle',
     'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Última_Cena_-_Da_Vinci_5.jpg',
     'wiki_slug': 'The_Last_Supper_(Leonardo)'},
    {'id': 3, 'title': 'Virgin of the Rocks (Louvre version)', 'title_original': 'La Vergine delle rocce',
     'date': 'c. 1483–1486', 'medium': 'Oil on panel, transferred to canvas',
     'dimensions': '199 × 122 cm', 'current_location': 'Louvre, Paris',
     'type': 'painting', 'era': 'middle', 'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Leonardo_Da_Vinci_-_Vergine_delle_Rocce_(Louvre).jpg',
     'wiki_slug': 'Virgin_of_the_Rocks'},
    {'id': 4, 'title': 'Virgin of the Rocks (London version)', 'date': 'c. 1495–1508',
     'medium': 'Oil on panel', 'dimensions': '189.5 × 120 cm',
     'current_location': 'National Gallery, London', 'type': 'painting', 'era': 'middle',
     'subject': 'religious', 'attribution': 'accepted (partly workshop)',
     'commons_filename': 'Leonardo_da_Vinci_Virgin_of_the_Rocks_(National_Gallery_London).jpg',
     'wiki_slug': 'Virgin_of_the_Rocks'},
    {'id': 5, 'title': 'Lady with an Ermine', 'title_original': 'Dama con l\'ermellino',
     'date': 'c. 1489–1491', 'medium': 'Oil on walnut panel', 'dimensions': '54 × 39 cm',
     'current_location': 'Czartoryski Museum, Kraków', 'type': 'painting', 'era': 'middle',
     'subject': 'portrait', 'attribution': 'accepted',
     'commons_filename': 'Lady_with_an_Ermine_-_Leonardo_da_Vinci_(adjusted_levels).jpg',
     'wiki_slug': 'Lady_with_an_Ermine'},
    {'id': 6, 'title': 'Ginevra de\' Benci', 'date': 'c. 1474–1478',
     'medium': 'Oil on panel', 'dimensions': '38.1 × 37 cm',
     'current_location': 'National Gallery of Art, Washington', 'type': 'painting',
     'era': 'early', 'subject': 'portrait', 'attribution': 'accepted',
     'commons_filename': 'Leonardo_da_Vinci_-_Ginevra_de\'_Benci_-_Google_Art_Project.jpg',
     'wiki_slug': 'Ginevra_de%27_Benci'},
    {'id': 7, 'title': 'Annunciation', 'title_original': 'Annunciazione', 'date': 'c. 1472–1475',
     'medium': 'Oil and tempera on panel', 'dimensions': '98 × 217 cm',
     'current_location': 'Uffizi, Florence', 'type': 'painting', 'era': 'early',
     'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Leonardo_da_Vinci_-_Annunciazione_-_Google_Art_Project.jpg',
     'wiki_slug': 'Annunciation_(Leonardo)'},
    {'id': 8, 'title': 'Benois Madonna', 'date': 'c. 1478–1480',
     'medium': 'Oil on canvas, transferred from panel', 'dimensions': '48 × 31 cm',
     'current_location': 'Hermitage Museum, St Petersburg', 'type': 'painting', 'era': 'early',
     'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Madonna_benois_01.jpg',
     'wiki_slug': 'Benois_Madonna'},
    {'id': 9, 'title': 'Saint John the Baptist', 'date': 'c. 1513–1516',
     'medium': 'Oil on walnut wood', 'dimensions': '69 × 57 cm',
     'current_location': 'Louvre, Paris', 'type': 'painting', 'era': 'late',
     'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Leonardo_da_Vinci_-_Saint_John_the_Baptist_C2RMF_retouched.jpg',
     'wiki_slug': 'Saint_John_the_Baptist_(Leonardo)'},
    {'id': 10, 'title': 'Virgin and Child with Saint Anne', 'date': 'c. 1503–1519',
     'medium': 'Oil on poplar panel', 'dimensions': '168 × 130 cm',
     'current_location': 'Louvre, Paris', 'type': 'painting', 'era': 'late',
     'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Leonardo_da_Vinci_-_Virgin_and_Child_with_St_Anne_C2RMF_retouched.jpg',
     'wiki_slug': 'The_Virgin_and_Child_with_Saint_Anne_(Leonardo)'},
    {'id': 11, 'title': 'Madonna of the Carnation', 'date': 'c. 1478–1480',
     'medium': 'Oil on panel', 'dimensions': '62 × 47 cm',
     'current_location': 'Alte Pinakothek, Munich', 'type': 'painting', 'era': 'early',
     'subject': 'religious', 'attribution': 'accepted',
     'commons_filename': 'Madonna_of_the_Carnation_-_Leonardo_da_Vinci.jpg',
     'wiki_slug': 'Madonna_of_the_Carnation'},
    {'id': 12, 'title': 'La Belle Ferronnière', 'date': 'c. 1490–1497',
     'medium': 'Oil on walnut panel', 'dimensions': '62 × 44 cm',
     'current_location': 'Louvre, Paris', 'type': 'painting', 'era': 'middle',
     'subject': 'portrait', 'attribution': 'accepted',
     'commons_filename': 'La_belle_ferronnière,Leonardo_da_Vinci_-_Louvre.jpg',
     'wiki_slug': 'La_Belle_Ferronni%C3%A8re'},
    {'id': 13, 'title': 'Portrait of a Musician', 'date': 'c. 1483–1487',
     'medium': 'Oil on walnut panel', 'dimensions': '43 × 31 cm',
     'current_location': 'Pinacoteca Ambrosiana, Milan', 'type': 'painting', 'era': 'middle',
     'subject': 'portrait', 'attribution': 'accepted (partly workshop)',
     'commons_filename': 'Leonardo_da_Vinci_-_Portrait_of_a_Musician_-_Pinacoteca_Ambrosiana.jpg',
     'wiki_slug': 'Portrait_of_a_Musician'},
    {'id': 14, 'title': 'Saint Jerome in the Wilderness', 'date': 'c. 1480–1490',
     'medium': 'Oil and tempera on walnut panel', 'dimensions': '103 × 75 cm',
     'current_location': 'Vatican Pinacoteca', 'type': 'painting', 'era': 'early',
     'subject': 'religious', 'attribution': 'accepted (unfinished)',
     'commons_filename': 'Saint_Jerome_Leonardo_-_image_only_(Q972196).jpg',
     'wiki_slug': 'Saint_Jerome_in_the_Wilderness_(Leonardo)'},
    {'id': 15, 'title': 'Adoration of the Magi', 'date': 'c. 1481–1482',
     'medium': 'Oil on panel', 'dimensions': '246 × 243 cm',
     'current_location': 'Uffizi, Florence', 'type': 'painting', 'era': 'early',
     'subject': 'religious', 'attribution': 'accepted (unfinished)',
     'commons_filename': 'Leonardo_da_Vinci_-_Adorazione_dei_Magi_-_Google_Art_Project.jpg',
     'wiki_slug': 'Adoration_of_the_Magi_(Leonardo)'},
    {'id': 16, 'title': 'Madonna Litta', 'date': 'c. 1490',
     'medium': 'Tempera on canvas (transferred from panel)', 'dimensions': '42 × 33 cm',
     'current_location': 'Hermitage Museum, St Petersburg', 'type': 'painting', 'era': 'middle',
     'subject': 'religious', 'attribution': 'attributed (partly workshop)',
     'commons_filename': 'Leonardo_da_Vinci_attributed_-_Madonna_Litta.jpg',
     'wiki_slug': 'Madonna_Litta'},
    # --- Drawings ---
    {'id': 17, 'title': 'Vitruvian Man', 'title_original': 'L\'uomo vitruviano',
     'date': 'c. 1490', 'medium': 'Pen and ink on paper', 'dimensions': '34.4 × 25.5 cm',
     'current_location': 'Gallerie dell\'Accademia, Venice', 'type': 'drawing', 'era': 'middle',
     'subject': 'study', 'attribution': 'accepted',
     'commons_filename': 'Da_Vinci_Vitruve_Luc_Viatour.jpg',
     'wiki_slug': 'Vitruvian_Man'},
    {'id': 18, 'title': 'Head of a Woman (La Scapigliata)', 'date': 'c. 1500–1510',
     'medium': 'Umber, green, and white pigments on panel', 'dimensions': '24.7 × 21 cm',
     'current_location': 'Galleria Nazionale, Parma', 'type': 'painting', 'era': 'late',
     'subject': 'study', 'attribution': 'accepted',
     'commons_filename': 'La_Scapigliata_di_Leonardo_Da_Vinci.jpg',
     'wiki_slug': 'La_Scapigliata'},
    {'id': 19, 'title': 'Portrait of a Man in Red Chalk', 'date': 'c. 1512',
     'medium': 'Red chalk on paper', 'dimensions': '33.3 × 21.4 cm',
     'current_location': 'Royal Library, Turin', 'type': 'drawing', 'era': 'late',
     'subject': 'portrait', 'attribution': 'attributed',
     'commons_filename': 'Leonardo_da_Vinci_-_presumed_self-portrait_-_lossless.png',
     'wiki_slug': 'Portrait_of_a_Man_in_Red_Chalk'},
    {'id': 20, 'title': 'Study of a Tuscan Landscape', 'date': '1473-08-05',
     'medium': 'Pen and ink on paper', 'dimensions': '19 × 28.5 cm',
     'current_location': 'Uffizi, Florence', 'type': 'drawing', 'era': 'early',
     'subject': 'landscape', 'attribution': 'accepted',
     'commons_filename': 'Paisagem_do_Arno_-_Leonardo_da_Vinci.jpg',
     'wiki_slug': 'Paesaggio_(Leonardo)'},
]


def fetch_image_info(filenames):
    titles = '|'.join(f'File:{fn}' for fn in filenames)
    params = urllib.parse.urlencode({
        'action': 'query', 'titles': titles,
        'prop': 'imageinfo', 'iiprop': 'url|size|mime',
        'iiurlwidth': '800', 'format': 'json',
    })
    req = urllib.request.Request(f'{COMMONS_API}?{params}',
                                 headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main():
    print(f"Resolving Commons metadata for {len(WORKS)} works...")
    # Batch by 50
    results = {}
    fnames = [w['commons_filename'] for w in WORKS]
    for i in range(0, len(fnames), 50):
        batch = fnames[i:i+50]
        resp = fetch_image_info(batch)
        pages = resp.get('query', {}).get('pages', {})
        for pid, p in pages.items():
            if int(pid) < 0:
                # missing page; will leave empty
                continue
            raw = p.get('title', '')[5:].replace(' ', '_')
            ii = (p.get('imageinfo') or [{}])[0]
            if not ii.get('url'):
                continue
            results[raw] = {
                'image_url': ii.get('url', ''),
                'thumb_url': ii.get('thumburl', ''),
                'commons_page': ii.get('descriptionurl', ''),
                'image_width': ii.get('width'),
                'image_height': ii.get('height'),
                'mime': ii.get('mime', ''),
            }
        time.sleep(0.8)

    # Build catalog
    catalog = []
    for w in WORKS:
        entry = dict(w)
        info = results.get(w['commons_filename'].replace(' ', '_'))
        if info:
            entry.update(info)
        else:
            print(f"  ! unresolved: {w['commons_filename']}")
        # provenance_url: wikipedia article if we have a slug
        if w.get('wiki_slug'):
            entry['provenance_url'] = f"https://en.wikipedia.org/wiki/{w['wiki_slug']}"
        # Tag as famous if it's a widely-recognised work
        famous = w['title'] in {'Mona Lisa', 'The Last Supper', 'Vitruvian Man',
                                 'Lady with an Ermine', 'Ginevra de\' Benci',
                                 'Virgin of the Rocks (Louvre version)',
                                 'Saint John the Baptist',
                                 'Virgin and Child with Saint Anne',
                                 'Head of a Woman (La Scapigliata)',
                                 'Portrait of a Man in Red Chalk'}
        entry['famous'] = famous
        # Parse year_start / year_end / circa from date string
        d = entry.get('date', '')
        circa = 'c.' in d.lower() or 'circa' in d.lower()
        entry['circa'] = circa
        years = [int(y) for y in re.findall(r'1[45]\d\d', d)]
        entry['year_start'] = min(years) if years else None
        entry['year_end'] = max(years) if years else None
        # strip the wiki_slug from output
        entry.pop('wiki_slug', None)
        catalog.append(entry)

    with open(RAW, 'w', encoding='utf-8') as f:
        json.dump(WORKS, f, ensure_ascii=False, indent=2)
    with open(CATALOG, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    ok = sum(1 for e in catalog if e.get('image_url'))
    print(f"\nWrote {len(catalog)} entries ({ok} with resolved images) -> {CATALOG}")


if __name__ == '__main__':
    main()
