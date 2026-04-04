# open-museum — Agent README

## Project Goal

Curate collections of **public domain artwork** with high-quality image links from Wikimedia Commons and other open sources. The first collection targets **Vincent van Gogh** — all of whose works are in the public domain (he died in 1890, well over 70+ years ago).

## Data Sources

- **Wikipedia**: Lists of works, biographical context, catalog references
  - https://en.wikipedia.org/wiki/List_of_works_by_Vincent_van_Gogh
  - https://en.wikipedia.org/wiki/Vincent_van_Gogh
- **Wikimedia Commons**: High-resolution public domain images
  - https://commons.wikimedia.org/wiki/Vincent_van_Gogh
- **Artwork catalogs**: De la Faille (F numbers), JH numbers

## Directory Structure

```
open-museum/
├── AGENT_README.md          # This file — project overview
├── AGENTS.md                # Standing instructions for all agents
├── .project/
│   ├── agent-log.md         # Mandatory agent tracking table
│   ├── changelog.md         # Project changelog
│   └── todo.md              # Current task list
└── van-gogh/
    ├── README.md            # Collection-specific notes
    ├── catalog.json         # Master catalog of works
    └── scripts/             # Scraping & processing scripts
```

## Collections

### van-gogh/
- **Scope**: All known paintings, drawings, and watercolors by Vincent van Gogh
- **Copyright status**: Public domain worldwide (artist died 1890)
- **Target output**: `catalog.json` — structured data with title, date, medium, dimensions, current location, Wikipedia URL, Wikimedia Commons image URL, and catalog numbers (F/JH)

## Agent Workflow

1. Scrape structured data from Wikipedia's list of works
2. For each work, resolve Wikimedia Commons file links
3. Build and validate a master `catalog.json`
4. Cross-reference with biographical data for completeness

## Rules for Agents

See `AGENTS.md` for mandatory agent logging and behavioral instructions.
