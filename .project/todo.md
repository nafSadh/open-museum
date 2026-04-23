# TODO — open-museum

_Last refreshed: 2026-04-21. See `.project/audit-2026-04-21.md` for current data-quality snapshot._

## Cross-collection

- [x] Cross-collection search (root `index.html`, uses `assets/search-index.json`)
- [x] Tier-based default sort across all 18 galleries (famous → well_known → rest)
- [x] Year-midpoint tiebreaker in the default sort (applied 2026-04-21)
- [x] Date-triplet backfill for parseable century / era strings (hokusai, utamaro, raja-ravi-varma, behzad)
- [x] `provenance_url` migration (100% of 7,400 entries; legacy `wikipedia_url` / `source` fully retired)
- [x] Per-collection `README.md` (all 18 present)
- [x] `scripts/build_search_index.py` — automated via `.githooks/pre-commit` (rebuilds + auto-stages when any catalog is staged; one-time `git config core.hooksPath .githooks` to enable)
- [ ] Surface Wikidata genres/depicts in gallery filters (fetched but unused in UI)

## Van Gogh

- [x] Catalog (1,153 works, 99.7% image coverage, 79% Wikidata match)
- [x] Sentence-builder filter UI (era / subject / famous) with sticky top bar
- [ ] Add Van Gogh drawings (separate Wikipedia article, ~1,100 works)
- [ ] Enrich `medium` for the non-Hague painting sections (currently 12%)
- [ ] Use high-res image URL in lightbox (currently same as thumb)
- [ ] Mobile layout pass
- [ ] Load-more / pagination UX improvement

## Collections — shipped (18)

- [x] Van Gogh (1,153)
- [x] Monet (1,766)
- [x] Leonardo da Vinci (1,697 — paintings + drawings + codex folios; `held_at` filter)
- [x] Titian (164)
- [x] Caravaggio (89)
- [x] Rembrandt (805 — paintings + etchings + drawings)
- [x] Vermeer (37)
- [x] Degas (51)
- [x] Mary Cassatt (182 — paintings + pastels + print)
- [x] Hokusai (86)
- [x] Hiroshige (363)
- [x] Utamaro (367)
- [x] Kuniyoshi (29)
- [x] Raja Ravi Varma (230)
- [x] Abanindranath Tagore (47)
- [x] Amrita Sher-Gil (169)
- [x] Xu Beihong (40)
- [x] Kamāl ud-Dīn Behzād (125)

## Collections — open

### Western canon
- [ ] Paul Cézanne
- [ ] Michelangelo
- [ ] Pierre-Auguste Renoir
- [ ] Édouard Manet
- [ ] Paul Gauguin
- [ ] Georges Seurat
- [ ] Henri de Toulouse-Lautrec
- [ ] Raphael
- [ ] Sandro Botticelli
- [ ] Hieronymus Bosch
- [ ] Pieter Bruegel the Elder
- [ ] Jan van Eyck
- [ ] Francisco Goya
- [ ] J.M.W. Turner
- [ ] Caspar David Friedrich
- [ ] Eugène Delacroix
- [ ] Gustav Klimt
- [ ] Egon Schiele
- [ ] Amedeo Modigliani

### East Asia
- [ ] Shitao
- [ ] Bada Shanren
- [ ] Shen Zhou
- [ ] Tang Yin
- [ ] Kuroda Seiki

## Data-quality follow-ups (from 2026-04-21 audit)

- [ ] Amrita Sher-Gil: 37 entries missing `image_url` (~22% of collection)
- [ ] Raja Ravi Varma: 15 entries missing `image_url`; 83 entries still carry "Unknown date" variants with no year
- [ ] Leonardo: 76% of entries lack a `date` (drawings and codex folios often undated — consider dating where catalogued)
- [ ] Behzad: 7 entries carry future-year `date` strings (`c. 3580`, `c. 2313`, `c. 4798`, `c. 2277`) — likely folio / accession numbers harvested as dates. Parser already refuses them (year triplet null), but the `date` display string still misleads; curation pass to correct or null the field.
