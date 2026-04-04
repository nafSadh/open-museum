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
- Catalog entries must include provenance (Wikipedia article URL at minimum)
- Dates should use ISO 8601 format (YYYY or YYYY-MM)
- Titles should match the most common English-language usage, with original Dutch/French noted where relevant

## Scripts

- All scraping/processing scripts go in `{collection}/scripts/`
- Scripts should be idempotent — safe to re-run without duplicating data
- Output structured data as JSON

## Copyright

- Only collect works that are verifiably in the **public domain**
- Van Gogh (d. 1890): PD worldwide
- Always note the copyright basis in collection README
