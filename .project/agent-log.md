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
