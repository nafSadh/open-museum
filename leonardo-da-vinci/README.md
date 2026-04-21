# Leonardo da Vinci Collection

## Scope

~1,700 works by **Leonardo da Vinci** (1452–1519) — the Tuscan polymath whose painted output is famously small (around 20 accepted panels) but whose drawings number in the thousands. The collection uses a **hybrid strategy**:

1. **Curated paintings** — the 17 universally accepted panels (Mona Lisa, Last Supper, the two Virgin of the Rocks, Lady with an Ermine, Ginevra de' Benci, Annunciation, Benois Madonna, Saint John the Baptist, Virgin and Child with Saint Anne, Madonna of the Carnation, La Belle Ferronnière, Portrait of a Musician, Saint Jerome, Adoration of the Magi, Madonna Litta, La Scapigliata) plus three famous drawings (Vitruvian Man, Portrait of a Man in Red Chalk, Study of a Tuscan Landscape) with hand-entered medium / dimensions / location.
2. **Commons category crawl** of drawings, studies, and manuscript folios from Leonardo's holdings at the **Royal Collection (Windsor)**, **Louvre**, **British Museum**, **Biblioteca Ambrosiana** (Milan), **Biblioteca Reale** (Turin), and **Gallerie dell'Accademia** (Venice). Plus the *Codex on the Flight of Birds* and Leonardo's manuscript pages held at the Institut de France.

**Not included**: *Salvator Mundi* (2017 auction provenance remains contested), modern 3D reconstructions of Leonardo's machine designs, copies-after-Leonardo and school-of-Leonardo works, and gallery-installation photos. Commons is dense with these — they're filtered out at both category and filename level (see [scripts/fetch_commons.py](scripts/fetch_commons.py)).

The painting category on Commons itself is almost entirely noise (multiple high-res scans of the same canvas, plus school-of / studio-of pieces), so paintings come from the curated list only.

## Copyright Status

**Public Domain Worldwide.** Leonardo died on 2 May 1519 — 506 years ago. Pre-modern. Any reproduction-photograph claims have long since lapsed everywhere.

## Collection specifics

- **Attribution field**: `accepted`, `accepted (unfinished)`, `accepted (partly workshop)`, or `attributed`. The curated paintings follow Zöllner, *Leonardo da Vinci: Complete Paintings and Drawings* (2019). Crawled drawings are marked `accepted` because Commons categories under "... by Leonardo da Vinci" are already filtered for him; `after-Leonardo` / `school-of` subcategories are excluded at crawl time.
- **`type` field**: `painting`, `drawing`, `study`, or `codex_folio`. Useful because Leonardo's drawings and codex folios are substantive independent works, not just preparatory sketches — the Royal Collection at Windsor alone has ~600 of them.
- **Unfinished works are canon**: *Saint Jerome*, *Adoration of the Magi*, *Last Supper* (deteriorated) are canonically Leonardo despite being incomplete or degraded.
- **Two versions of Virgin of the Rocks**: both the Louvre (c.1483–1486) and National Gallery, London (c.1495–1508) versions are separate entries. They're sufficiently different that scholars treat them as autonomous works.
- **Dates are sparse on drawings**: only ~24% of drawings carry a parsable date. Leonardo rarely dated folios; most dates in the literature are inferred from ink type, handwriting, and referenced events. Where the field is blank, `year_start` / `year_end` are null.
- **Hand-curated + scripted hybrid**: script at [scripts/fetch_commons.py](scripts/fetch_commons.py). Re-running it re-resolves all Commons URLs, re-crawls the source categories, and re-applies the filters. Curated entries always win on dedupe.

## Sources

- Wikipedia: [Leonardo da Vinci](https://en.wikipedia.org/wiki/Leonardo_da_Vinci), [List of works by Leonardo da Vinci](https://en.wikipedia.org/wiki/List_of_works_by_Leonardo_da_Vinci)
- Wikimedia Commons: [Category:Paintings by Leonardo da Vinci](https://commons.wikimedia.org/wiki/Category:Paintings_by_Leonardo_da_Vinci), [Category:Drawings by Leonardo da Vinci](https://commons.wikimedia.org/wiki/Category:Drawings_by_Leonardo_da_Vinci)
- Catalogue raisonné: Zöllner, *Leonardo da Vinci: The Complete Paintings and Drawings*, Taschen (2019)
