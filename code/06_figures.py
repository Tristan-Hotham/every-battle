"""Static figures: header.png (1200 x 630 social card), blog figures (release/blog/b_*.png) and paper figures
(release/paper/f_*.png). All numbers come from data/results.json, data/battles.csv or data/hexes.json."""
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.patches import Rectangle, Polygon as MPolygon
from figstyle import *

R = jload(f"{DATA}/results.json")
D = pd.read_csv(f"{DATA}/battles.csv", keep_default_na=False, na_values=[""])
M = D[D.lat.notna() & D.year.notna()].copy()
M["e"] = M.year.map(lambda y: era_of(int(y)))
X, Y = proj(M.lon.values, M.lat.values)
BL = os.path.join(ROOT, "release", "blog"); PP = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PP, exist_ok=True)
HEXC = LinearSegmentedColormap.from_list("hx", ["#FFF1CD", "#FAC878", "#EC8842", "#CC422C", "#8C1424", "#3E0818"])
SEAc, LANDc = "#E6ECEE", "#E2DCCD"
WEXT = ext_of(-128, -50, 150, 66)
CC = [c[1] for c in CONTS]


def dotmap(ax, ext, sel=None, s=2.2, alpha=.75):
    world(ax, ext, land=LANDc, ec="#FFFFFF", lw=.25, sea=SEAc)
    m = np.ones(len(M), bool) if sel is None else sel
    order = np.argsort(M.e.values[m])
    for e in range(len(ERAS)):
        k = m & (M.e.values == e)
        ax.scatter(X[k], Y[k], s=s, c=ECOL[e], alpha=alpha, lw=0, zorder=3 + e * .01)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])


