# open-museum — Francisco Goya Collection

## Overview

This collection curates the paintings and print series of **Francisco Goya** (1746–1828), one of Spain's most influential painters and printmakers. The collection contains 844 works: 580 paintings spanning his early, court, crisis, war, and late/black painting eras, and 264 prints across his major series (*Los Caprichos*, *The Disasters of War*, *La Tauromaquia*, *Los disparates*, and the *Bulls of Bordeaux*).

## Data Schema

Each entry in `catalog.json` conforms to the following schema:

*   **`id`** — Sequential integer starting from 1.
*   **`slug`** — URL-safe slug for the work.
*   **`type`** — `"painting"` or `"print"`.
*   **`title`** — The common English title of the work.
*   **`title_disambig`** — Optional short string to distinguish duplicate titles (e.g. `1814 · Prado` or `Caprichos No. 1`).
*   **`date`** — Free-form date string (e.g., `"1777"`, `"1819 to 1823"`, `"c. 1771–74"`).
*   **`year_start`** / **`year_end`** / **`circa`** — Date triplet for chronological sorting and queries.
*   **`era`** — Chronological division of Goya's paintings:
    *   `early` — 1763–1774: Zaragoza and early tapestry cartoons.
    *   `court` — 1775–1792: Tapestry cartoons and rising status as a court portrait painter.
    *   `crisis` — 1793–1807: Illness, deafness, *Los Caprichos*, major portraits, and the *Majas*.
    *   `war` — 1808–1818: Peninsular War, *The Disasters of War*, *Second/Third of May*.
    *   `late` — 1819–1828: Quinta del Sordo (Black Paintings), Bordeaux exile.
*   **`series`** — Print series identification:
    *   `caprichos` — *Los Caprichos* (1797-1799)
    *   `disasters_of_war` — *The Disasters of War* (1810-1820)
    *   `tauromaquia` — *La Tauromaquia* (1815-1816)
    *   `disparates` — *Los disparates* (1815-1824)
    *   `bulls_of_bordeaux` — *Bulls of Bordeaux* (1825)
    *   `other_prints` — Miscellaneous prints
*   **`subject`** — Primary classification: `portrait`, `landscape`, `religious`, `genre`, `allegory`, `mythological`, `history`, `dark_painting`, `other`.
*   **`medium`** — Medium/technique (e.g. `"oil on canvas"`, `"Etching, aquatint and drypoint"`).
*   **`dimensions`** — Free-form dimension string.
*   **`current_location`** — Holding institution or collection (paintings only).
*   **`commons_filename`** — Filename on Wikimedia Commons.
*   **`image_url`** — High-resolution original file URL.
*   **`thumb_url`** — Thumbnail file URL (960px width).
*   **`commons_page`** — File detail page on Wikimedia Commons.
*   **`image_width`** / **`image_height`** / **`mime`** — Image dimensions and mime type.
*   **`famous`** — Boolean set to `true` for Goya's key masterpieces.
*   **`tier`** — Curation level (`famous` or absent).
*   **`provenance_url`** — Stables provenance URL (usually Wikipedia article or Commons file page).
*   **`harvest_method`** — `"wikipedia_list"`.

## Copyright Basis

Francisco Goya died in Bordeaux in **1828**. 
All of his works entered the public domain worldwide in the 19th century under the standard life + 70 years copyright rule (which expired in **1898**). 
All images in this collection are harvested from Wikimedia Commons and are confirmed to be in the public domain.
