"""Every number quoted anywhere (page, paper, blog, collage, post) goes into data/results.json. Also writes the page data
(data/site.json, data/points.json, data/hexes.json, data/casualties_map.json) and tidy tables (data/*.csv)."""
import pandas as pd
from shapely.geometry import shape, Point
from shapely.ops import transform as stransform
from shapely.strtree import STRtree
from pyproj import Transformer
from common import *

B = pd.read_pickle(f"{WORK}/battles.pkl")
CM = jload(f"{WORK}/clean_meta.json")
CASM = jload(f"{WORK}/cas_meta.json")
CAS = pd.read_csv(f"{DATA}/casualties.csv", keep_default_na=False, na_values=[""])
pc = lambda a, b: 100.0 * a / b if b else 0.0
R = {"meta": {"page": PAGE, "repo": REPO, "slug": SLUG, "retrieved": "2026"}}
N = len(B)
hasxy = B.lat.notna(); hasy = B.year.notna()
M = B[hasxy & hasy].copy()                       # mapped and dated: the map, hexagons, centres, continents
M["year"] = M.year.astype(int); M["century"] = M.century.astype(int); M["era"] = M.era.astype(int)
Dd = B[hasy].copy(); Dd["year"] = Dd.year.astype(int); Dd["century"] = Dd.century.astype(int)
NM = len(M)

# ---------- the record ----------
R["n_rows"] = CM["n_rows"]; R["n"] = N
R["n_xy"] = int(hasxy.sum()); R["n_own"] = int((B.coord_from == "own").sum()); R["n_locxy"] = int((B.coord_from == "location").sum())
R["n_dated"] = int(hasy.sum()); R["n_map"] = NM
R["pct_xy"] = pc(R["n_xy"], N); R["pct_dated"] = pc(R["n_dated"], N); R["pct_map"] = pc(NM, N)
R["n_nolabel"] = int((B.label == "").sum()); R["pct_nolabel"] = pc(R["n_nolabel"], N)
R["n_nolabel_map"] = int((M.label == "").sum())
R["n_war"] = int((B.war != "").sum()); R["pct_war"] = pc(R["n_war"], N)
R["n_conflicts"] = int(B.loc[B.conflict != "", "conflict"].nunique())
R["n_bce"] = int((Dd.year <= 0).sum()); R["n_bce_map"] = int((M.year <= 0).sum())
R["n_since1800"] = int((Dd.year >= 1800).sum()); R["pct_since1800"] = pc(R["n_since1800"], R["n_dated"])
R["n_since1500"] = int((Dd.year >= 1500).sum()); R["pct_since1500"] = pc(R["n_since1500"], R["n_dated"])
first = Dd.sort_values(["year", "sitelinks"], ascending=[True, False]).iloc[0]
R["first"] = {"label": first.label, "year": int(first.year), "year_text": ytxt(int(first.year)), "qid": first.qid}
R["n_before_2000bce"] = int((Dd.year <= -1999).sum())
R["sitelinks_median"] = float(B.sitelinks.median()); R["sitelinks_1"] = int((B.sitelinks <= 1).sum()); R["pct_sl_le1"] = pc(R["sitelinks_1"], N)
R["kinds"] = [{"name": k[0], "n": int((B.kind == i).sum()), "pct": pc((B.kind == i).sum(), N)} for i, k in enumerate(KINDS)]
R["n_not_battle"] = N - R["kinds"][0]["n"]; R["pct_not_battle"] = pc(R["n_not_battle"], N)
R["n_sea"] = int((M.at_sea == True).sum()); R["pct_sea"] = pc(R["n_sea"], NM)
R["n_ocean"] = int(M.cont.isna().sum())
assert first.year == -3000

