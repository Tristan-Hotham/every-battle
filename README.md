# Every battle in history

Five thousand years of battles from Wikidata: 20,202 battle items, 13,712 of them with both a place and a date, from 3001 BCE to 2026. Where war happened century by century, how the centre of recorded war moved, the most fought-over places on Earth, the best-recorded wars, and how skewed the record is.

Interactive page: https://maps.tristanhotham.com/every-battle/
Paper: https://doi.org/10.5281/zenodo.23857870
Blog post: https://blog.tristanhotham.com/2026/10/31/every-battle/

## Headline results

- The record is recent: 77% of dated battles are after 1500 and 52% after 1800. The 19th century has the most (3,714), then the 20th (3,630); the busiest year is 1944 (319 battles). The 21st century so far has 35.4 recorded battles a year, close to the 19th century's 37.1.
- The centre of war (spherical median of each century's battles) lies in Greece in the 5th century BCE and in Italy under Rome; from the 5th to the 19th century it lies within 800 km of the Alps in every century but the 7th. In the 21st century it is in Syria.
- Most fought-over region (seven equal-area hexagons, 65,472 km2): Flanders, Artois and Brabant, 369 battles in 17 centuries. Longest fought over (one hexagon, 9,353 km2): Jerusalem, Gaza and the coastal plain, battles in 16 centuries. Belgium has the most battles per area of any country over 20,000 km2 (63.4 per 10,000 km2).
- Best-recorded wars: World War II (864 battle items, world war theatres grouped), World War I (532), the American Civil War (524). The War in the Vendee and the Chouannerie together have 191, more than the Thirty Years' War.
- Bias: Europe has 51% of mapped battles on 7% of the world's land. Only 79% of items are called a battle in their English label; 7.1% have no English label; only 551 of the 709 rows of Wikipedia's list of battles by casualties match a Wikidata battle item.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/05_build_site.py`; results, world outline and city names embedded; other page data loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/battles.csv` | All 20,202 Wikidata battle items: QID, English label, year (astronomical) and year text, century, era, point and where it came from, location, modern country, continent, at sea, kind, grouped war, all "part of" values, sitelinks. CC0 source; CC BY 4.0 here. |
| `data/battles_by_century.csv` | Dated and mapped battles per century, by continent, with median sitelinks. |
| `data/centre_of_war.csv` | The centre of war (spherical geometric median) per century. |
| `data/hexagons.csv` | Every occupied equal-area hexagon (60 km circumradius): battles, centuries, eras, first and last year, names for the top ones. |
| `data/wars.csv` | The 25 wars with the most battle items. |
| `data/casualties.csv` | Wikipedia's list of battles by casualties, parsed and matched to Wikidata (CC BY-SA 4.0, as its source). |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/points.json`, `data/hexes.json`, `data/casualties_map.json`, `data/sitelinks_by_year.json`, `data/site.json`, `data/world.json`, `data/cities.json` | Page data. |
| `code/` | Scripts, run in order (below), page, paper and blog templates, and `qa.js` (Playwright screenshots). |
| `release/` | Paper PDF and LaTeX source with figures, blog post, figures and meta, Zenodo files. |
| `reddit/` | Collage (`collage.py`, `every_battle.png`) and post text. |

## Method in brief

- Battles: every Wikidata item that is an instance of battle (Q178561) or a subclass, via QLever (23,069 rows reduced to 20,202 items). Point: the item's own coordinates (9,626), else its location's (5,142). Year: point in time, else start time; Wikidata's RDF uses astronomical years (0 = 1 BCE). Centuries are ordinal (1801 to 1900 is the 19th).
- Places: Natural Earth countries (nearest within 400 km for battles at sea); Russia west of the Urals and Turkey west of the Bosporus count as Europe.
- Hexagons on an equal-area grid in the Equal Earth projection (EPSG:8857); regions are a hexagon and its six neighbours, chosen greedily without overlap. Centre of war: spherical geometric median per century (20 or more battles).
- Wars: the "part of" value with most battles; theatres and campaigns of the two world wars grouped into the wars. Kinds: first matching word in the English label.
- Caveats: Wikidata items, not a census of battles; strong European, modern and language bias; inconsistent classes; approximate points and dates; legendary early battles.

## How to rerun

Needs Python 3 with pandas, numpy, shapely, pyproj, matplotlib, fontTools and Pillow, xelatex and pdftotext; Node with Playwright for QA. Raw inputs are read in place from `/home/claude/newdata/raw8/battles/` and `/home/claude/newdata/raw/geo/` (set in `code/common.py`). Intermediate files go to `/dev/shm/battles/work` (set `BATTMP` to change).

```
cd code
python3 01_clean.py        # one row per battle item
python3 02_geo.py          # world outline, country and city names
python3 03_casualties.py   # Wikipedia list of battles by casualties
python3 04_results.py      # results.json and page data
python3 05_build_site.py   # index.html
python3 06_figures.py      # header, blog and paper figures
python3 07_paper.py        # paper PDF
python3 08_readme.py       # README and LICENSE
python3 09_release.py      # blog post, Zenodo files, Reddit post
python3 ../reddit/collage.py
```

## Sources and licences

- Wikidata contributors (2026): items that are instances of battle (Q178561) and its subclasses, via QLever (https://qlever.cs.uni-freiburg.de/wikidata). CC0.
- Wikipedia contributors (2026) List of battles by casualties, English Wikipedia, revision 1382711824. CC BY-SA 4.0. `data/casualties.csv` is derived from it and shared under CC BY-SA 4.0.
- Natural Earth countries and populated places (public domain). Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Every battle in history: five thousand years of battles in Wikidata, where war happened and how skewed the record is. Zenodo. https://doi.org/10.5281/zenodo.23857870

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
