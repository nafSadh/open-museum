# Changelog — open-museum

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