# ---------- centuries ----------
C0, C1 = int(Dd.century.min()), int(Dd.century.max())
cents = [c for c in range(C0, C1 + 1) if c != 0]
cr = []
for c in cents:
    d = Dd[Dd.century == c]; m = M[M.century == c]
    a = (c - 1) * 100 + 1 if c > 0 else c * 100 + 1      # first astronomical year of the century
    yrs = 100 if c < 21 else 2026 - 2000
    cr.append({"c": c, "name": cname(c), "short": cshort(c), "y0": a, "n": int(len(d)), "n_map": int(len(m)), "per_year": len(d) / yrs,
               "by_cont": [int((m.cont == k).sum()) for k in range(len(CONTS))], "ocean": int(m.cont.isna().sum()),
               "sl_median": float(d.sitelinks.median()) if len(d) else None, "sl_mean": float(d.sitelinks.mean()) if len(d) else None,
               "pct_europe": pc((m.cont == 0).sum(), len(m)) if len(m) >= 10 else None,
               "by_kind": [int((d.kind == k).sum()) for k in range(len(KINDS))]})
R["centuries"] = cr
big = max(cr, key=lambda r: r["n"])
R["peak_century"] = {"name": big["name"], "n": big["n"], "c": big["c"]}
fast = max(cr, key=lambda r: r["per_year"])
R["fastest_century"] = {"name": fast["name"], "per_year": fast["per_year"], "n": fast["n"]}
cc = {r["c"]: r for r in cr}
R["c19"] = cc[19]["n"]; R["c20"] = cc[20]["n"]; R["c21"] = cc[21]["n"]; R["c18"] = cc[18]["n"]
R["c19_per_year"] = cc[19]["per_year"]; R["c20_per_year"] = cc[20]["per_year"]; R["c21_per_year"] = cc[21]["per_year"]
R["c19_20_pct"] = pc(cc[19]["n"] + cc[20]["n"], R["n_dated"])
yc = Dd.groupby("year").size()
R["peak_year"] = int(yc.idxmax()); R["peak_year_n"] = int(yc.max())
dec = Dd[Dd.year >= 1500].groupby(Dd.year // 10 * 10).size()
R["peak_decade"] = int(dec.idxmax()); R["peak_decade_n"] = int(dec.max())
R["decades"] = [[int(k), int(v)] for k, v in dec.items()]
top_yr = yc.sort_values(ascending=False).head(6)
R["top_years"] = [[int(k), int(v)] for k, v in top_yr.items()]
# battles per year, for the year chart (1500 onwards, mapped and dated, by continent)
YC = pd.crosstab(M[M.year >= 1500].year, M[M.year >= 1500].cont.fillna(-1).astype(int))
R["years_1500"] = [[int(y)] + [int(YC.loc[y].get(k, 0)) if y in YC.index else 0 for k in range(len(CONTS))] for y in range(1500, 2027)]

# ---------- continents through time ----------
eras = []
for i, (n, a, b) in enumerate(ERAS):
    m = M[M.era == i]; d = Dd[(Dd.year >= a) & (Dd.year <= b)]
    bc = [int((m.cont == k).sum()) for k in range(len(CONTS))]
    eras.append({"name": n, "short": ESHORT[i], "a": a, "b": b, "n": int(len(d)), "n_map": int(len(m)), "by_cont": bc,
                 "pct_cont": [pc(v, len(m)) for v in bc], "top_cont": int(np.argmax(bc)),
                 "sl_median": float(d.sitelinks.median())})
R["eras"] = eras
R["europe_pct"] = pc((M.cont == 0).sum(), NM)
R["by_cont"] = [{"name": c[0], "n": int((M.cont == k).sum()), "pct": pc((M.cont == k).sum(), NM)} for k, c in enumerate(CONTS)]
# land area by continent (Natural Earth, Equal Earth projection), for comparison only
EE = Transformer.from_crs(4326, 8857, always_xy=True)
W = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
carea, area_c = {}, np.zeros(len(CONTS))
for f in W["features"]:
    p = f["properties"]; g = stransform(EE.transform, shape(f["geometry"]))
    carea[iso_of(p)] = (p["NAME_EN"] or p["NAME"], g.area / 1e6)
    k = CONT_OF_NE.get(p["CONTINENT"])
    if k is not None:
        area_c[k] += g.area / 1e6
# Natural Earth puts all of Russia in Europe: only Russia west of the Urals (about 3.95 million km2) counts as Europe here,
# as in the battle assignment, so the rest moves to Asia
ru_asia = carea["RUS"][1] - 3.95e6
area_c[0] -= ru_asia; area_c[1] += ru_asia
R["land_pct"] = [pc(a, area_c.sum()) for a in area_c]
R["europe_land_pct"] = R["land_pct"][0]
R["europe_x_land"] = R["europe_pct"] / R["europe_land_pct"]
R["asia_pct"] = R["by_cont"][1]["pct"]; R["africa_pct"] = R["by_cont"][2]["pct"]
R["europe_pct_19"] = cc[19]["pct_europe"]; R["europe_pct_21"] = cc[21]["pct_europe"]
R["n_americas_19"] = cc[19]["by_cont"][3] + cc[19]["by_cont"][4]
R["pct_americas_19"] = pc(R["n_americas_19"], cc[19]["n_map"])
R["asia_pct_21"] = pc(cc[21]["by_cont"][1], cc[21]["n_map"]); R["africa_pct_21"] = pc(cc[21]["by_cont"][2], cc[21]["n_map"])

# ---------- the centre of war: spherical geometric median per century ----------
la, lo = np.radians(M.lat.values), np.radians(M.lon.values)
P3 = np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]


