# Evaluation of Data Sources: Museum APIs vs Wikimedia

**Date**: 2026-04-05

## Context
During the expansion of the Van Gogh catalog, we reviewed whether to integrate public domain data from external museum APIs (such as The Metropolitan Museum of Art, Art Institute of Chicago, Rijksmuseum, and Europeana) instead of relying solely on Wikipedia and Wikimedia Commons.

## Considered Sources

1. **Wikimedia / Wikipedia (Current Approach)**
   - **Pros**: Easy to scrape, contains standard metadata (Year, Medium, Dimensions) for famous works, low maintenance.
   - **Cons**: Crowd-sourced text lacking curatorial authority, focuses mostly on major works, image quality can vary.

2. **The Met / Art Institute of Chicago (Open APIs - No Auth)**
   - **Pros**: Curatorial text, very high-resolution images (IIIF for AIC), CC0/Public Domain verified.
   - **Cons**: Matching works is difficult without standard canonical identifiers (like Van Gogh's F-numbers) present in their easy-to-query schemas.

3. **Rijksmuseum / Europeana (Requires API Keys)**
   - **Pros**: Incredibly detailed metadata (e.g., extracted color palettes from Rijksmuseum), canonical catalog numbers are tracked, uncovers the "long tail" of obscure works and sketches across small European institutions.
   - **Cons**: Requires account creation for keys, complex data alignment.

## Decision / Outcome
**Outcome**: We decided to stick with the primary **Wikipedia / Wikidata** architecture for the baseline system, rather than building and maintaining multiple separate museum API scrapers. 

**Reasoning**:
While the high-res imagery and curatorial notes of Museum APIs are incredibly appealing for a "premium" feel, maintaining 3-4 separate API scrapers alongside fuzzy-matching algorithms (to solve the "multiple Sunflowers/Self-Portraits" naming problem) introduces too much engineering overhead. For a clean, basic visual gallery, the Wikidata/Wikipedia approach provides the best balance of data completeness (basic metadata) and low maintenance.

If a specific need arises in the future for deep curatorial essays or color-based filtering, we will revisit adding the *Rijksmuseum* API for specific high-value collections.
