# Agent Tracking — open-museum

> **Rule**: Every sub-agent spawned in this repo must be logged here. See `AGENTS.md` for full instructions.

---

## Active Agents

| # | Date | Agent ID | Task | Status | Output |
|---|------|----------|------|--------|--------|

## Completed Agents

| # | Date | Agent ID | Task | Status | Output |
|---|------|----------|------|--------|--------|
| 1 | 2026-04-04 | wiki-list-research | Fetch & analyze Wikipedia "List of works by Van Gogh" structure | done | ~1,345 works across 11 sections, 3 table variants identified |
| 2 | 2026-04-04 | commons-research | Analyze Wikimedia Commons category structure for Van Gogh | done | 859 per-title subcategories, API bulk-fetch strategy identified |
| 3 | 2026-04-04 | wiki-scraper | Run scrape_wiki_list.py to extract works from Wikipedia | done | 1,154 works -> van-gogh/wiki_works_raw.json |
| 4 | 2026-04-04 | commons-resolver | Run resolve_commons_urls.py to fetch image URLs from Commons API | done | 1,150/1,150 resolved -> van-gogh/catalog.json |
| 5 | 2026-04-04 | catalog-cleanup | Remove malformed entries, normalize fields | done | 1,153 final works in catalog.json |
| 6 | 2026-04-04 | web-init | Create index.html landing + van-gogh/index.html gallery | done | Root catalog page + filterable gallery with lightbox |
| 7 | 2026-04-04 | wikidata-fetch | Write & run fetch_wikidata.py to get genre/depicts from Wikidata | done | 887 items, 911 matched (79%), 713 genres, 664 depicts |
| 8 | 2026-04-06 | titian-wiki-scraper | Run scrape_wiki_list.py for Titian | done | 164 works -> titian/wiki_works_raw.json |
| 9 | 2026-04-06 | titian-commons-resolver | Run resolve_commons_urls.py for Titian | done | 164/164 resolved -> titian/catalog.json |
| 10 | 2026-04-06 | titian-web-init | Create titian/index.html gallery and root listing | done | Titian catalog page added |
| 11 | 2026-04-06 | monet-wiki-scraper | Run scrape_wiki_list.py for Monet | done | 1,774 works -> monet/wiki_works_raw.json |
| 12 | 2026-04-06 | monet-commons-resolver | Run resolve_commons_urls.py for Monet | done | Resolved -> monet/catalog.json |
| 13 | 2026-04-06 | monet-web-init | Create monet/index.html gallery and root listing | done | Add Monet page and root link |
| 14 | 2026-04-05 | titian-enrich | Create enrich_catalog.py; compute era/subject/type/famous for all 164 works | done | early 55 / middle 64 / late 45; portrait 50 / religious 40 / mythological 27 / allegory 6; 41 famous |
| 15 | 2026-04-06 | titian-gallery-filters | Add sentence-builder filters (era, subject, famous) to titian/index.html | done | Inline pick UI with live filtering |
| 16 | 2026-04-06 | monet-enrich | Create enrich_catalog.py; compute era/subject/famous for all 1,774 works | done | early 144 / impressionist 1137 / series 493; water 664 / landscape 465 / garden 224 / urban 81 / portrait 58 / still_life 38; 437 famous |
| 17 | 2026-04-06 | monet-gallery-filters | Add era, subject, famous filters to monet/index.html sentence builder | done | Filters alongside existing series picker |
| 18 | 2026-04-09 | rembrandt-wiki-scraper | Scrape 3 Wikipedia list pages for Rembrandt | done | 806 works (348 paintings, 289 etchings, 169 drawings) → rembrandt/wiki_works_raw.json |
| 19 | 2026-04-09 | rembrandt-commons-resolver | Resolve Commons URLs for Rembrandt | done | 804/806 resolved → rembrandt/catalog.json |
| 20 | 2026-04-09 | rembrandt-enrich | Enrich catalog with era/subject/famous | done | early 435 / middle 245 / late 126; portrait 292 / religious 195 / landscape 49 / mythological 22; 129 famous |
| 21 | 2026-04-09 | rembrandt-web-init | Create rembrandt/index.html gallery (medium/era/subject filters) + root listing | done | Gallery with 4 filters: medium, era, subject, famous |