def gmed(V):
    m = V.mean(0); m /= np.linalg.norm(m)
    for _ in range(500):
        d = np.arccos(np.clip(V @ m, -1, 1)); w = 1 / np.maximum(d, 1e-7)
        m2 = (V * w[:, None]).sum(0); m2 /= np.linalg.norm(m2)
        if np.linalg.norm(m2 - m) < 1e-12:
            break
        m = m2
    return m


geoms = [shape(f["geometry"]) for f in W["features"]]; gnames = [f["properties"]["NAME_EN"] or f["properties"]["NAME"] for f in W["features"]]
tree = STRtree(geoms)


def place(lat, lon):
    p = Point(lon, lat); hit = tree.query(p, predicate="intersects")
    if len(hit):
        return gnames[int(hit[0])], False
    return gnames[int(tree.nearest(p))], True


centres = []
for c in cents:
    k = (M.century == c).values
    if k.sum() < 20:
        continue
    m = gmed(P3[k]); lat, lon = float(np.degrees(np.arcsin(m[2]))), float(np.degrees(np.arctan2(m[1], m[0])))
    dist = np.degrees(np.arccos(np.clip(P3[k] @ m, -1, 1))) * 111.195
    nm, sea = place(lat, lon)
    centres.append({"c": c, "name": cname(c), "short": cshort(c), "n": int(k.sum()), "lat": round(lat, 3), "lon": round(lon, 3),
                    "median_km": float(np.median(dist)), "within1000_pct": pc((dist <= 1000).sum(), k.sum()), "place": nm, "at_sea": sea})
R["centres"] = centres
CE = {r["c"]: r for r in centres}
R["centre_first_c"] = centres[0]["name"]
R["n_centre_centuries"] = len(centres)
# how far the centre moved: from the 5th century BCE to the 21st century, and the latest move
gc = lambda a, b: 111.195 * math.degrees(math.acos(min(1, math.sin(math.radians(a["lat"])) * math.sin(math.radians(b["lat"])) +
                                                  math.cos(math.radians(a["lat"])) * math.cos(math.radians(b["lat"])) * math.cos(math.radians(a["lon"] - b["lon"])))))
