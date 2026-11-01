"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo), Reddit post text (reddit/post.md).
10.5281/zenodo.23857870, https://doi.org/10.5281/zenodo.23857870 and https://blog.tristanhotham.com/2026/10/31/every-battle/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Every_Battle_in_History"

# the page build checks the shared facts; these are numbers written in words or alt text in the blog
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "05_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
assert R["c19"] == 3714 and 3550 <= R["c20"] <= 3650
assert [g["n"] for g in R["regions"][:4]] == [369, 260, 244, 205]
assert [w["n"] for w in R["wars"][:5]] == [864, 532, 524, 221, 155]
assert [round(c["pct"]) for c in R["by_cont"]] == [51, 24, 9, 11, 4, 1] and [round(x) for x in R["land_pct"]] == [7, 33, 22, 18, 13, 6]
q = {r[0]: r for r in R["sl_quant"]}
assert all(6 <= q[c][2] <= 10 for c in (-5, -4, -3)) and all(q[c][2] in (3, 4) for c in range(11, 22)) and all(24 <= q[c][3] <= 27 for c in (-5, -4, -3, -2)) and all(11 <= q[c][3] <= 16 for c in range(11, 22))
assert R["hex_cent"][1]["name"].startswith("Milan") and R["centres"][-1]["place"] == "Syria"
assert {w["name"] for w in R["wars"] if w["cont"] == 1} == {"Korean War", "Vietnam War", "Syrian Civil War", "War in Afghanistan (2001 to 2021)"}

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Every battle in history, mapped",
        "slug": "every-battle",
        "excerpt": f"Wikidata knows of {R['n']:,} battles. I mapped the {R['n_map']:,} with a place and a date, from {R['first']['year_text']} to 2026, to find the most fought-over places on Earth, follow the centre of war century by century, and see how much the famous map is really a map of who wrote things down.",
        "seo_description": f"{R['n_map']:,} battles mapped from Wikidata, {R['first']['year_text']} to 2026: the most fought-over places, the centre of war, and the bias in the record.",
        "tags": ["battles", "military history", "maps", "data visualisation", "Wikidata", "Wikipedia", "historical GIS", "open data"],
        "header_alt": f"Title card reading 'Every battle in history' in black and red on pale paper, beside a map of Europe, North Africa and the Middle East covered in small dots coloured by era, densest in western Europe and the Levant. Text: {R['n_map']:,} battles with a place and a date, {R['first']['year_text']} to 2026; most fought-over: Flanders, {R['flanders']['n']} battles; Europe has {R['europe_pct']:.0f}% of battles and {R['europe_land_pct']:.0f}% of the land."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/every-battle_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"every-battle/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        if os.path.exists(os.path.join(ROOT, fn)):
            z.write(os.path.join(ROOT, fn), f"every-battle/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "every-battle/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("~", " ")
zmeta = {"title": "Every Battle in History: Five Thousand Years of Battles in Wikidata, Where War Happened, the Most Fought-Over Places, and How Skewed the Record Is",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/every-battle/}}.</p><p>Data: Wikidata (CC0), all items that are instances of battle (Q178561) or its subclasses, via QLever; English Wikipedia, List of battles by casualties (CC BY-SA 4.0; the derived casualty table is shared under CC BY-SA 4.0); Natural Earth.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["battles", "military history", "Wikidata", "Wikipedia", "knowledge gaps", "historical GIS", "spatial analysis", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.wikidata.org/wiki/Q178561", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://en.wikipedia.org/wiki/List_of_battles_by_casualties", "relation": "isDerivedFrom", "resource_type": "other"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")

# Reddit post text
F = R["flanders"]
post_md = f"""## Title

[OC] Every battle in history: {R['n_map']:,} battles from Wikidata with a place and a date, {R['first']['year_text']} to 2026. The most fought-over region is Flanders ({F['n']} battles in {F['cent']} centuries), and Europe has {R['europe_pct']:.0f}% of all battles on {R['europe_land_pct']:.0f}% of the land

## Body

I took every Wikidata item that is an instance of "battle" or one of its subclasses ({R['n']:,} items) and mapped the {R['n_map']:,} that have both coordinates and a date. The record is mostly recent: {R['pct_since1800']:.0f}% of dated battles are after 1800, and the 19th century has the most ({R['c19']:,}). To compare places fairly I counted battles on an equal-area hexagon grid: the most fought-over region is Flanders, Artois and Brabant (Caesar, the Golden Spurs, Marlborough, Waterloo, Ypres), then western France (mostly the War in the Vendee, which French Wikipedia covers skirmish by skirmish), then the southern Levant. The hexagon around Jerusalem and Gaza has battles in {R['hex_cent'][0]['cent']} different centuries. Big caveat: this is a map of what Wikipedia editors have written up as much as of war. Europe has {R['europe_pct']:.0f}% of the mapped battles on {R['europe_land_pct']:.0f}% of the world's land, only {R['kinds'][0]['pct']:.0f}% of the items are actually called a battle (the rest are sieges, raids, skirmishes and so on), and some famous fights such as the Siege of Leningrad are not typed as battles at all. Interactive map with a time slider: https://maps.tristanhotham.com/every-battle/

## Source comment

Sources: Wikidata (CC0), all items that are instances of battle (Q178561) or its subclasses, via the QLever SPARQL endpoint; English Wikipedia, List of battles by casualties (CC BY-SA 4.0); Natural Earth outlines (public domain).

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map. Hexagons are on an equal-area grid in the Equal Earth projection.

Interactive version: https://maps.tristanhotham.com/every-battle/
Paper: {{https://doi.org/10.5281/zenodo.23857870}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/every-battle/}}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in post_md, bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post_md)
print("reddit title chars", len(post_md.splitlines()[2]))
