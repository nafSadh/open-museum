# Paul Cézanne Collection

## Scope

932 oil paintings by **Paul Cézanne** (1839–1906), scraped from Wikipedia's
_List of paintings by Paul Cézanne_ and resolved against Wikimedia Commons.

Cézanne also produced ~400 watercolours and a comparable body of drawings;
those are currently **out of scope** and may be added in a later pass
(Wikipedia lists them on separate articles).

## Copyright Status

**Public Domain Worldwide.** Paul Cézanne died on **19 October 1906** —
well clear of the 70-year life+ threshold, public domain in every
life+70 (and life+100) jurisdiction since 1977.

## Sources

- Wikipedia: [List of paintings by Paul Cézanne](https://en.wikipedia.org/wiki/List_of_paintings_by_Paul_C%C3%A9zanne) — primary list (4 tables, chronological)
- Wikimedia Commons — all image URLs
- Catalogue raisonné numbers are carried through from Wikipedia's table:
  - **V** — Lionello Venturi, _Cézanne, son art, son œuvre_ (1936)
  - **R** — John Rewald, _The Paintings of Paul Cézanne: A Catalogue Raisonné_ (1996)
  - **FWN** — Feilchenfeldt / Warman / Nash, _The Paintings of Paul Cézanne: An Online Catalogue Raisonné_ ([cezannecatalogue.com](https://www.cezannecatalogue.com))

## Collection-specific schema fields

Most entries carry:

- `title`, `slug`, `id` — standard
- `date` + `year_start` + `year_end` + `circa` — date triplet. Year ranges
  (`"1872-73"`, `"1877-79"`) resolve to `start`/`end` spans; `"c. 1859"`
  sets `circa=true`.
- `era` — `early` (1859–70) · `impressionist` (1871–78) · `constructive`
  (1878–90) · `late` (1890–1906). Derived from the Wikipedia section the
  row was found in.
- `section` — verbatim Wikipedia section heading.
- `subject` — heuristic from title: `landscape` · `mountain` (Mont
  Sainte-Victoire) · `still_life` · `portrait` · `bather` · `cardplayer`
  · `other`.
- `series` — set only when a recurring motif matches: `mont-sainte-victoire`,
  `bathers`, `card-players`, `apples`, `mount-marseille` (L'Estaque / Gulf
  of Marseille views), `self-portrait`, `harlequin-pierrot`.
- `dimensions` — verbatim from the Wikipedia table (`"65 x 81 cm"`).
- `current_location` — verbatim from the Wikipedia table; many are
  `"Private collection"`.
- `v_number`, `r_number`, `fwn_number` — catalogue-raisonné numbers,
  prefixed (`"V.3"`, `"R.1"`, `"FWN.560"`). Any of the three may be
  absent; `raw_cat_no` keeps the original "V 3 | R 1 | FWN 560" string.
- `commons_filename`, `image_url`, `thumb_url`, `commons_page`,
  `image_width`, `image_height`, `mime` — image info from Commons
  `imageinfo` API. `thumb_url` is the 960 px variant (smallest
  pre-cached JPG size; the lightbox swaps to 1280/1920/3840 by DPR).
- `title_disambig` — set for duplicate titles; format is
  `"{date} · {FWN.xxx or V.xxx}"`.
- `provenance_url` — the list-page URL on Wikipedia (per-work articles
  are rare).
- `harvest_method` — `"wikipedia_list"`.
- `tier` — _unset_ until manual curation (same pattern as monet,
  titian, etc.).
- `famous` — not set; will come with the manual tier pass.

## Scripts

- `scripts/scrape_wiki_list.py` — parses the 4 wikitables from the
  Wikipedia list; writes `wiki_works_raw.json`.
- `scripts/resolve_commons_urls.py` — batch-resolves Commons imageinfo,
  enriches the date triplet / slug / id / provenance / harvest fields,
  adds `title_disambig` for dup titles; writes `catalog.json`.

Both are idempotent — safe to re-run.