R["centre_move_20_21_km"] = gc(CE[20], CE[21])
R["centre_move_19_20_km"] = gc(CE[19], CE[20])
R["centre_eu_centuries"] = sum(1 for r in centres if 0 <= r["lon"] <= 30 and 40 <= r["lat"] <= 55)
R["centre_c19_median_km"] = CE[19]["median_km"]; R["centre_c15_median_km"] = CE[15]["median_km"]
ALPS = {"lat": 46.5, "lon": 10.5}
R["centre_alps_km"] = {r["short"]: gc(r, ALPS) for r in centres}
assert all(gc(CE[c], ALPS) < 800 for c in range(5, 20) if c != 7) and gc(CE[7], ALPS) > 2000 and gc(CE[1], ALPS) < 200
assert min(gc(CE[2], ALPS), gc(CE[3], ALPS)) > 2500 and gc(CE[4], ALPS) > 1000 and gc(CE[20], ALPS) > 1000 and gc(CE[21], ALPS) > 2500
assert [CE[c]["place"] for c in (-5, -1, 7, 15, 19, 20, 21)] == ["Greece", "Italy", "Syria", "Germany", "France", "Romania", "Syria"]
R["centre_c2_km"] = CE[2]["median_km"]; R["centre_c3_km"] = CE[3]["median_km"]; R["centre_c21_place"] = CE[21]["place"]
R["centre_c2_asia_pct"] = pc(cc[2]["by_cont"][1], cc[2]["n_map"]); R["centre_c3_asia_pct"] = pc(cc[3]["by_cont"][1], cc[3]["n_map"])

# ---------- most fought-over places: equal-area hexagons ----------
M["hk"] = list(zip(M.hq, M.hr))
H = M.groupby("hk").agg(n=("qid", "size"), cent=("century", "nunique"), era=("era", "nunique"), y0=("year", "min"), y1=("year", "max"),
                        country=("country", lambda s: s[s != ""].mode().iloc[0] if (s != "").any() else ""),
                        sl=("sitelinks", "sum")).reset_index()
H["q"] = H.hk.map(lambda k: k[0]); H["r"] = H.hk.map(lambda k: k[1])
INV = Transformer.from_crs(8857, 4326, always_xy=True)
H["lon"], H["lat"] = zip(*[INV.transform(*hex_centre(q, r)) for q, r in zip(H.q, H.r)])
R["hex_km2"] = 1.5 * math.sqrt(3) * HEX_R ** 2 / 1e6
R["hex_n"] = len(H); R["hex_1"] = int((H.n == 1).sum())
hs = H.sort_values(["n", "cent"], ascending=False).reset_index(drop=True)
R["hex_top10_pct"] = pc(hs.n.head(10).sum(), NM); R["hex_top100_pct"] = pc(hs.n.head(100).sum(), NM)
hc = H.sort_values(["cent", "n"], ascending=False).reset_index(drop=True)
R["hex_all_eras"] = int((H.era == len(ERAS)).sum())
assert sorted(H[H.era == len(ERAS)].hk.tolist()) == [(8, 44), (15, 46)]       # Jerusalem and Gaza; Baghdad
east = H[H.lon > 60].sort_values("n", ascending=False).iloc[0]
assert east.hk == (90, 48)                                                     # Kyoto, Osaka and Nara: the busiest place east of 60 E


def hrow(r):
    k = (int(r.q), int(r.r))
    s = M[M.hk == k]
    nm = HEXNAME.get(k)
    assert nm, ("name this hexagon", k, r.n, r.cent, r.country, s.location.value_counts().head(4).index.tolist(),
                s.sort_values("sitelinks", ascending=False).label.head(3).tolist())
    top = s.sort_values("sitelinks", ascending=False).head(3)
    return {"q": k[0], "r": k[1], "name": nm, "country": r.country, "n": int(r.n), "cent": int(r.cent), "era": int(r.era),
            "y0": int(r.y0), "y1": int(r.y1), "y0t": ytxt(int(r.y0)), "y1t": ytxt(int(r.y1)), "lat": round(r.lat, 3), "lon": round(r.lon, 3),
            "by_era": [int((s.era == i).sum()) for i in range(len(ERAS))], "famous": [dash(x) for x in top.label]}


