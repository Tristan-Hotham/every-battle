"""r/dataisbeautiful collage for every-battle: 3000 x 2100 px, light background. Numbers from data/results.json.
A world map of every battle by era, a Europe and Middle East inset with the most fought-over regions (numbered in the
margin, leader lines sorted so they never cross labels), the ranking, and a century timeline. Map labels sit on open sea
and are checked: a label box must not touch land or any battle dot."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.patches import Rectangle, Polygon as MPolygon, Ellipse
from shapely.geometry import Polygon as SPoly, box as sbox, Point
from shapely.ops import unary_union

R = jload(f"{DATA}/results.json")
HX = jload(f"{DATA}/hexes.json")
D = pd.read_csv(f"{DATA}/battles.csv", keep_default_na=False, na_values=[""])
Dd = D[D.year.notna()].copy(); Dd["year"] = Dd.year.astype(int)
M = Dd[Dd.lat.notna()].copy(); M["e"] = M.year.map(era_of)
X, Y = proj(M.lon.values, M.lat.values)
BGc = "#F7F5F0"; SEAc = "#E8EEF1"; LANDc = "#E1DBCC"
HEXC = LinearSegmentedColormap.from_list("hx", ["#FFF1CD", "#FAC878", "#EC8842", "#CC422C", "#8C1424", "#3E0818"])
HALO = [pe.withStroke(linewidth=4, foreground=SEAc)]
WEXT = ext_of(-165, -48, 155, 66)
IEXT = ext_of(-10.5, 29.5, 41, 59)
# land for label placement and checks: Natural Earth 1:50m land, unsimplified (rings crossing the antimeridian, far from
# any label, are left out)
LANDP = []
for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]:
    g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for poly in polys:
        ring = np.array(poly[0])
        if np.ptp(ring[:, 0]) > 180 or len(ring) < 4:
            continue
        x, y = proj(np.clip(ring[:, 0], -179.9, 179.9), np.clip(ring[:, 1], -89.5, 89.5))
        p = SPoly(np.c_[x, y]); LANDP.append(p if p.is_valid else p.buffer(0))
LAND = unary_union(LANDP)
PAD_ASSERT = 25000                              # every map label box, grown by 25 km, must clear land and battle points
PAD_PLACE = 150000                              # placement asks for more room, so labels sit well out on open ocean
CHECK = []                                      # (axes, text) to test against land and dots

W_, H_ = 3000, 2100
fy = lambda px: 1 - px / H_
fx = lambda px: px / W_
fig = plt.figure(figsize=(15, 10.5), dpi=200, facecolor=BGc)

# ---------- title ----------
fig.text(fx(70), fy(40), "Every battle in history", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(fx(72), fy(205), f"{R['n_map']:,} battles with a place and a date in Wikidata, {R['first']['year_text']} to 2026. Europe has {R['europe_pct']:.0f}% of them\n"
         f"on {R['europe_land_pct']:.0f}% of the world's land, and {R['pct_since1800']:.0f}% happened after 1800.",
         fontproperties=SERP, fontsize=14.5, color=FG, va="top", linespacing=1.4)

# ---------- world map ----------
wx0, wy0, ww = 40, 370, 1820
wh = ww * (WEXT[3] - WEXT[2]) / (WEXT[1] - WEXT[0])
axw = fig.add_axes([fx(wx0), fy(wy0 + wh), fx(ww), wh / H_])
world(axw, WEXT, land=LANDc, ec="#FFFFFF", lw=.25, sea=SEAc)
for e in range(len(ERAS)):
    k = M.e.values == e
    axw.scatter(X[k], Y[k], s=1.5, c=ECOL[e], alpha=.8, lw=0, zorder=3 + e * .01)
axw.set_xlim(WEXT[0], WEXT[1]); axw.set_ylim(WEXT[2], WEXT[3])
axw.add_patch(Rectangle((WEXT[0], WEXT[2]), WEXT[1] - WEXT[0], WEXT[3] - WEXT[2], fc="none", ec="#C9C3B6", lw=.8, zorder=6))
NOTES = [(-125, 0, f"19th century:\n{R['pct_americas_19']:.0f}% in the Americas"),
         (78, -34, f"Since 1946:\n{R['eras'][7]['pct_cont'][1]:.0f}% in Asia,\n{R['eras'][7]['pct_cont'][2]:.0f}% in Africa")]
fig.canvas.draw()


def box_of(t, pad):
    bb = t.get_window_extent().transformed(axw.transData.inverted())
    return bb, sbox(bb.x0 - pad, bb.y0 - pad, bb.x1 + pad, bb.y1 + pad)


def clear(t, pad=PAD_PLACE):
    bb, b = box_of(t, pad)
    if bb.x0 < WEXT[0] or bb.x1 > WEXT[1] or bb.y0 < WEXT[2] or bb.y1 > WEXT[3]:
        return False
    x0, y0, x1, y1 = b.bounds
    return not b.intersects(LAND) and not ((X > x0) & (X < x1) & (Y > y0) & (Y < y1)).any()


for lo, la, t in NOTES:
    tx = axw.text(0, 0, t, fontsize=10, color=FG, ha="center", va="center", zorder=8, path_effects=HALO, linespacing=1.3)
    cands = sorted([(lo + dx, la + dy) for dx in range(-40, 41, 2) for dy in range(-24, 25, 2)], key=lambda p: (p[0] - lo) ** 2 + (p[1] - la) ** 2)
    for clo, cla in cands:
        tx.set_position(proj(clo, cla))
        if clear(tx):
            break
    else:
        raise AssertionError(f"no clear place on open ocean for {t!r}")
    CHECK.append((axw, tx))

# ---------- era legend (dots on the world map and bars in the timeline) ----------
ly = wy0 + wh + 40
for i, (n, a, b) in enumerate(ERAS):
    cx, cy = fx(wx0 + 10 + (i % 4) * 445), fy(ly + (i // 4) * 40)
    fig.patches.append(Ellipse((cx + .004, cy), .008, .008 * W_ / H_, transform=fig.transFigure, fc=ECOL[i], ec="none"))
    fig.text(cx + .012, cy, n, fontsize=11, color=FG, va="center")
fig.text(fx(wx0), fy(ly + 78), "Each dot one battle, coloured by era. Points are the battle's own coordinates or its recorded location.", fontsize=9.5, color=MUT, va="center")

# ---------- Europe and Middle East inset with the most fought-over regions ----------
ix0, iy0, iw = 1930, 400, 1040
ar = (IEXT[3] - IEXT[2]) / (IEXT[1] - IEXT[0])
mw = iw - 150; ih2 = mw * ar; ih = ih2
axi = fig.add_axes([fx(ix0 + 75), fy(iy0 + ih2), fx(mw), ih2 / H_])
world(axi, IEXT, land=LANDc, ec="#FFFFFF", lw=.3, sea=SEAc)
k = (M.lon > -14) & (M.lon < 44) & (M.lat > 26) & (M.lat < 62)
axi.hexbin(X[k], Y[k], gridsize=44, extent=IEXT, mincnt=1, cmap=HEXC, norm=LogNorm(1, 60), lw=.2, edgecolors=BGc, zorder=3)
axi.set_xlim(IEXT[0], IEXT[1]); axi.set_ylim(IEXT[2], IEXT[3])
axi.add_patch(Rectangle((IEXT[0], IEXT[2]), IEXT[1] - IEXT[0], IEXT[3] - IEXT[2], fc="none", ec="#C9C3B6", lw=.8, zorder=6))
regs = [(i, g) for i, g in enumerate(HX["top"]["regions"][:12])]
cents = []
for i, g in regs:
    ring = np.array(g["ring"]); px, py = proj(ring[:, 1], ring[:, 0])
    if px.min() < IEXT[0] or px.max() > IEXT[1] or py.min() < IEXT[2]:
        continue
    axi.add_patch(MPolygon(np.c_[px, py], closed=True, fc="none", ec=FG, lw=1.4, zorder=6))
    cents.append((i, px.mean(), py.mean(), px.min(), px.max(), py.min(), py.max()))
# labels in the paper margins, each joined to its outline by a straight line that crosses no label: regions near the
# top edge get labels above the map (vertical lines), western ones to the left (horizontal), southern ones below
LEAD, NUM = [], {}
SIDE = {0: "T", 8: "T", 7: "T", 10: "L", 4: "L", 1: "L", 11: "L", 5: "B", 3: "B", 6: "B", 2: "B"}
to_fig = lambda x, y: fig.transFigure.inverted().transform(axi.transData.transform((x, y)))
ytop, ybot, xleft = fy(iy0 - 16), fy(iy0 + ih2 + 16), fx(ix0 + 55)
for i, cx, cy, x0, x1, y0_, y1_ in cents:
    sd = SIDE[i]
    if sd == "T":
        ex, ey = to_fig(cx, y1_); fig.lines.append(plt.Line2D([ex, ex], [ytop - .004, ey], transform=fig.transFigure, color=FG, lw=.7))
        LEAD.append((fig.lines[-1], i)); NUM[i] = fig.text(ex, ytop, str(i + 1), fontsize=11.5, fontweight="bold", color=FG, ha="center", va="bottom")
    elif sd == "B":
        ex, ey = to_fig(cx, y0_); fig.lines.append(plt.Line2D([ex, ex], [ybot + .004, ey], transform=fig.transFigure, color=FG, lw=.7))
        LEAD.append((fig.lines[-1], i)); NUM[i] = fig.text(ex, ybot, str(i + 1), fontsize=11.5, fontweight="bold", color=FG, ha="center", va="top")
    else:
        ex, ey = to_fig(x0, cy); fig.lines.append(plt.Line2D([xleft + .004, ex], [ey, ey], transform=fig.transFigure, color=FG, lw=.7))
        LEAD.append((fig.lines[-1], i)); NUM[i] = fig.text(xleft, ey, str(i + 1), fontsize=11.5, fontweight="bold", color=FG, ha="right", va="center")
fig.text(fx(ix0 + 75), fy(iy0 - 62), "The most fought-over regions", fontproperties=DISPB, fontsize=14, color=FG, va="bottom")
# hexagon legend
hy = iy0 + ih2 + 100
lx_ = fig.add_axes([fx(ix0 + 75), fy(hy + 14), fx(260), 14 / H_]); lx_.imshow(np.linspace(0, 1, 256)[None, :], cmap=HEXC, aspect="auto"); lx_.set_axis_off()
fig.text(fx(ix0 + 75), fy(hy + 34), "1", fontsize=9, color=MUT, va="center"); fig.text(fx(ix0 + 330), fy(hy + 34), "60+", fontsize=9, color=MUT, va="center", ha="right")
fig.text(fx(ix0 + 350), fy(hy + 4), "battles per hexagon, all eras (log scale)", fontsize=9.5, color=FG, va="center")
fig.text(fx(ix0 + 350), fy(hy + 42), "outlined: the regions ranked below", fontsize=9.5, color=FG, va="center")

# ---------- ranking ----------
rx0, ry0 = 1930, hy + 122
fig.text(fx(rx0 + 20), fy(ry0), f"Battles per region (seven hexagons, {R['region_km2']:,.0f} km² each)", fontproperties=DISPB, fontsize=13, color=FG, va="bottom")
SHORT = {"The southern Levant: Galilee, Jerusalem, Gaza and Damascus": "Southern Levant", "Flanders, Artois and Brabant": "Flanders, Artois, Brabant",
         "The Welsh Marches and the English Midlands": "Welsh Marches, Midlands", "Western France, from the Vendée to Normandy": "Western France",
         "Central Scotland and the Highlands": "Central Scotland", "The Basque Country and Navarre": "Basque Country, Navarre",
         "Richmond and eastern Virginia": "Richmond, Virginia", "Masovia and Little Poland": "Masovia, Little Poland",
         "Lombardy and the Po valley": "Lombardy, Po valley", "Southern and central Greece": "Southern Greece", "Alsace and the Upper Rhine": "Alsace, Upper Rhine"}
assert R["hex_cent"][0]["name"].startswith("Jerusalem, Gaza")
RG = R["regions"][:12]
rh = 36; nx = rx0 + 340
axr = fig.add_axes([fx(nx), fy(ry0 + 20 + rh * len(RG)), fx(iw - 330 - 30), rh * len(RG) / H_]); axr.set_facecolor(BGc)
for i, g in enumerate(RG):
    yv = len(RG) - i; left = 0
    for e, v in enumerate(g["by_era"]):
        axr.barh(yv, v, left=left, color=ECOL[e], height=.62); left += v
    axr.text(left + 5, yv, f"{g['n']}", va="center", fontsize=10, fontweight="bold")
    fig.text(fx(nx - 12), fy(ry0 + 20 + rh * (i + .5)), f"{i + 1}. {SHORT.get(g['name'], g['name'])}", ha="right", va="center", fontsize=10)
axr.set_xlim(0, 420); axr.set_ylim(.5, len(RG) + .5); axr.axis("off")
fig.text(fx(rx0 + 20), fy(ry0 + 40 + rh * len(RG)), f"Number 10 lies outside the inset (American Civil War).\nFought over longest: the hexagon around Jerusalem and Gaza,\n"
         f"with battles in {R['hex_cent'][0]['cent']} different centuries.", fontsize=9.5, color=MUT, va="top", linespacing=1.35)

# ---------- century timeline ----------
tx0, ty0, tw, th = 130, 1450, 1620, 360
fig.text(fx(wx0), fy(ty0 - 30), "Battles per century, coloured by era", fontproperties=DISPB, fontsize=14, color=FG, va="bottom")
axt = fig.add_axes([fx(tx0), fy(ty0 + th), fx(tw), th / H_]); axt.set_facecolor(BGc); spines(axt)
C = [r for r in R["centuries"] if r["c"] >= -13]
cidx = {r["c"]: i for i, r in enumerate(C)}
Dd["c"] = Dd.year.map(century_of); Dd["e"] = Dd.year.map(era_of)
bottom = np.zeros(len(C))
for e in range(len(ERAS)):
    v = np.zeros(len(C))
    for c, n in Dd[Dd.e == e].groupby("c").size().items():
        if c in cidx: v[cidx[c]] = n
    axt.bar(np.arange(len(C)), v, bottom=bottom, color=ECOL[e], width=.8); bottom += v
assert all(abs(bottom[i] - C[i]["n"]) < 1 for i in range(len(C)))
show = [-10, -5, 1, 5, 10, 15, 19, 21]
axt.set_xticks([cidx[c] for c in show]); axt.set_xticklabels([cshort(c).replace(" BCE", "\nBCE") for c in show], fontsize=9.5)
axt.set_yticks([0, 1000, 2000, 3000]); axt.set_yticklabels(["0", "1,000", "2,000", "3,000"], fontsize=9.5); axt.yaxis.grid(True, color=RULE); axt.set_axisbelow(True)
axt.text(cidx[19] - .5, C[cidx[19]]["n"] + 60, f"{C[cidx[19]]['n']:,}", ha="right", fontsize=10, fontweight="bold")
axt.text(cidx[20] + .5, C[cidx[20]]["n"] + 60, f"{C[cidx[20]]['n']:,}", ha="left", fontsize=10, fontweight="bold")
axt.set_ylim(0, 4100); axt.set_xlim(-.7, len(C) + .2)
axt.text(cidx[-5], 3300, f"{R['n_bce']} battles are dated before 1 CE.\nThe 21st century (2001 to 2026) already has {R['c21']:,}.", fontsize=10, color=FG, va="top")

# ---------- footer ----------
fig.text(fx(40), fy(1985), "Data: Wikidata (CC0), all items that are instances of battle or its subclasses; Natural Earth. Equal-area hexagons in the Equal Earth projection. "
         "Wikidata reflects\nwhat Wikipedia editors have written up, so the record is heavily European and modern; battle items include sieges, raids and skirmishes.", fontsize=9, color=MUT, va="center", linespacing=1.4)
fig.text(fx(40), fy(2060), "Dr Tristan Hotham · maps.tristanhotham.com/every-battle", fontsize=9.5, color=FG, va="center")

# ---------- render-time checks ----------
from shapely.geometry import LineString
fig.canvas.draw()
rend = fig.canvas.get_renderer()
# 1. every map label's box, grown by 25 km, clears Natural Earth 1:50m land and every battle point
for ax, t in CHECK:
    bb, b = box_of(t, PAD_ASSERT)
    assert not b.intersects(LAND), ("map label touches land", t.get_text())
    x0, y0, x1, y1 = b.bounds
    n = int(((X > x0) & (X < x1) & (Y > y0) & (Y < y1)).sum())
    assert n == 0, ("map label covers battle points", t.get_text(), n)
    assert bb.x0 >= WEXT[0] and bb.x1 <= WEXT[1] and bb.y0 >= WEXT[2] and bb.y1 <= WEXT[3], ("map label outside the map", t.get_text())
# 2. no text overlaps another text (figure texts and texts inside every axes, in display pixels)
texts = [t for t in fig.texts if t.get_text().strip()] + [t for a in fig.axes for t in a.texts if t.get_text().strip()]
texts += [lab for a in fig.axes if a.axison for lab in a.get_xticklabels() + a.get_yticklabels() if lab.get_visible() and lab.get_text().strip()]
boxes = [(t, t.get_window_extent(rend)) for t in texts]
for k, (t1, b1) in enumerate(boxes):
    for t2, b2 in boxes[k + 1:]:
        ov = min(b1.x1, b2.x1) - max(b1.x0, b2.x0), min(b1.y1, b2.y1) - max(b1.y0, b2.y0)
        assert not (ov[0] > 1 and ov[1] > 1), ("labels overlap", t1.get_text()[:40], t2.get_text()[:40])
# 3. no leader line crosses any label other than its own number
for ln, i in LEAD:
    xy = fig.transFigure.transform(np.c_[ln.get_xdata(), ln.get_ydata()])
    seg = LineString(xy)
    for t, b in boxes:
        if t is NUM[i]:
            continue
        assert not seg.intersects(sbox(b.x0, b.y0, b.x1, b.y1)), ("leader line crosses a label", i + 1, t.get_text()[:40])
print(f"checks passed: {len(CHECK)} map labels clear land and points by 25 km; {len(boxes)} texts without overlap; {len(LEAD)} leader lines cross no label")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "every_battle.png")
fig.savefig(out, dpi=200, facecolor=BGc)
print(out)
