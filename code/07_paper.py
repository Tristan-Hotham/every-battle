"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays a placeholder (10.5281/zenodo.23857870)."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Every_Battle_in_History"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
R["meta"]["doi"] = "@@DOI@@"

# statements made in words in the paper only
cc = {r["c"]: r for r in R["centuries"]}
assert cc[18]["n"] < cc[20]["n"] and R["hex_top"][0]["n"] == max(h["n"] for h in R["hex_top"])
assert all(c["place"] == "Greece" for c in R["centres"] if c["c"] in (-6, -5, -4))


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    return tex(str(v))


def table(cap, lab, spec, head, rows):
    return (f"\\begin{{table}}[tbp]\\centering\\small\\caption{{{cap}}}\\label{{tab:{lab}}}\\begin{{tabular}}{{{spec}}}\\toprule {head}\\\\\\midrule\n"
            + "".join(r + "\\\\\n" for r in rows) + "\\bottomrule\\end{tabular}\\end{table}")


CN = [c[0] for c in CONTS]
TE = table("Battles by era: dated battles, mapped battles and the share of mapped battles by continent.", "eras", "lrrrrrrrr",
           "Era & Dated & Mapped & Europe & Asia & Africa & N. Am. & S. Am. & Oceania",
           [f"{tex(e['name'])} & {e['n']:,} & {e['n_map']:,} & " + " & ".join(f"{p:.0f}\\%" for p in e["pct_cont"]) for e in R["eras"]])
TC = table("The centre of war: spherical geometric median of each century's mapped battles, and the distance within which half of them lie.", "centres", "lrlr",
           "Century & Battles & Centre in or near & Half within (km)",
           [f"{tex(c['name'])} & {c['n']:,} & {tex(c['place'])}{' (sea)' if c['at_sea'] else ''} & {c['median_km']:,.0f}" for c in R["centres"]])
TR = table(f"The fifteen most fought-over regions (seven equal-area hexagons, {R['region_km2']:,.0f} km\\textsuperscript{{2}}): battles, centuries with a battle, and the most widely covered battles.", "regions", "p{4.6cm}rrp{6.4cm}",
           "Region & Battles & Centuries & Best-known battles",
           [f"{tex(g['name'])} & {g['n']} & {g['cent']} & {tex('; '.join(g['famous'][:2]))}" for g in R["regions"]])
TK = table("Battle items by the first matching word in their English label.", "kinds", "lrr", "Kind & Items & Share",
           [f"{tex(k['name'])} & {k['n']:,} & {k['pct']:.1f}\\%" for k in R["kinds"]])
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("ERAS", TE), ("CENTRES", TC), ("REGIONS", TR), ("KINDS", TK)):
    t = t.replace("{{TABLE_%s}}" % k, v)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:3]
t = t.replace("\\href{https://doi.org/@@DOI@@}{https://doi.org/@@DOI@@}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/@@DOI@@}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "@@" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