R["hex_top"] = [hrow(r) for _, r in hs.head(20).iterrows()]
R["hex_cent"] = [hrow(r) for _, r in hc.head(15).iterrows()]
assert R["hex_top"][0]["name"].startswith("Arras") and R["hex_cent"][0]["name"].startswith("Jerusalem")

# regions: a hexagon and its six neighbours (about 65,000 km2), chosen greedily without overlap
NB = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
cnt = dict(zip(H.hk, H.n))
ros = {k: sum(cnt.get((k[0] + a, k[1] + b), 0) for a, b in NB) for k in cnt}
used, regs = set(), []
for k in sorted(ros, key=lambda k: -ros[k]):
    cells = {(k[0] + a, k[1] + b) for a, b in NB}
    if cells & used:
        continue
    s = M[M.hk.isin(cells)]
    nm = REGNAME.get(k)
    assert nm, ("name this region", k, ros[k], s.country.value_counts().head(3).to_dict(), s.location.value_counts().head(5).index.tolist())
    lon, lat = INV.transform(*hex_centre(*k))
    regs.append({"q": k[0], "r": k[1], "name": nm, "n": int(len(s)), "cent": int(s.century.nunique()), "era": int(s.era.nunique()),
                 "lat": round(lat, 3), "lon": round(lon, 3), "by_era": [int((s.era == i).sum()) for i in range(len(ERAS))],
                 "countries": [dash(x) for x in s.country.value_counts().head(3).index.tolist()],
                 "famous": [dash(x) for x in s.sort_values("sitelinks", ascending=False).label.head(3)]})
    used |= cells
    if len(regs) == 15:
        break
R["regions"] = regs
R["region_km2"] = 7 * R["hex_km2"]
R["flanders"] = regs[0]
vr = M[M.hk.isin({(regs[1]["q"] + a, regs[1]["r"] + b) for a, b in NB})]
R["vendee_region_pct"] = pc(vr.conflict.isin(["War in the Vendée", "Chouannerie"]).sum(), len(vr))
assert regs[1]["name"].startswith("Western France") and 60 < R["vendee_region_pct"] < 75
fl = set(M[M.hk.isin({(regs[0]["q"] + a, regs[0]["r"] + b) for a, b in NB})].label)
assert {"Battle of the Sabis", "Battle of the Golden Spurs", "Battle of Ramillies", "Battle of Malplaquet", "Battle of Waterloo", "Third Battle of Ypres"} <= fl
assert regs[0]["name"].startswith("Flanders")

# modern countries: battles and battles per 10,000 km2 (countries of 20,000 km2 or more)
cty = M[M.iso != ""].groupby("iso").size()
crow = []
for iso, n in cty.items():
    nm, a = carea.get(iso, (iso, None))
    crow.append({"iso": iso, "name": dash(nm.replace("United States of America", "United States").replace("People's Republic of China", "China")),
                 "n": int(n), "km2": a, "per10k": n / a * 1e4 if a else None})
crow.sort(key=lambda r: -r["n"])
R["countries_top"] = crow[:15]
dens = sorted([r for r in crow if r["km2"] and r["km2"] >= 20000], key=lambda r: -r["per10k"])
R["countries_dense"] = dens[:15]
R["n_countries"] = len(crow)
R["belgium"] = next(r for r in crow if r["iso"] == "BEL")
assert dens[0]["iso"] == "BEL", [d["iso"] for d in dens[:3]]

# ---------- best-recorded wars ----------
W2 = B[B.conflict != ""].groupby("conflict").agg(n=("qid", "size"), n_map=("lat", lambda s: int(s.notna().sum())),
                                                 sl_med=("sitelinks", "median"), sl_sum=("sitelinks", "sum"),
                                                 y0=("year", "min"), y1=("year", "max")).reset_index().sort_values(["n", "sl_sum"], ascending=False)
