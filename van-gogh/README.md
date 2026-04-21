# Van Gogh — Public Domain Artwork Collection

## Overview

A comprehensive catalog of **Vincent van Gogh's** artworks with links to public domain images on Wikimedia Commons.

- **Artist**: Vincent Willem van Gogh (1853–1890)
- **Copyright status**: Public domain worldwide (died 1890; 70+ year rule satisfied globally)
- **Estimated works**: ~2,100 artworks (860+ oil paintings, 1,300+ drawings/watercolors/sketches)

## Sources

- [List of works by Vincent van Gogh](https://en.wikipedia.org/wiki/List_of_works_by_Vincent_van_Gogh) — Wikipedia
- [Vincent van Gogh](https://en.wikipedia.org/wiki/Vincent_van_Gogh) — Wikipedia biography
- [Vincent van Gogh on Wikimedia Commons](https://commons.wikimedia.org/wiki/Vincent_van_Gogh)

> **Note on Museum APIs**: We evaluated integrating APIs from The Met, Art Institute of Chicago, and Rijksmuseum. We decided to stick with Wikipedia/Wikidata as the primary source to minimize scraping complexity and fuzzy-matching overhead. See `../.project/api-sources-evaluation.md` for details.

## Catalog Schema

Each entry in `catalog.json` follows this structure:

```json
{
  "title": "The Starry Night",
  "title_original": "De sterrennacht",
  "date": "1889-06",
  "medium": "Oil on canvas",
  "dimensions": "73.7 cm × 92.1 cm",
  "location": "Museum of Modern Art, New York",
  "f_number": "F612",
  "jh_number": "JH1731",
  "provenance_url": "https://en.wikipedia.org/wiki/The_Starry_Night",
  "commons_url": "https://commons.wikimedia.org/wiki/File:Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
  "image_url": "https://upload.wikimedia.org/wikipedia/commons/...",
  "type": "painting"
}
```

## Files

- `catalog.json` — Master catalog of all works
- `scripts/` — Scraping and data processing scripts
