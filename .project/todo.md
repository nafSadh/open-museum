# TODO — open-museum

## Van Gogh Collection

### Data
- [x] Initialize project structure
- [x] Scrape list of works from Wikipedia (1,153 works)
- [x] Collect Wikimedia Commons image URLs (1,150 resolved, 99.7%)
- [x] Build master catalog (van-gogh/catalog.json)
- [x] Cross-reference with Wikidata for canonical metadata (911 matched, 79%)
- [ ] Add Van Gogh drawings (separate Wikipedia article: ~1,100 works)
- [ ] Enrich medium field for non-Hague painting sections (currently 12%)
- [ ] Surface Wikidata genres/depicts in gallery filters (currently fetched but unused in UI)

### Gallery UI
- [x] Build browseable HTML gallery (era/subject/famous filters + lightbox)
- [x] Sentence builder filter UI with inline expandable picks
- [x] Smooth colored glow on cards and lightbox (not shadow)
- [x] Sticky top bar on scroll
- [ ] Use high-res image URL in lightbox (currently uses thumb_url same as card)
- [ ] Mobile layout pass
- [ ] "Load more" → infinite scroll or pagination improvement

### Other artists
- [ ] Rembrandt collection
- [ ] Vermeer collection