wars = []
for _, r in W2.head(25).iterrows():
    s = B[B.conflict == r.conflict]
    ct = s.cont.dropna().astype(int).value_counts()
    wars.append({"name": dash(r.conflict), "n": int(r.n), "n_map": int(r.n_map), "sl_med": float(r.sl_med), "sl_sum": int(r.sl_sum),
                 "y0": int(r.y0) if pd.notna(r.y0) else None, "y1": int(r.y1) if pd.notna(r.y1) else None,
                 "cont": int(ct.index[0]) if len(ct) else None,
                 "top": dash(s.sort_values("sitelinks", ascending=False).label.iloc[0])})
R["wars"] = wars
assert all(CONTS[w["cont"]][0] in ("Europe", "North America") for w in wars if w["name"] not in ("Korean War", "Vietnam War", "Syrian Civil War", "War in Afghanistan (2001 to 2021)"))
R["n_no_war"] = int((B.conflict == "").sum()); R["pct_no_war"] = pc(R["n_no_war"], N)
R["ww2"] = next(w for w in wars if w["name"] == "World War II"); R["ww1"] = next(w for w in wars if w["name"] == "World War I")
R["acw"] = next(w for w in wars if w["name"] == "American Civil War")
R["ww2_recorded_as"] = int(B[B.conflict == "World War II"].war.nunique())
R["vendee"] = int(B.conflict.isin(["War in the Vendée", "Chouannerie"]).sum())
R["wars_top10_pct"] = pc(sum(w["n"] for w in wars[:10]), R["n_war"])
# best-linked battles
TL = B.sort_values("sitelinks", ascending=False).head(12)
R["most_linked"] = [{"label": dash(r.label), "sl": int(r.sitelinks), "year": ytxt(int(r.year)) if pd.notna(r.year) else ""} for _, r in TL.iterrows()]

# ---------- bias ----------
R["sl_by_era"] = [e["sl_median"] for e in eras]
R["n_sl_ge50"] = int((B.sitelinks >= 50).sum())
cut = lambda a, b: B[(B.year >= a) & (B.year <= b)]
R["sl_med_ancient"] = float(cut(-3500, 499).sitelinks.median()); R["sl_med_modern"] = float(cut(1800, 2026).sitelinks.median())
R["sl_med_c21"] = float(cut(2001, 2026).sitelinks.median())
R["nolabel_pct_xy"] = pc(B[B.label == ""].lat.notna().sum(), R["n_nolabel"])
nl = M[M.label == ""]
R["nolabel_by_cont"] = [{"name": c[0], "pct": pc((nl.cont == k).sum(), len(nl))} for k, c in enumerate(CONTS)]
R["nolabel_asia_pct"] = R["nolabel_by_cont"][1]["pct"]
R["n_undated_xy"] = int((hasxy & ~hasy).sum()); R["n_dated_noxy"] = int((~hasxy & hasy).sum())
R["xy_pct_by_era"] = [pc(((B.era == i) & hasxy).sum(), (B.era == i).sum()) for i in range(len(ERAS))]
R["vendee_hexes"] = [h["name"] for h in R["hex_top"] if "Vend" in h["name"] or "Brittany" in h["name"] or "Nantes" in h["name"]]
# sitelinks against year: a sample of points for the scatter chart (every dated battle, rounded)
jsave({"cols": ["year (astronomical)", "sitelinks", "continent (-1 unknown)"],
       "rows": [[int(y), int(s), int(c) if pd.notna(c) else -1] for y, s, c in zip(Dd.year, Dd.sitelinks, Dd.cont)]}, f"{DATA}/sitelinks_by_year.json")
qs = []
for c in cents:
    d = Dd[Dd.century == c]
    if len(d) >= 10:
        qs.append([c, (c - 1) * 100 + 50 if c > 0 else c * 100 + 50, float(d.sitelinks.median()), float(d.sitelinks.quantile(.9)), int(len(d))])
R["sl_quant"] = qs

