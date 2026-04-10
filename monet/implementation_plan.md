# Monet Collection Implementation Plan

This implementation plan details the steps to establish a new collection for Claude Monet, incorporating his public domain works into the `open-museum` project.

## User Review Required

> [!IMPORTANT]
> The scripts from `van-gogh/` will be used as a base and modified to work with Monet's Wikipedia article structure. Are `fetch_wikidata.py` and `enrich_catalog.py` needed for Monet as well, or should I skip them and just synthesize `wiki_works_raw.json` with Wikimedia Commons URLs directly into `catalog.json`? For this plan, I've left out Wikidata enrichment, focusing on Wikipedia and Wikimedia Commons.

## Proposed Changes

### 1. Project Scaffolding
We will create the core directory structure for Monet:
- **`monet/`** folder inside the project root.
- **`monet/README.md`**: Add copyright details (public domain, 70+ year rule applies) and references.
- **`monet/scripts/`**: Copy over base scrape and resolve scripts from `van-gogh/scripts/`.

### 2. Scrape Structured Data
- **`monet/scripts/scrape_wiki_list.py`**: 
  - Read `https://en.wikipedia.org/w/api.php?action=parse&page=List_of_paintings_by_Claude_Monet`.
  - Process tables with columns (`ImageTitle`, `Year`, `Location`, `Dimensions (cm.)`, `Cat. no.Medium`).
  - Extract Wildenstein index (`W numbers`).
  - Extract `era` and `series` information using text analysis of sections or titles (e.g. "Water Lilies", "Haystacks").
  - Output to `monet/wiki_works_raw.json`.

### 3. Resolve Wikimedia Commons
- **`monet/scripts/resolve_commons_urls.py`**:
  - Pull Wikimedia Commons image resolution data.
  - Rely on careful filename matching (crucial for Monet's expansive series) for high-resolution images.

### 4. Build Master JSON Catalog
- Compile the enriched Monet dataset into **`monet/catalog.json`**.

### 5. Update Gallery UI
- **`monet/index.html`**:
  - Copy foundational layout and styles from `van-gogh/index.html`.
  - Add a new "Series" UI filter next to the existing Era and Subject filters.
  - Wire JavaScript filtering to parse the new `monet` dataset.
- **`index.html`**:
  - Add a collection card highlighting Monet alongside Van Gogh and Titian.

## Open Questions

> [!WARNING]  
> Can you confirm the Wikipedia "Cat. no.Medium" column accurately reflects what you need for dimension and W_number extraction, and any specific series names we should explicitly track besides the main ones (e.g., Water Lilies, Rouen Cathedral)?

## Verification Plan

### Automated Tests
- Validate `monet/catalog.json` to ensure 95%+ of items have valid Wikimedia Commons URLs.
- Assert every entry has a `W_number` index (from Wikipedia `Cat. no.` column).

### Manual Verification
- Launch local static server and review `index.html` to confirm Monet appears.
- Test `monet/index.html` to confirm the new Series filter works properly alongside Era and Subject filters.