def era_legend(fig, x, y, cols=4, dx=.22, dy=.035, fs=11, labels=None, square=False):
    from matplotlib.patches import Circle, Rectangle as Rc
    W, H = fig.get_size_inches()
    for i, (n, a, b) in enumerate(ERAS):
        cx, cy = x + (i % cols) * dx, y - (i // cols) * dy
        r = .0055
        if square:
            fig.patches.append(Rc((cx, cy - r * W / H), 2 * r, 2 * r * W / H, transform=fig.transFigure, fc=ECOL[i], ec="none"))
        else:
            from matplotlib.patches import Ellipse
            fig.patches.append(Ellipse((cx + r, cy), 2 * r, 2 * r * W / H, transform=fig.transFigure, fc=ECOL[i], ec="none"))
        fig.text(cx + .018, cy, (labels or [e[0] for e in ERAS])[i], color=FG, fontsize=fs, va="center", ha="left")


# ---------- header 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ext = ext_of(-12, 24, 62, 62)
ax = fig.add_axes([.44, .02, .56, .96]); dotmap(ax, ext, s=3.2, alpha=.8)
ax.add_patch(Rectangle((ext[0], ext[2]), ext[1] - ext[0], ext[3] - ext[2], fc="none", ec="#C9C3B6", lw=.8, zorder=6))
fig.text(.04, .9, "Every battle", fontproperties=DISP, fontsize=52, color=FG, va="top")
fig.text(.04, .76, "in history", fontproperties=DISP, fontsize=52, color=HOT, va="top")
fig.text(.04, .6, f"{R['n_map']:,} battles with a place and a date,\n{R['first']['year_text']} to 2026, from Wikidata.\n"
         f"Most fought-over: {R['flanders']['name'].split(',')[0]}, {R['flanders']['n']} battles.\n"
         f"Europe: {R['europe_pct']:.0f}% of battles, {R['europe_land_pct']:.0f}% of the land.", fontproperties=SERP, fontsize=15, color=FG, va="top", linespacing=1.45)
era_legend(fig, .04, .25, cols=2, dx=.19, dy=.045, fs=10)
fig.text(.04, .04, "maps.tristanhotham.com/every-battle", fontsize=10, color=MUT, va="bottom")
save(fig, os.path.join(ROOT, "header.png"), dpi=100)

# ---------- world map of every battle ----------
for out, dpi in ((f"{BL}/b_world.png", 150), (f"{PP}/f_world.png", 200)):
    fig = plt.figure(figsize=(12, 6.6), facecolor=BG)
    ax = fig.add_axes([.01, .1, .98, .88]); dotmap(ax, WEXT, s=1.6)
    era_legend(fig, .03, .07, cols=4, dx=.24, dy=.04, fs=10.5)
    save(fig, out, dpi=dpi)

# ---------- small multiples by era (hexagons) ----------
HX = jload(f"{DATA}/hexes.json")

EEXT = ext_of(-20, 22, 80, 60)
gs = 46
VMAX = 1
for e in range(len(ERAS)):
    f = plt.figure(); h = f.add_subplot().hexbin(X[M.e.values == e], Y[M.e.values == e], gridsize=gs, extent=WEXT, mincnt=1); VMAX = max(VMAX, h.get_array().max()); plt.close(f)
NORM = LogNorm(1, VMAX)
for out, dpi in ((f"{BL}/b_eras.png", 150), (f"{PP}/f_eras.png", 200)):
    fig = plt.figure(figsize=(12, 15), facecolor=BG)
    pw = .465; ph = pw * 12 / 15 * (WEXT[3] - WEXT[2]) / (WEXT[1] - WEXT[0])
    for k, (n, a, b) in enumerate(ERAS):
        col, row = k % 2, k // 2
        y0 = .955 - (row + 1) * ph - row * .045
        ax = fig.add_axes([.025 + col * (pw + .02), y0, pw, ph])
        world(ax, WEXT, land=LANDc, ec="#FFFFFF", lw=.2, sea=SEAc)
        m = M.e.values == k
        ax.hexbin(X[m], Y[m], gridsize=gs, extent=WEXT, mincnt=1, cmap=HEXC, norm=NORM, lw=.3, edgecolors=BG, zorder=3)
        ax.set_xlim(WEXT[0], WEXT[1]); ax.set_ylim(WEXT[2], WEXT[3])
        ax.add_patch(Rectangle((WEXT[0], WEXT[2]), WEXT[1] - WEXT[0], WEXT[3] - WEXT[2], fc="none", ec="#C9C3B6", lw=.8, zorder=6))
        er = R["eras"][k]
        fig.text(.025 + col * (pw + .02), y0 + ph + .006, n, fontproperties=DISPB, fontsize=16, color=FG, va="bottom")
        fig.text(.025 + col * (pw + .02) + pw, y0 + ph + .007, f"{er['n_map']:,} battles · Europe {er['pct_cont'][0]:.0f}% · Asia {er['pct_cont'][1]:.0f}%", fontsize=10, color=MUT, va="bottom", ha="right")
    lx = fig.add_axes([.03, .035, .25, .01]); lx.imshow(np.linspace(0, 1, 256)[None, :], cmap=HEXC, aspect="auto"); lx.set_axis_off()
    fig.text(.03, .022, "1", fontsize=9.5, color=MUT, va="top"); fig.text(.28, .022, f"{int(VMAX)}", fontsize=9.5, color=MUT, va="top", ha="right")
    fig.text(.3, .036, "battles per hexagon (log scale; hexagons are equal in projected area)", fontsize=10, color=FG, va="center")
    save(fig, out, dpi=dpi)

# ---------- battles per century ----------
C = [r for r in R["centuries"] if r["c"] >= -13]
for out, dpi in ((f"{BL}/b_centuries.png", 150), (f"{PP}/f_centuries.png", 200)):
    fig, ax = plt.subplots(figsize=(12, 5.6), facecolor=BG); ax.set_facecolor(BG); spines(ax)
    x = np.arange(len(C)); bottom = np.zeros(len(C))
    for k, (n, col) in enumerate(CONTS):
        v = np.array([r["by_cont"][k] for r in C]); ax.bar(x, v, bottom=bottom, color=col, width=.82, label=n); bottom += v
    rest = np.array([r["n"] for r in C]) - bottom
    ax.bar(x, rest, bottom=bottom, color="#BDB6A8", width=.82, label="Dated, not mapped or open ocean")
    ax.set_xticks([i for i, r in enumerate(C) if r["c"] in (-10, -5, -1, 1, 5, 10, 15, 19, 21)])
    ax.set_xticklabels([r["short"].replace(" BCE", "\nBCE") for r in C if r["c"] in (-10, -5, -1, 1, 5, 10, 15, 19, 21)], fontsize=10)
    ax.set_ylabel("battles per century"); ax.yaxis.grid(True, color=RULE); ax.set_axisbelow(True)
    ax.set_yticks([0, 1000, 2000, 3000]); ax.set_yticklabels(["0", "1,000", "2,000", "3,000"])
    i19 = [r["c"] for r in C].index(19); ax.text(i19, C[i19]["n"] + 60, f"{C[i19]['n']:,}", ha="center", fontsize=10.5, fontweight="bold")
    ax.legend(frameon=False, loc="upper left", fontsize=10, ncol=1)
    save(fig, out, dpi=dpi)

# ---------- centre of war ----------
CE = R["centres"]
cmap = LinearSegmentedColormap.from_list("cw", ["#D9A21B", "#D66028", "#6E0A16"])
CEXT = ext_of(-14, 27, 60, 58)
LB = {-5: ("5th BCE", 18.6, 35.4), -1: ("1st BCE", 12.6, 38.9), 2: ("2nd and 3rd", 52.5, 39.0), 20: ("20th", 31.0, 43.6), 7: ("7th and 21st", 26.5, 33.0),
      19: ("19th", -7, 46.6), 15: ("5th to 18th:\naround the Alps", 2.0, 56.0)}
for out, dpi in ((f"{BL}/b_centre.png", 150), (f"{PP}/f_centre.png", 200)):
    fig = plt.figure(figsize=(12, 7.4), facecolor=BG)
    ax = fig.add_axes([.01, .08, .98, .9]); world(ax, CEXT, land=LANDc, ec="#FFFFFF", lw=.35, sea=SEAc)
    cx, cy = proj([c["lon"] for c in CE], [c["lat"] for c in CE])
    for i in range(1, len(CE)):
        ax.plot(cx[i - 1:i + 1], cy[i - 1:i + 1], color=cmap(i / (len(CE) - 1)), lw=2.4, alpha=.85, zorder=4, solid_capstyle="round")
    ax.scatter(cx, cy, s=70, c=[cmap(i / (len(CE) - 1)) for i in range(len(CE))], edgecolors=FG, linewidths=.8, zorder=5)
    for c, (t, lo, la) in LB.items():
        k = [x["c"] for x in CE].index(c); px, py = proj(lo, la)
        ax.text(px, py, t, fontsize=13, fontweight="bold", color=FG if c == 15 else cmap(k / (len(CE) - 1)), ha="center", va="center", zorder=7,
                path_effects=[__import__("matplotlib.patheffects", fromlist=["x"]).withStroke(linewidth=3, foreground=SEAc)])
    ax.set_xlim(CEXT[0], CEXT[1]); ax.set_ylim(CEXT[2], CEXT[3])
    lx = fig.add_axes([.04, .045, .3, .016]); lx.imshow(np.linspace(0, 1, 256)[None, :], cmap=cmap, aspect="auto"); lx.set_axis_off()
    fig.text(.04, .03, "6th century BCE", fontsize=10, va="top"); fig.text(.34, .03, "21st century", fontsize=10, va="top", ha="right")
    fig.text(.37, .053, "Spherical median of each century's mapped battles (centuries with 20 or more)", fontsize=10.5, color=MUT, va="center")
    save(fig, out, dpi=dpi)

# ---------- most fought-over regions (map and ranking) ----------
SHORTREG = {"The southern Levant: Galilee, Jerusalem, Gaza and Damascus": "The southern Levant", "Western France, from the Vendée to Normandy": "Western France",
            "The Welsh Marches and the English Midlands": "Welsh Marches and Midlands", "Central Scotland and the Highlands": "Central Scotland"}
short_reg = lambda n: SHORTREG.get(n, n)
from matplotlib import patheffects as pe
REXT = ext_of(-11, 29, 40, 60)
tops = HX["top"]["regions"]
for out, dpi in ((f"{BL}/b_places.png", 150), (f"{PP}/f_places.png", 200)):
    fig = plt.figure(figsize=(12, 7.2), facecolor=BG)
    ax = fig.add_axes([.0, .0, .6, 1]); world(ax, REXT, land=LANDc, ec="#FFFFFF", lw=.35, sea=SEAc)
    k = (M.lon > -13) & (M.lon < 42) & (M.lat > 27) & (M.lat < 62)
    ax.hexbin(X[k], Y[k], gridsize=60, extent=REXT, mincnt=1, cmap=HEXC, norm=LogNorm(1, 60), lw=.2, edgecolors=BG, zorder=3)
    for i, g in enumerate(tops):
        ring = np.array(g["ring"]); px, py = proj(ring[:, 1], ring[:, 0])
        if px.min() < REXT[0] or px.max() > REXT[1]:
            continue
        ax.add_patch(MPolygon(np.c_[px, py], closed=True, fc="none", ec=FG, lw=1.6, zorder=6))
        ax.text(px.mean(), py.max() + 25000, str(i + 1), fontsize=12, fontweight="bold", ha="center", va="bottom", zorder=7,
                path_effects=[pe.withStroke(linewidth=3, foreground="white")])
    ax.set_xlim(REXT[0], REXT[1]); ax.set_ylim(REXT[2], REXT[3])
    bx = fig.add_axes([.62, .07, .36, .86]); bx.set_facecolor(BG)
    regs = R["regions"]; n = len(regs)
    for i, g in enumerate(regs):
        yv = n - i; left = 0
        for e, v in enumerate(g["by_era"]):
            bx.barh(yv - .22, v, left=left, color=ECOL[e], height=.34); left += v
        bx.text(0, yv + .2, f"{i + 1}. {short_reg(g['name'])}", va="center", fontsize=10)
        bx.text(left + 5, yv - .22, f"{g['n']}", va="center", fontsize=9.5, fontweight="bold")
    bx.set_xlim(0, 420); bx.set_ylim(.3, n + .7); bx.axis("off")
    fig.text(.62, .955, "Most fought-over regions: battles by era", fontsize=10.5, color=MUT)
    era_legend(fig, .62, .05, cols=4, dx=.095, dy=.03, fs=8, labels=ESHORT, square=True)
    save(fig, out, dpi=dpi)

# ---------- wars ----------
Wr = R["wars"][:20]
for out, dpi in ((f"{BL}/b_wars.png", 150), (f"{PP}/f_wars.png", 200)):
    fig, ax = plt.subplots(figsize=(11, 7.4), facecolor=BG); ax.set_facecolor(BG); spines(ax)
    yv = np.arange(len(Wr))[::-1]
    ax.barh(yv, [w["n"] for w in Wr], color=[CC[w["cont"]] for w in Wr], height=.7)
    ax.set_yticks(yv); ax.set_yticklabels([w["name"] for w in Wr], fontsize=10.5)
    for y_, w in zip(yv, Wr):
        ax.text(w["n"] + 8, y_, f"{w['n']}", va="center", fontsize=10, fontweight="bold")
    ax.set_xlabel("battle items in Wikidata (world war theatres grouped)"); ax.xaxis.grid(True, color=RULE); ax.set_axisbelow(True)
    hs = [Rectangle((0, 0), 1, 1, color=CC[k]) for k in (0, 1, 3)]
    ax.legend(hs, ["Europe", "Asia", "North America"], frameon=False, loc="lower right", title="most battles in", fontsize=10)
    fig.tight_layout(); save(fig, out, dpi=dpi)

# ---------- bias: sitelinks and Europe ----------
SL = jload(f"{DATA}/sitelinks_by_year.json")["rows"]
KN = [(0, -3000), (90, -1000), (230, -300), (380, 500), (540, 1300), (690, 1700), (820, 1850), (1000, 2026)]
def y2p(y):
    for (a, ya), (b, yb) in zip(KN[:-1], KN[1:]):
        if y <= yb:
            return a + (b - a) * (y - ya) / (yb - ya)
    return 1000
rng = np.random.default_rng(1)
for out, dpi in ((f"{BL}/b_bias.png", 150), (f"{PP}/f_bias.png", 200)):
    fig = plt.figure(figsize=(12, 6.2), facecolor=BG)
    ax = fig.add_axes([.06, .14, .56, .78]); ax.set_facecolor(BG); spines(ax)
    xs = np.array([y2p(r[0]) for r in SL]); ys = np.log10(1 + np.array([r[1] for r in SL])) + rng.normal(0, .012, len(SL))
    cs = [CC[r[2]] if r[2] >= 0 else "#999" for r in SL]
    ax.scatter(xs + rng.normal(0, 1.2, len(SL)), ys, s=2, c=cs, alpha=.3, lw=0)
    q = R["sl_quant"]
    ax.plot([y2p(r[1]) for r in q], [np.log10(1 + r[3]) for r in q], color=HOT, lw=2.4, label="90th percentile")
    ax.plot([y2p(r[1]) for r in q], [np.log10(1 + r[2]) for r in q], color=FG, lw=2.4, label="median")
    tk = [0, 1, 3, 10, 30, 100]; ax.set_yticks([np.log10(1 + t) for t in tk]); ax.set_yticklabels(tk)
    xt = [-3000, -300, 500, 1300, 1700, 1850, 2026]; ax.set_xticks([y2p(t) for t in xt]); ax.set_xticklabels([ytxt(t) for t in xt], fontsize=10)
    ax.set_ylabel("Wikipedia language editions"); ax.set_xlim(0, 1005); ax.legend(frameon=False, loc="upper left", fontsize=10)
    ax.set_title("Each dot a dated battle (stretched time scale)", fontsize=11, color=MUT, loc="left")
    bx = fig.add_axes([.77, .14, .21, .78]); bx.set_facecolor(BG); spines(bx)
    lab = [c[0] for c in CONTS]; yv = np.arange(len(lab))[::-1]
    bx.barh(yv + .18, [r["pct"] for r in R["by_cont"]], height=.36, color=CC, label="share of mapped battles")
    bx.barh(yv - .18, R["land_pct"], height=.36, color="#C9C3B6", label="share of land")
    for y_, a, b in zip(yv, [r["pct"] for r in R["by_cont"]], R["land_pct"]):
        bx.text(a + 1, y_ + .18, f"{a:.0f}%", va="center", fontsize=9.5, fontweight="bold"); bx.text(b + 1, y_ - .18, f"{b:.0f}%", va="center", fontsize=9.5, color=MUT)
    bx.set_yticks(yv); bx.set_yticklabels(lab, fontsize=10.5); bx.set_xlim(0, 66); bx.set_xticks([])

    bx.set_title("Share of battles (colour)\nand of land (grey)", fontsize=11, color=MUT, loc="left")
    save(fig, out, dpi=dpi)
print("figures done", sorted(os.listdir(BL)), sorted(f for f in os.listdir(PP) if f.endswith(".png")))