# ---------- the deadliest battles (Wikipedia list) ----------
CM2 = CAS[CAS.lat.notna()].copy()
R["cas"] = {"n": CASM["n"], "matched": CASM["matched"], "mapped": CASM["mapped"], "revid": CASM["revid"],
            "matched_pct": pc(CASM["matched"], CASM["n"]),
            "europe_pct": pc((CM2.continent == "Europe").sum(), len(CM2)), "asia_pct": pc((CM2.continent == "Asia").sum(), len(CM2)),
            "n_over_100k": int((CAS.casualties_high >= 100000).sum()), "n_over_1m": int((CAS.casualties_high >= 1e6).sum())}
R["cas"]["unmatched_examples"] = [x for x in ["Operation Barbarossa", "Siege of Leningrad", "Battle of the Bulge", "Hundred Days Offensive"]
                                  if x in set(CAS[CAS.qid.isna() | (CAS.qid == "")].name)]
assert len(R["cas"]["unmatched_examples"]) >= 3, R["cas"]["unmatched_examples"]
top = CAS.sort_values("casualties_high", ascending=False).head(10)
R["cas"]["top"] = [{"name": r["name"], "y": ytxt(int(r.year_from)) if pd.notna(r.year_from) else "", "cas": float(r.casualties_high),
                    "mapped": bool(pd.notna(r.lat))} for _, r in top.iterrows()]
jsave({"cols": ["lat", "lon", "name", "year", "table", "casualties_high", "conflict", "qid"],
       "rows": [[r.lat, r.lon, r["name"], ytxt(int(r.year_from)) if pd.notna(r.year_from) else "", r.table, r.casualties_high, r.conflict, r.qid]
                for _, r in CM2.sort_values("casualties_high", ascending=False).iterrows()]}, f"{DATA}/casualties_map.json")

# ---------- tidy tables ----------
pd.DataFrame([{"century": r["name"], "first_year": ytxt(r["y0"]), "battles_dated": r["n"], "battles_mapped": r["n_map"], "per_year": round(r["per_year"], 2),
               **{c[0]: r["by_cont"][k] for k, c in enumerate(CONTS)}, "open_ocean": r["ocean"], "median_sitelinks": r["sl_median"]} for r in cr]
             ).to_csv(f"{DATA}/battles_by_century.csv", index=False)
pd.DataFrame([{"century": r["name"], "battles_mapped": r["n"], "centre_lat": r["lat"], "centre_lon": r["lon"], "in_or_near": r["place"],
               "median_distance_km": round(r["median_km"]), "within_1000km_pct": round(r["within1000_pct"], 1)} for r in centres]
             ).to_csv(f"{DATA}/centre_of_war.csv", index=False)
hx = H.sort_values("n", ascending=False).copy()
hx["name"] = hx.hk.map(lambda k: HEXNAME.get(k, ""))
hx[["q", "r", "lat", "lon", "name", "country", "n", "cent", "era", "y0", "y1"]].rename(columns={"n": "battles", "cent": "centuries", "era": "eras",
    "y0": "first_year", "y1": "last_year", "lat": "centre_lat", "lon": "centre_lon"}).to_csv(f"{DATA}/hexagons.csv", index=False)
pd.DataFrame(wars).rename(columns={"n": "battles", "n_map": "mapped", "sl_med": "median_sitelinks", "sl_sum": "total_sitelinks",
                                   "y0": "first_year", "y1": "last_year", "top": "most_linked_battle"}).assign(
    cont=lambda d: d.cont.map(lambda k: CONTS[k][0] if k is not None and not pd.isna(k) else "")).rename(columns={"cont": "main_continent"}).to_csv(f"{DATA}/wars.csv", index=False)

# ---------- page data ----------
conf = B[B.conflict != ""].conflict.value_counts()
CL = [dash(c) for c in conf.index]
CI = {c: i for i, c in enumerate(conf.index)}
site = {"conts": CONTS, "eras": ERAS, "eshort": ESHORT, "ecol": ECOL, "kinds": [k[0] for k in KINDS], "kcol": KCOL,
        "conflicts": CL, "conflict_n": [int(v) for v in conf.values]}
