"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json, cities) is embedded; data/points.json, hexes.json,
casualties_map.json and sitelinks_by_year.json are loaded by the page. 10.5281/zenodo.23857870 and https://blog.tristanhotham.com/2026/10/31/every-battle/ stay as placeholders."""
import json
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")

# facts stated in words on the page (and in the blog and paper)
cc = {r["c"]: r for r in R["centuries"]}
assert R["peak_century"]["c"] == 19 and cc[19]["n"] > cc[20]["n"] > cc[18]["n"]
assert R["peak_year"] == 1944 and R["top_years"][1][0] == 1863
assert cc[2]["by_cont"][1] > cc[2]["by_cont"][0] and cc[3]["by_cont"][1] > cc[3]["by_cont"][0]        # more Asian than European battles
E = R["eras"]
assert E[0]["top_cont"] == 1 and all(E[i]["top_cont"] == 0 for i in (1, 2, 3, 4, 6)) and E[7]["top_cont"] == 1   # Asia, Europe ..., Asia
assert E[7]["by_cont"][1] + E[7]["by_cont"][2] > .8 * E[7]["n_map"]
assert R["pct_americas_19"] > cc[19]["pct_europe"]
W = {w["name"]: w["n"] for w in R["wars"]}
assert W["American Revolutionary War"] > W["Napoleonic Wars"] and W["Greek War of Independence"] > W["Hundred Years' War"] and W["Polish-Soviet War"] > W["Korean War"]
assert R["vendee"] > W["Thirty Years' War"]
assert [w["name"] for w in R["wars"][:3]] == ["World War II", "World War I", "American Civil War"]
assert R["sl_med_ancient"] > R["sl_med_modern"]
assert abs(R["hex_km2"] - 9251) < 400 and 1.9 < R["region_km2"] / 30689 < 2.3          # about the size of Cyprus; about twice Belgium
assert R["hex_cent"][0]["era"] == 8 and R["hex_cent"][2]["name"] == "Rome" and R["hex_cent"][1]["name"].startswith("Milan")
assert [m["label"] for m in R["most_linked"][:3]] == ["Battle of Stalingrad", "Battle of Waterloo", "Attack on Pearl Harbor"]
assert R["countries_dense"][0]["iso"] == "BEL"
assert R["cas"]["asia_pct"] < 30 and R["cas"]["europe_pct"] > 60


def fill(tpl):
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = [x for x in re.findall(r"\{\{[^}]*\}\}", html) if x not in ("10.5281/zenodo.23857870", "https://blog.tristanhotham.com/2026/10/31/every-battle/")]
    assert not left, left[:5]
    return html


def build():
    html = fill(open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read())
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
