# Leonardo da Vinci Collection

## Scope

20 works by **Leonardo da Vinci** (1452–1519) — the Tuscan polymath whose painted output is famously small but whose influence is outsized. The collection is a **curated list**, not an exhaustive scrape: fewer than 20 paintings are universally accepted as fully autograph, the rest are disputed or partly workshop. Trying to scrape Wikipedia lists of "works" produces far too much attribution noise.

This collection includes:
- The 15–16 widely accepted paintings (Mona Lisa, Last Supper, Virgin of the Rocks in both Louvre and London versions, Lady with an Ermine, Ginevra de' Benci, Annunciation, Benois Madonna, Saint John the Baptist, Virgin and Child with Saint Anne, Madonna of the Carnation, La Belle Ferronnière, Portrait of a Musician, Saint Jerome, Adoration of the Magi, Madonna Litta).
- Famous drawings / studies (Vitruvian Man, La Scapigliata, Portrait of a Man in Red Chalk, the 1473 Arno Valley landscape).

**Not included**: *Salvator Mundi* (2017 auction provenance remains disputed), the 5000+ notebook sketches (too many to meaningfully catalog here), and workshop pieces.

## Copyright Status

**Public Domain Worldwide.** Leonardo died on 2 May 1519 — 506 years ago. Pre-modern. Any reproduction-photograph claims have long since lapsed everywhere.

## Collection specifics

- **Attribution classifications**: each entry carries an `attribution` field — `accepted`, `accepted (unfinished)`, `accepted (partly workshop)`, or `attributed`. Follows Zöllner, *Leonardo da Vinci: Complete Paintings and Drawings* (2019) as a standard.
- **Unfinished works are canon**: *Saint Jerome* and *Adoration of the Magi* are canonically Leonardo despite being incomplete — this reflects scholarly consensus, not data error.
- **`type` field**: splits paintings from drawings. Useful because Leonardo's drawings are substantive independent works, not just preparatory sketches.
- **Two versions of Virgin of the Rocks**: both the Louvre (c.1483–1486) and National Gallery, London (c.1495–1508) versions are in the collection. They're sufficiently different that scholars treat them as two autonomous works.
- **Hand-curated, not scraped**: unusual among the collections in this repo. The source script lives at [scripts/fetch_commons.py](scripts/fetch_commons.py). Re-running it resolves all Commons URLs / metadata freshly but the list of works is hard-coded.

## Sources

- Wikipedia: [Leonardo da Vinci](https://en.wikipedia.org/wiki/Leonardo_da_Vinci), [List of works by Leonardo da Vinci](https://en.wikipedia.org/wiki/List_of_works_by_Leonardo_da_Vinci)
- Wikimedia Commons: [Category:Paintings by Leonardo da Vinci](https://commons.wikimedia.org/wiki/Category:Paintings_by_Leonardo_da_Vinci), [Category:Drawings by Leonardo da Vinci](https://commons.wikimedia.org/wiki/Category:Drawings_by_Leonardo_da_Vinci)
- Catalogue raisonné: Zöllner, *Leonardo da Vinci: The Complete Paintings and Drawings*, Taschen (2019)
