"""README.md and LICENSE, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
F = R["flanders"]; H = R["hex_cent"][0]
readme = f"""# Every battle in history

Five thousand years of battles from Wikidata: {R['n']:,} battle items, {R['n_map']:,} of them with both a place and a date, from {R['first']['year_text']} to 2026. Where war happened century by century, how the centre of recorded war moved, the most fought-over places on Earth, the best-recorded wars, and how skewed the record is.

Interactive page: https://maps.tristanhotham.com/{SLUG}/
Paper: https://doi.org/{{10.5281/zenodo.23857870}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/every-battle/}}

## Headline results

- The record is recent: {R['pct_since1500']:.0f}% of dated battles are after 1500 and {R['pct_since1800']:.0f}% after 1800. The 19th century has the most ({R['c19']:,}), then the 20th ({R['c20']:,}); the busiest year is {R['peak_year']} ({R['peak_year_n']} battles). The 21st century so far has {R['c21_per_year']:.1f} recorded battles a year, close to the 19th century's {R['c19_per_year']:.1f}.
- The centre of war (spherical median of each century's battles) lies in Greece in the 5th century BCE and in Italy under Rome; from the 5th to the 19th century it lies within 800 km of the Alps in every century but the 7th. In the 21st century it is in {R['centre_c21_place']}.
- Most fought-over region (seven equal-area hexagons, {R['region_km2']:,.0f} km2): {F['name']}, {F['n']} battles in {F['cent']} centuries. Longest fought over (one hexagon, {R['hex_km2']:,.0f} km2): {H['name']}, battles in {H['cent']} centuries. Belgium has the most battles per area of any country over 20,000 km2 ({R['belgium']['per10k']:.1f} per 10,000 km2).
- Best-recorded wars: World War II ({R['ww2']['n']} battle items, world war theatres grouped), World War I ({R['ww1']['n']}), the American Civil War ({R['acw']['n']}). The War in the Vendee and the Chouannerie together have {R['vendee']}, more than the Thirty Years' War.
- Bias: Europe has {R['europe_pct']:.0f}% of mapped battles on {R['europe_land_pct']:.0f}% of the world's land. Only {R['kinds'][0]['pct']:.0f}% of items are called a battle in their English label; {R['pct_nolabel']:.1f}% have no English label; only {R['cas']['matched']} of the {R['cas']['n']} rows of Wikipedia's list of battles by casualties match a Wikidata battle item.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/05_build_site.py`; results, world outline and city names embedded; other page data loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/battles.csv` | All {R['n']:,} Wikidata battle items: QID, English label, year (astronomical) and year text, century, era, point and where it came from, location, modern country, continent, at sea, kind, grouped war, all "part of" values, sitelinks. CC0 source; CC BY 4.0 here. |
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

- Battles: every Wikidata item that is an instance of battle (Q178561) or a subclass, via QLever ({R['n_rows']:,} rows reduced to {R['n']:,} items). Point: the item's own coordinates ({R['n_own']:,}), else its location's ({R['n_locxy']:,}). Year: point in time, else start time; Wikidata's RDF uses astronomical years (0 = 1 BCE). Centuries are ordinal (1801 to 1900 is the 19th).
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
- Wikipedia contributors (2026) List of battles by casualties, English Wikipedia, revision {R['cas']['revid']}. CC BY-SA 4.0. `data/casualties.csv` is derived from it and shared under CC BY-SA 4.0.
- Natural Earth countries and populated places (public domain). Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Every battle in history: five thousand years of battles in Wikidata, where war happened and how skewed the record is. Zenodo. https://doi.org/{{10.5281/zenodo.23857870}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in readme.replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = open("/home/claude/studies/piracy-hotspots/LICENSE", encoding="utf-8").read().split("Text, figures and derived data")[0] + """Text, figures and derived data

The text, figures, page and derived data are licensed under the Creative Commons Attribution 4.0 International licence
(CC BY 4.0, https://creativecommons.org/licenses/by/4.0/), except data/casualties.csv and data/casualties_map.json, which
are derived from English Wikipedia's "List of battles by casualties" and are licensed under CC BY-SA 4.0
(https://creativecommons.org/licenses/by-sa/4.0/). The battle data are derived from Wikidata (CC0). Please credit those
sources as well as this work.
"""
assert "MIT License" in lic
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
print("README", len(readme.split()), "words")
