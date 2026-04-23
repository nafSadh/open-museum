# Changelog — open-museum

## 2026-04-21: Date-triplet backfill + year-aware sort + search-index builder

### Data
- Parsed loose date strings into the `year_start` / `year_end` / `circa` triplet across non-Western collections. 61 entries updated: behzad 32, utamaro 17, raja-ravi-varma 11, hokusai 1.
- Parser covers century expressions with modifiers ("First half of 16th century", "late 19th century", "end of the 15th century"), century ranges ("15th–16th centuries", "Late 19th/Early 20th Century"), Roman numerals ("XV век"), and Japanese era names (寛政6年-7年頃 → Kansei 6–7 = 1794–1795, circa).
- Future-dated outliers (`c. 3580`, `c. 2313`) and pure unknowns (`"Unknown date"`, `"—"`) correctly refused — year triplet stays null.

### Tooling
- New `scripts/build_search_index.py` — reproduces the existing `assets/search-index.json` shape from the 18 catalogs. Previously generated one-shot; now a script.
- Regenerated `assets/search-index.json`; picks up the 61 new `y` values.

### UI
- `applyFilters` in all 18 gallery `index.html` files: year-midpoint tiebreaker inserted between tier rank and id. Within each tier, entries now sort chronologically rather than by catalog id. Nulls sort last (9999 sentinel); ranges sort by the center of `year_start`..`year_end`.

### Project hygiene
- `.project/todo.md` rewritten to reflect reality (Leonardo, Mary Cassatt, Abanindranath Tagore, Caravaggio all shipped but unchecked; completed items separated from open ones).
- `.project/audit-2026-04-21.md` supersedes `audit-2026-04-20.md`. All previous blocker-level findings resolved. Remaining items are curation-level.

---

## 2026-04-05 → 2026-04-20: Expansion phase (not previously logged here)

Captured in `.project/agent-log.md` (rows 8–47) rather than this changelog. High-level milestones:

- Shipped 17 additional artist collections (all except Van Gogh): Titian, Monet, Rembrandt, Vermeer, Degas, Hokusai, Hiroshige, Utamaro, Kuniyoshi, Raja Ravi Varma, Amrita Sher-Gil, Xu Beihong, Behzad, Leonardo da Vinci (1,697 entries via Commons crawl), Mary Cassatt, Caravaggio, Abanindranath Tagore.
- Schema evolution: `wikipedia_url` → `provenance_url` migration across all collections; `source` string → `harvest_method` (lineage, not URL).
- Comprehensive 2026-04-20 audit; 99.98% image-URL liveness sweep; deduplication pass (−20 near-duplicate entries across monet/rembrandt/raja-ravi-varma).
- Cross-collection search + tier-based default sort across all 18 galleries (commit aec7399).
- Manual "famous" + "well_known" curation across all 18 collections; research-grounded per-artist scaling.

---

## 2026-04-04 (session 2): Gallery UI design refinement

### Sentence builder filter UI
- Replaced pill/dropdown filter bar with a **sentence builder** — natural language that expands inline on hover
- Collapsed state reads: `showing 146 famous works from any era of any subject`
- On hover, all sections expand simultaneously (`.sentence:hover` not `.exp:hover`) — prevents reflow/jitter when moving between sections
- Each filter group uses `.exp-picks` with `.pick` buttons; active = cadmium gold, inactive = dim italic
- Multi-select for era and subject (Sets), single-select for scope (famous/all)
- `any` pick button added to type, era, subject — acts as "clear all" for that group

### Summary text wording decisions
- Scope: "famous" shown when active; hidden entirely when "all" (reads "showing 329 works" not "showing 329 all works")
- Era: summary includes the word "era"/"eras" — e.g. "from Arles era" is unambiguous (vs "from Arles" which looks like a place not a period)
- Subject: "any subject" / "landscapes" / "landscapes and portraits" — no suffix needed, subjects are self-describing
- Type: "works" as the neutral default in collapsed state

### Visual polish
- **Card glow**: dark backgrounds need colored glow not shadow — 3-layer cobalt/cyan `box-shadow` with no x/y offset
- **Lightbox glow**: 7-layer smooth cobalt/cyan falloff (4px → 260px), replacing harsh yellow-black shadow
- **Lightbox text**: bumped title to `clamp(1.1rem, 2.8vw, 1.6rem)`, meta to `0.72rem`, links to `0.65rem`
- **Underlines on sentence summaries**: bumped from `rgba(..., 0.25)` to `0.5` alpha for readability
- **`open museum` link**: was `--text-lo` (#403828) — invisible on dark bg. Fixed to `--text-mid`

### Sticky top bar
- Appears after scrolling past the hero's stroke divider
- Contains: `← open museum` link | `Van Gogh` title (click = scroll to top) | filtered count (far right)
- CSS: `position: fixed; z-index: 20`, `backdrop-filter: blur(12px)`, slides in via `translateY(-100%)` → `translateY(0)` + opacity

### CSS patterns worth reusing
- `.sentence:hover .exp-picks` — hovering the parent expands ALL children at once, no layout shift when moving mouse between sections
- `.exp-hide-on-hover` — static connector words ("from", "of") that disappear on hover, replaced by labels inside expanded picks
- Multi-layer `box-shadow` with `0 0 Xpx rgba(color, alpha)` and decreasing alpha = smooth colored glow on dark backgrounds (no harsh edge)

---

## 2026-04-04: Project initialized
- Created `.project/` tracking directory
- Created `AGENT_README.md`, `AGENTS.md`
- Created `van-gogh/` subdirectory for Van Gogh public domain artwork collection
- Goal: collect all Van Gogh artworks (public domain) with Wikimedia Commons links
