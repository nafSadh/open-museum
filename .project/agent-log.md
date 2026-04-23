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
| 42 | 2026-04-21 | dedupe-artifacts | Merge 20 near-duplicate catalog entries (same commons_filename, variant titles) — 2 exact dupes + 18 title-variant pairs across monet, rembrandt, raja-ravi-varma | done | monet 1772→1766, rembrandt 806→805, raja-ravi-varma 241→230; kept richer title, preserved all non-empty fields from dropped entries |
| 43 | 2026-04-21 | image-backfill-pass2 | Second pass on remaining missing images with stricter shared-token threshold (>=3) | done | Filled 4 more: van-gogh "Blossoming Acacia Branches", utamaro "Shinagawa no Tsuki", raja-ravi-varma "Yashoda and Krishna" + "Swarbat Player" |
| 44 | 2026-04-21 | cassatt-build | Build mary-cassatt collection via Commons crawl (Paintings/Prints/Drawings cats); filter Breeskin catalogue-raisonné book scans and tombstone photos | done | 182 works: 130 paintings + 51 pastels + 1 print; rose/sage palette; mother_child / portrait / print / genre filters |
| 45 | 2026-04-21 | caravaggio-build | Build caravaggio collection; keep one representative file per painting-subcategory (921 → 89 by deduping detail-shot variants) | done | 89 paintings; chiaroscuro palette (deep crimson/ochre); religious / mythological / genre / portrait / still_life filters |
| 46 | 2026-04-21 | tagore-build | Build abanindranath-tagore collection; filter out photos of his house / garden / memorial street (non-artworks) | done | 47 paintings; saffron/marigold/indigo palette; mythological / portrait / landscape / religious filters |
| 47 | 2026-04-21 | gitignore | Add .gitignore excluding Claude Code runtime artifacts (scheduled_tasks.lock, scheduled_tasks.json) + Python/OS noise | done | Untracked .claude/scheduled_tasks.lock that had been accidentally committed earlier |
| 48 | 2026-04-21 | date-triplet-backfill | Parse loose date strings → year_start/year_end/circa across non-Western collections (centuries, Japanese eras, Roman numerals); refuses future-year outliers and pure unknowns | done | 61 entries: behzad 32, utamaro 17, raja-ravi-varma 11, hokusai 1 |
| 49 | 2026-04-21 | search-index-builder | Create scripts/build_search_index.py; reproduces the existing assets/search-index.json shape from the 18 catalogs so future rebuilds are automated | done | New script + regenerated search-index.json picks up the 61 new y values |
| 50 | 2026-04-21 | year-aware-sort | Add year-midpoint tiebreaker in applyFilters across all 18 gallery index.html files (chronological within tier, nulls last) | done | Uniform 3-line patch in each gallery |
| 51 | 2026-04-21 | project-refresh | Rewrite .project/todo.md, write .project/audit-2026-04-21.md (supersedes 04-20), catch up .project/changelog.md (April 5–20 expansion summarized with pointer to agent-log) | done | todo + audit + changelog in sync with current reality |
| 52 | 2026-04-22 | asg-rrv-image-backfill | Commons search for the 52 residual no-image entries (amrita-sher-gil 37 + raja-ravi-varma 15) after 2 prior passes. Fuzzy-match title tokens + artist name against Commons API; HEAD-verify each candidate; populate image_url/thumb_url/commons_filename/commons_page | running | — |
| 53 | 2026-04-22 | vg-drawings-build | Scrape "List of drawings by Vincent van Gogh" from Wikipedia, resolve Commons URLs, append to van-gogh/catalog.json as type="drawing" (do not overwrite existing paintings); update van-gogh/index.html filter UI to expose type toggle | done | 516 drawings added (100% images resolved); catalog 1,153 → 1,669; 141 slug collisions resolved with `-drawing` suffix; added `drawings` pick to type filter + typeNames map; hero desc updated. Curation (tier/famous) left unset per task spec |
| 54 | 2026-04-22 | leonardo-rcin-dates | Scrape Royal Collection catalog (rct.uk or equivalent) keyed by RCIN number for the 743 Windsor Leonardo drawings; populate date + year_start/year_end/circa on leonardo-da-vinci/catalog.json entries where harvest_method contains "Royal Collection" | done | 743/743 dated (568 from title tokens, 163 from col.rct.uk, 2 Commons `15-16c` fallback); www.rct.uk is Cloudflare-blocked but col.rct.uk subdomain works; leonardo-da-vinci catalog-wide coverage 24%→67% |
| 55 | 2026-04-22 | propagate-vg-ui-patterns | Apply the recently-shipped Van Gogh UX patterns to Monet, Leonardo, Rembrandt galleries: (1) scroll-event infinite-load in applyFilters area, (2) @media (hover: none) + JS tap-toggle on .sentence, (3) include wikidata_genres/wikidata_depicts in search haystack if those fields exist in the catalog, (4) lb-tags row in lightbox if data present | done | monet/rembrandt: patterns 1+2 applied (no wikidata fields in those catalogs so 3+4 skipped). leonardo: pattern 2 only (no pagination system in that gallery — needs separate refactor). Main session added leonardo's missing tap-handler JS |
| 56 | 2026-04-22 | cezanne-build | Full Paul Cézanne collection: scrape Wikipedia "List of paintings by Paul Cézanne" (4 tables), resolve Commons URLs, build catalog.json with date triplet + V/R/FWN catalog numbers, write index.html gallery (Provence ochre/sage/terracotta/sky palette, era + subject + series + famous filters, infinite scroll, DPR-aware lightbox, tap-to-expand), add to root index.html, write README.md with PD rationale (d. 1906, PD worldwide since 1977) | done | 932 oils (159 early / 185 impressionist / 301 constructive / 287 late); 931/932 (99.9%) Commons-resolved; series: 34 mont-sainte-victoire + 61 bathers + 50 apples + 27 l'estaque + 25 self-portrait + 7 card-players + 4 harlequin; tier/famous unset (manual pass) |
