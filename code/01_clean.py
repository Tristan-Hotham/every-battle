"""Wikidata battles: one row per item. Coordinates from the item's own P625, else from its location (P276); year from
point in time (P585), else start time (P580), in astronomical numbering; primary war = the part-of (P361) value with the
most battles; kind from the English label; modern country and continent from Natural Earth (nearest country within
400 km for battles at sea). Writes data/battles.csv and WORK/battles.pkl."""
import csv
import pandas as pd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from pyproj import Transformer
from common import *

D = pd.read_csv(f"{RAW}/wikidata_battles.tsv", sep="\t", quoting=csv.QUOTE_NONE, dtype=str)
D.columns = [c.lstrip("?") for c in D.columns]
n_rows = len(D)
D["qid"] = D.b.str.extract(r"(Q\d+)>$")[0]
assert D.qid.notna().all()
lit = lambda s: s.str.replace(r'^"(.*)"@en$', r"\1", regex=True)
for c in ("bL", "warL", "locL"):
    D[c] = lit(D[c])


def pt(s):
    m = re.match(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)", s if isinstance(s, str) else "")
    return (float(m.group(1)), float(m.group(2))) if m else None


def yr(s):
    m = re.match(r"^(-?\d{4,})-(\d\d)-(\d\d)T", s if isinstance(s, str) else "")
    return int(m.group(1)) if m else None


D["c_own"] = D.coord.map(pt); D["c_loc"] = D.locCoord.map(pt)
D["y_pit"] = D.date.map(yr); D["y_start"] = D.start.map(yr)
n_unknown_dates = int((D.date.notna() & D.y_pit.isna()).sum() + (D.start.notna() & D.y_start.isna()).sum())

rows = []
for q, g in D.groupby("qid", sort=False):
    own = [c for c in g.c_own if c]
    loc = [(c, l) for c, l in zip(g.c_loc, g.locL) if c]
    lon = lat = None; src = ""; spread = 0.0; locname = ""
    if own:
        lon, lat = own[0]; src = "own"
    if loc:
        xs = np.array([c[0] for c, _ in loc]); ys = np.array([c[1] for c, _ in loc])
        mx, my = np.median(xs), np.median(ys)
        k = int(np.argmin((xs - mx) ** 2 + (ys - my) ** 2))
        spread = float(max(xs.max() - xs.min(), ys.max() - ys.min()))
        locname = loc[k][1] if isinstance(loc[k][1], str) else ""
        if not own:
            lon, lat = loc[k][0]; src = "location"
    if not locname:
        ln = [l for l in g.locL if isinstance(l, str)]
        locname = ln[0] if ln else ""
    yp = [y for y in g.y_pit if y is not None and not pd.isna(y)]
    ys_ = [y for y in g.y_start if y is not None and not pd.isna(y)]
    year = int(min(yp)) if yp else (int(min(ys_)) if ys_ else None)
    ysrc = "point in time" if yp else ("start time" if ys_ else "")
    wars = sorted({w for w in g.warL if isinstance(w, str)})
    lab = g.bL.dropna()
    rows.append({"qid": q, "label": lab.iloc[0] if len(lab) else "", "sitelinks": int(g.sl.iloc[0]), "lon": lon, "lat": lat,
                 "coord_from": src, "loc_spread_deg": round(spread, 3), "location": locname, "year": year, "year_from": ysrc,
                 "wars": wars})
B = pd.DataFrame(rows)
# primary war: the part-of value with the most battles overall
wc = pd.Series([w for ws in B.wars for w in ws]).value_counts()
B["war"] = B.wars.map(lambda ws: max(ws, key=lambda w: (wc[w], w)) if ws else "")
B["n_wars"] = B.wars.map(len)
B["conflict"] = [conflict_of(ws, None if pd.isna(y) else int(y)) or w for ws, y, w in zip(B.wars, B.year, B.war)]
B["kind"] = B.label.map(kind_of)

# sanity: coordinates in range, years not in the future
bad_xy = B.lat.notna() & ((B.lat.abs() > 90) | (B.lon.abs() > 180))
assert not bad_xy.any()
fut = B.year.notna() & (B.year > 2026)
print("future years dropped to missing:", B.loc[fut, ["qid", "label", "year"]].values.tolist())
B.loc[fut, "year"] = None

