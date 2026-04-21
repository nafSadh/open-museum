# open-museum — Standing Instructions for All Agents

These instructions apply to every agent operating in this repo — Claude, Gemini, or any other orchestrator or sub-agent.

---

## Agent Tracking (MANDATORY)

**Every time a sub-agent is spawned, it must be logged in `.project/agent-log.md`.**

This applies to:
- Claude background agents (`run_in_background: true`)
- Any other automated agent or subprocess
- Scripts that perform bulk operations

### What to log

When spawning an agent, add a row to the tracking table in `.project/agent-log.md`:

```markdown
| # | Date | Agent ID | Task | Status | Output |
|---|------|----------|------|--------|--------|
| N | YYYY-MM-DD | short-id | What it's doing | running / done / failed | path/to/output or notes |
```

Update the row when the agent completes (status -> done/failed, add output path or summary).

### Format

`.project/agent-log.md` uses this structure:

```markdown
# Agent Tracking — open-museum

## Active Agents
| # | Date | Agent ID | Task | Status | Output |

## Completed Agents
| # | Date | Agent ID | Task | Status | Output |
```

---

## Data Quality Standards

- All image links must point to **Wikimedia Commons** or other verified public domain sources
- Catalog entries must include provenance via `provenance_url` (see Schema Policy below)
- Titles should match the most common English-language usage, with original-language titles noted where relevant (e.g. `title_original`, `japanese_title`)

## Schema Policy

The project spans very different art traditions (Western oil painting, ukiyo-e prints, Persian miniatures, Indian calendar art). Rather than force one schema on all collections, each collection owns its own schema, and shared fields follow the conventions below. **Code and schema duplication across collections is preferred over premature abstraction** when a uniform schema would misrepresent the works.

### Shared fields (when applicable)

**`provenance_url`** — single field carrying a URL that provenance-stamps the entry. Populate with the first available source in this priority:
1. Wikipedia article URL
2. Wikimedia Commons page URL (gallery or file page)
3. Any other stable public-domain source

Do not use one per source; pick the best available and put it in `provenance_url`. (This field replaces the earlier `wikipedia_url` — a migration pass renamed it across all collections.)

**`harvest_method`** — optional tag documenting *how* the entry was collected (e.g. `wikipedia_gallery`, `commons_category`, `manual`). This is lineage metadata, **not** a URL and **not** provenance. Keep separate from `provenance_url`. (This field replaces the earlier `source` string.)

**Date fields** — art-historical dates legitimately carry uncertainty, ranges, and monthly precision that ISO 8601 cannot express. Collections should carry **a triplet**:
- `date` — free-form display string (e.g. `"c. 1654–55"`, `"August 1882"`, `"c. 1500"`); preserves art-historical nuance.
- `year_start` — integer, earliest plausible year. Null if unknown.
- `year_end` — integer, latest plausible year. Equal to `year_start` for single-year works. Null if unknown.
- `circa` — boolean, true if `c.` / `circa` applied to the original.

UIs should sort/filter on `year_start`/`year_end` and display `date`.

### Per-collection fields

Fields like `dimensions`, `current_location`, `medium`, `technique`, `series`, `japanese_title`, `w_number`, `f_number` are collection-specific. Each collection's `README.md` documents which fields are required/optional for that collection. Do not retrofit fields into a collection if they don't fit the underlying art tradition (e.g. `current_location` is ill-defined for print editions that exist in many museums simultaneously).

## Scripts

- All scraping/processing scripts go in `{collection}/scripts/`
- Scripts should be idempotent — safe to re-run without duplicating data
- Output structured data as JSON

## Copyright

- Only collect works that are verifiably in the **public domain**
- Always note the copyright basis in the collection `README.md` (death year + applicable rule + year the works entered PD)
- Reference examples: Van Gogh (d. 1890, PD worldwide); Monet (d. 1926, PD worldwide); Amrita Sher-Gil (d. 1941, PD in life+70 jurisdictions since 2012); Xu Beihong (d. 1953, PD in life+70 jurisdictions since 2024)