WC = jload(f"{WORK}/countries.json"); site["cname"] = WC["cname"]; site["cpos"] = WC["cpos"]
jsave(site, f"{DATA}/site.json")
MM = M.sort_values("sitelinks").reset_index(drop=True)
# equal-area hexagons at three sizes for the page: each point carries its hexagon index at 60, 120 and 240 km
SIZES = [HEX_R, 2 * HEX_R, 4 * HEX_R]
HX, hid = {}, []
for k, rr in enumerate(SIZES):
    q, r_ = hex_of(MM.x.values, MM.y.values, rr)
    keys = list(zip(q.tolist(), r_.tolist())); uniq = sorted(set(keys)); ix = {u: i for i, u in enumerate(uniq)}
    hid.append([ix[u] for u in keys])
    rings = []
    for u in uniq:
        xs, ys = zip(*hex_ring(*u, rr)); lo_, la_ = INV.transform(np.array(xs), np.array(ys))
        rings.append([v for a, b in zip(la_, lo_) for v in (round(float(a), 3), round(float(b), 3))])
    HX[f"{int(rr/1000)}"] = rings
pts = [[round(r.lat, 3), round(r.lon, 3), int(r.year), int(r.kind), int(r.cont) if pd.notna(r.cont) else -1, int(r.sitelinks),
        CI.get(r.conflict, -1), r.label, r.location, r.qid[1:], hid[0][i], hid[1][i], hid[2][i]] for i, r in enumerate(MM.itertuples())]
jsave({"cols": ["lat", "lon", "year (astronomical: 0 = 1 BCE)", "kind", "continent", "sitelinks", "conflict", "label", "location", "qid number",
                "hexagon 60 km", "hexagon 120 km", "hexagon 240 km"], "rows": pts}, f"{DATA}/points.json")
# outlines of the most fought-over hexagons and regions (rosettes of seven hexagons), as lat/lon rings
from shapely.geometry import Polygon
from shapely.ops import unary_union
def ll(ring):
    xs, ys = zip(*ring); lo_, la_ = INV.transform(np.array(xs), np.array(ys))
    return [[round(float(a), 3), round(float(b), 3)] for a, b in zip(la_, lo_)]
tops = {"hex": [{"name": h["name"], "n": h["n"], "cent": h["cent"], "ring": ll(hex_ring(h["q"], h["r"]))} for h in R["hex_top"]],
        "regions": [{"name": g["name"], "n": g["n"], "cent": g["cent"],
                     "ring": ll(list(unary_union([Polygon(hex_ring(g["q"] + a, g["r"] + b)) for a, b in NB]).buffer(1).exterior.coords)[:-1])}
                    for g in regs]}
jsave({"note": "Equal-area hexagons in the Equal Earth projection (EPSG:8857); circumradius 60, 120 and 240 km; rings are lat, lon pairs",
       "rings": HX, "top": tops}, f"{DATA}/hexes.json")
jsave(R, f"{DATA}/results.json", indent=1)
print({k: R[k] for k in ("n", "n_xy", "n_own", "n_dated", "n_map", "n_nolabel", "n_bce", "peak_century", "fastest_century", "peak_year", "peak_decade",
                         "europe_pct", "europe_land_pct", "europe_x_land", "hex_km2", "hex_n")})
print("centres", [(r["short"], r["place"], round(r["median_km"])) for r in centres])
print("regions", [(r["name"], r["n"], r["cent"]) for r in regs])
print("wars", [(w["name"], w["n"]) for w in wars[:12]])
print("dense", [(d["name"], d["n"], round(d["per10k"], 1)) for d in dens[:8]])
print("cas", {k: v for k, v in R["cas"].items() if k != "top"})
for f in ("points.json", "site.json", "results.json", "hexes.json", "casualties_map.json"):
    print(f, os.path.getsize(f"{DATA}/{f}") // 1024, "KB")