# country and continent: Natural Earth 1:50m, point in polygon, else nearest country within 400 km (battles at sea)
W = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
geoms, meta = [], []
for f in W["features"]:
    p = f["properties"]
    geoms.append(shape(f["geometry"])); meta.append((iso_of(p), p["NAME_EN"] or p["NAME"], CONT_OF_NE.get(p["CONTINENT"])))
tree = STRtree(geoms)
EE = Transformer.from_crs(4326, 8857, always_xy=True)
iso, cn, ct, sea = [], [], [], []
for lon, lat in zip(B.lon, B.lat):
    if lon is None or pd.isna(lon):
        iso.append(""); cn.append(""); ct.append(None); sea.append(None); continue
    p = Point(lon, lat)
    hit = [i for i in tree.query(p, predicate="intersects")]
    if hit:
        i = hit[0]; s = False
    else:
        i = int(tree.nearest(p)); s = True
        # distance check in metres (approximate, Equal Earth)
        g = geoms[i]; from shapely.ops import nearest_points
        a, b = nearest_points(p, g)
        x0, y0 = EE.transform(a.x, a.y); x1, y1 = EE.transform(b.x, b.y)
        if math.hypot(x1 - x0, y1 - y0) > 400000:
            iso.append(""); cn.append(""); ct.append(None); sea.append(True); continue
    iso.append(meta[i][0]); cn.append(meta[i][1]); ct.append(meta[i][2]); sea.append(s)
B["iso"] = iso; B["country"] = cn; B["cont"] = ct; B["at_sea"] = sea
# Natural Earth puts Russia, Turkey, Georgia and others in one continent: split Russia and Turkey by the Urals and Bosporus
ru = (B.iso == "RUS") & (B.lon > 60) | (B.iso == "RUS") & (B.lon < -160)
B.loc[(B.iso == "RUS") & ~ru, "cont"] = 0; B.loc[ru, "cont"] = 1
tr_eu = (B.iso == "TUR") & (B.lon < 29.1) & (B.lat > 40.3)
B.loc[tr_eu, "cont"] = 0
B.loc[(B.iso == "TUR") & ~tr_eu, "cont"] = 1

xy = EE.transform(B.lon.fillna(0).values, B.lat.fillna(0).values)
B["x"], B["y"] = xy
has = B.lat.notna()
B["hq"], B["hr"] = hex_of(B.x.values, B.y.values)
B.loc[~has, ["hq", "hr"]] = -999999
B["century"] = B.year.map(lambda y: century_of(int(y)) if pd.notna(y) else None)
B["era"] = B.year.map(lambda y: era_of(int(y)) if pd.notna(y) else None)
B.to_pickle(f"{WORK}/battles.pkl")

out = B.copy()
out["year_text"] = out.year.map(lambda y: ytxt(int(y)) if pd.notna(y) else "")
out["continent"] = out.cont.map(lambda c: CONTS[int(c)][0] if pd.notna(c) else "")
out["kind"] = out.kind.map(lambda k: KINDS[k][0])
out["century"] = out.century.map(lambda c: cname(int(c)) if pd.notna(c) else "")
out["era"] = out.era.map(lambda e: ERAS[int(e)][0] if pd.notna(e) else "")
out["wars"] = out.wars.map(lambda ws: "; ".join(ws))
out["year"] = out.year.astype("Int64")
out["at_sea"] = out.at_sea.map(lambda v: "" if v is None else ("yes" if v else "no"))
for c in ("label", "location", "war", "wars", "conflict", "country"):
    out[c] = out[c].map(dash)
out["lat"] = out.lat.round(5); out["lon"] = out.lon.round(5)
out[["qid", "label", "year", "year_text", "year_from", "century", "era", "lat", "lon", "coord_from", "loc_spread_deg", "location",
     "country", "iso", "continent", "at_sea", "kind", "conflict", "war", "wars", "sitelinks"]].to_csv(f"{DATA}/battles.csv", index=False)
meta = {"n_rows": n_rows, "n_items": len(B), "n_unknown_dates": n_unknown_dates}
jsave(meta, f"{WORK}/clean_meta.json")
print(meta, "coords", int(has.sum()), "own", int((B.coord_from == "own").sum()), "years", int(B.year.notna().sum()),
      "both", int((has & B.year.notna()).sum()), "min year", B.year.min(), "max", B.year.max())
print(B.kind.value_counts().sort_index().rename(index=lambda k: KINDS[k][0]))
print(B[has].cont.value_counts(dropna=False))
print(B[has & B.cont.isna()][["label", "lat", "lon"]].head(10))
print(B.conflict.value_counts().head(25))
