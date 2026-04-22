#!/usr/bin/env python3
"""Build assets/search-index.json from the 18 per-artist catalogs.

Compact entry shape consumed by index.html:
  a: artist slug           (directory name)
  s: artwork slug          (from catalog)
  t: title                 (display)
  r: tier ('famous' | 'well_known')  — omitted if neither
  i: thumbnail URL         (thumb_url preferred, falls back to image_url)
  y: year_start (int)      — omitted if missing

Entries without an image_url are dropped (they can't render in the result list).

Run:  python3 scripts/build_search_index.py
"""
import json
from pathlib import Path

ARTISTS = sorted([
    'abanindranath-tagore', 'amrita-sher-gil', 'behzad', 'caravaggio',
    'degas', 'hiroshige', 'hokusai', 'kuniyoshi', 'leonardo-da-vinci',
    'mary-cassatt', 'monet', 'raja-ravi-varma', 'rembrandt', 'titian',
    'utamaro', 'van-gogh', 'vermeer', 'xu-beihong',
])

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'search-index.json'


def build():
    out = []
    for a in ARTISTS:
        f = ROOT / a / 'catalog.json'
        catalog = json.loads(f.read_text())
        for e in catalog:
            image = e.get('image_url')
            if not image:
                continue
            slug = e.get('slug')
            if not slug:
                continue
            entry = {
                'a': a,
                's': slug,
                't': e.get('title', ''),
            }
            tier = e.get('tier')
            if tier in ('famous', 'well_known'):
                entry['r'] = tier
            entry['i'] = e.get('thumb_url') or image
            ys = e.get('year_start')
            if ys is not None:
                entry['y'] = ys
            out.append(entry)
    return out


def main():
    entries = build()
    OUT.write_text(json.dumps(entries, ensure_ascii=False, separators=(',', ':')))
    print(f'wrote {len(entries)} entries to {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
