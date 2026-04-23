# open-museum — Agent README

## Project Goal

Curate collections of **public domain artwork** with high-quality image links from Wikimedia Commons and other open sources. Each artist has its own directory with an independent catalog and gallery page.

## Data Sources

- **Wikimedia Commons**: high-resolution public domain images (primary image source for every entry)
- **Wikipedia**: lists of works, biographical context, catalog references (primary `provenance_url` source)
- **Wikidata**: canonical metadata, genres, depicts (used selectively — see Van Gogh collection)
- **Artist-specific catalogue raisonnés** where applicable (Van Gogh F/JH numbers, Monet W numbers, Rembrandt B numbers, etc.)

For the decision to prefer Wikimedia/Wikidata over per-museum APIs, see [.project/api-sources-evaluation.md](.project/api-sources-evaluation.md).

## Directory Structure

```
open-museum/
├── AGENT_README.md        # This file — project overview
├── AGENTS.md              # Standing instructions for all agents (schema policy, scripts, PD rules)
├── README.md              # User-facing landing page for the repo
├── index.html             # Root landing page + cross-collection search
├── assets/
│   ├── covers/            # Per-collection cover images used on the landing page
│   └── search-index.json  # Compact cross-collection search index (built from catalogs)
├── scripts/
│   └── build_search_index.py   # Rebuilds assets/search-index.json from all catalogs
├── .project/
│   ├── agent-log.md       # Mandatory agent tracking table
│   ├── changelog.md       # Project changelog
│   ├── todo.md            # Current task list
│   ├── audit-*.md         # Periodic data-quality audits
│   └── api-sources-evaluation.md
└── {artist-slug}/         # 18 of these — see Collections below
    ├── README.md          # Collection-specific notes + PD rationale
    ├── catalog.json       # Master catalog of works
    ├── index.html         # Gallery page (self-contained)
    ├── wiki_works_raw.json  # Raw scrape output (kept for reproducibility)
    └── scripts/           # Scraping & processing scripts specific to this collection
```

## Collections (18)

Western canon: `van-gogh`, `monet`, `leonardo-da-vinci`, `titian`, `caravaggio`, `rembrandt`, `vermeer`, `degas`, `mary-cassatt`.
Ukiyo-e: `hokusai`, `hiroshige`, `utamaro`, `kuniyoshi`.
South Asia: `raja-ravi-varma`, `abanindranath-tagore`, `amrita-sher-gil`.
China: `xu-beihong`.
Persian miniature: `behzad`.

Each collection's `README.md` documents scope, sources, copyright basis, and any collection-specific schema fields.

## Data Model

Schema policy lives in [AGENTS.md](AGENTS.md) — per-collection schemas are allowed and preferred. Shared fields that apply across most collections:

- `title`, `slug`, `image_url`, `thumb_url`, `commons_filename`, `commons_page`
- `provenance_url` — single URL stamping provenance (Wikipedia → Commons → other PD source)
- `harvest_method` — how the entry was collected (`wikipedia_gallery`, `commons_category`, `manual`, etc.) — lineage tag, not a URL
- Date triplet: `date` (display string) + `year_start`, `year_end` (ints) + `circa` (bool)
- `tier` — `famous` | `well_known` | absent (curation)

Per-collection fields (`dimensions`, `current_location`, `medium`, `technique`, `series`, `japanese_title`, `w_number`, `f_number`, `held_at`, etc.) are scoped to individual collections — see each `README.md`.

## Agent Workflow

1. Scrape structured data from Wikipedia / Wikimedia Commons for the artist
2. Resolve Commons file URLs and verify they return 200
3. Build `{artist}/catalog.json`; populate the date triplet and `provenance_url`
4. Write `{artist}/index.html` gallery (independent per collection — copy-paste a sibling as a starting template; don't extract a shared template)
5. Commit — the `.githooks/pre-commit` hook regenerates `assets/search-index.json` automatically when any catalog is staged (run `scripts/build_search_index.py` manually if you need to refresh without committing)
6. Log the work in `.project/agent-log.md`

## One-time setup per clone

Enable the pre-commit hook that keeps `assets/search-index.json` in sync with the catalogs:

```
git config core.hooksPath .githooks
```

Without this, catalog edits commit without rebuilding the search index, and cross-collection search goes stale.

## Rules for Agents

See [AGENTS.md](AGENTS.md) for mandatory agent logging, data-quality standards, schema policy, and PD compliance rules.
