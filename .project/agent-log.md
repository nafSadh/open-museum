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
| 22 | 2026-04-09 | vermeer-wiki-scraper | Scrape Wikipedia list for Vermeer | done | 37 works (36 confirmed + 1 disputed) → vermeer/wiki_works_raw.json |
| 23 | 2026-04-09 | vermeer-commons-resolver | Resolve Commons URLs for Vermeer | done | 37/37 resolved → vermeer/catalog.json |
| 24 | 2026-04-09 | vermeer-enrich | Enrich catalog with era/subject/famous | done | early 8 / middle 15 / late 14; genre 25 / religious 3 / allegory 2 / portrait 2 / landscape 2; 28 famous |
| 25 | 2026-04-09 | vermeer-web-init | Create vermeer/index.html gallery + root listing | done | Lapis/pearl palette, flow layout default, 3 layout modes |
| 26 | 2026-04-09 | degas-wiki-scraper | Scrape Degas gallery from main article (no list page) | done | 51 works → degas/wiki_works_raw.json (custom gallery parser) |
| 27 | 2026-04-09 | degas-commons-resolver | Resolve Commons URLs for Degas | done | 51/51 resolved → degas/catalog.json |
| 28 | 2026-04-09 | degas-enrich | Enrich catalog with era/subject/famous | done | early 11 / impressionist 31 / late 9; dance 15 / nude 8 / portrait 8; 22 famous |
| 29 | 2026-04-09 | degas-web-init | Create degas/index.html gallery + root listing | done | Rose/blush/sage palette, flow default, dance/nude/portrait/racing filters |
| 30 | 2026-04-09 | hokusai-full | Scrape + resolve + enrich + gallery for Hokusai | done | 86 works, indigo/wave palette, 36 Views of Fuji series |
| 31 | 2026-04-09 | hiroshige-full | Scrape 6 series pages + resolve + enrich + gallery for Hiroshige | done | 363 works, misty landscape palette |
| 32 | 2026-04-09 | utamaro-full | Scrape + resolve + enrich + gallery for Utamaro | done | 367 works, pale pink/woodblock red palette |
| 33 | 2026-04-09 | kuniyoshi-full | Scrape + resolve + enrich + gallery for Kuniyoshi | done | 29 works, indigo/crimson/gold palette |
| 34 | 2026-04-09 | raja-ravi-varma-full | Scrape Wikipedia + 11 Commons categories + resolve + enrich + gallery | done | 241 works, saffron/gold/peacock palette |
| 35 | 2026-04-09 | amrita-sher-gil-full | Scrape 12 year-tables + resolve + enrich + gallery | done | 169 works, terracotta/ochre/green palette |
| 36 | 2026-04-09 | xu-beihong-full | Scrape Commons categories + Wikipedia + resolve + enrich + gallery | done | 40 works, ink wash palette |
| 37 | 2026-04-09 | behzad-full | Scrape Wikipedia + 7 Commons subcategories + resolve + enrich + gallery | done | 125 works, lapis/gold/turquoise palette |
| 38 | 2026-04-20 | audit-2026-04-20 | Comprehensive read-only audit: data quality, structure, PD compliance, URL liveness across all 14 collections | done | .project/audit-2026-04-20.md — 7 cross-cutting findings, 5 policy questions, prioritized backlog |
| 39 | 2026-04-21 | leonardo-curated | Build curated leonardo-da-vinci collection: 20 works (16 paintings + 4 drawings), README, umber/sienna palette, added to root | done | leonardo-da-vinci/ — all 20 Commons URLs resolved |
| 40 | 2026-04-21 | liveness-sweep-full | Full throttled HTTP HEAD sweep of all 5,339 non-empty image_url values across 14 collections (~90 min, 1 req/s, retry on 429) | done | 5,338/5,339 live (99.98%); 1 dead URL in monet (idx 161 Pool of London) — replacement filename found on Commons and patched. Results appended to audit-2026-04-20.md §Appendix A |
| 41 | 2026-04-21 | leonardo-expand | Expand leonardo-da-vinci to 1,698 works via Commons category crawl (Royal Collection, Louvre, British Museum, Ambrosiana, etc.); add type filter to gallery UI | done | 17 paintings (curated) + 1,655 drawings + 20 codex folios + 6 studies. Filters drop detail shots / copies / school-of / modern reconstructions |
