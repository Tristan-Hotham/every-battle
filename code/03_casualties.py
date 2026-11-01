"""English Wikipedia's 'List of battles by casualties' (CC BY-SA 4.0): parse its five tables (sieges and urban combat, major
operations, classical formation battles, raids and sacks, naval battles), read the highest casualty figure in each row,
and match each row to a Wikidata battle by English label (linked article title, else row text, without any bracketed
qualifier) and year (within 3 years, or inside the row's year range). Writes data/casualties.csv (CC BY-SA 4.0)."""
import io
from urllib.parse import unquote
import pandas as pd
from common import *

H = jload(f"{RAW}/wiki_List_of_battles_by_casualties.json")
REVID = H["revid"]
T = pd.read_html(io.StringIO(H["html"]), extract_links="body")
TABLES = {4: "Siege or urban combat", 5: "Major operation", 7: "Battle", 8: "Raid or sack", 9: "Naval battle"}
B = pd.read_pickle(f"{WORK}/battles.pkl")
import unicodedata
fold = lambda s: "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))
norm = lambda s: re.sub(r"\s+", " ", re.sub(r"\s*\([^)]*\)\s*$", "", s or "")).strip().lower().replace("–", "-").replace("’", "'")
norm0 = norm
norm = lambda s: norm0(fold(s))       # accents folded: Bailen matches Bailén
idx = {}
for i, (lab, y) in enumerate(zip(B.label, B.year)):
    idx.setdefault(norm(lab), []).append(i)


def years(s):
    """Astronomical year range of a 'Year' cell such as '332 BC', '213-212 BC', '1904–1905', 'c. 149 BC'."""
    s = (s or "").replace("–", "-").replace("—", "-")
    bc = bool(re.search(r"\bBC|BCE\b", s))
    ns = [int(n) for n in re.findall(r"\d{1,4}", s)]
    if not ns:
        return None
    a, b = ns[0], ns[-1] if len(ns) > 1 else ns[0]
    if bc:
        return (1 - max(a, b), 1 - min(a, b))
    if b < a and len(str(b)) < len(str(a)):          # 1914-18
        b = int(str(a)[:len(str(a)) - len(str(b))] + str(b))
    return (min(a, b), max(a, b))


def high(s):
    """Highest number in a casualty cell (ignores footnote markers)."""
    s = re.sub(r"\[[^\]]*\]", " ", s or "")
    ns = [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", s)]
    ns = [n for n in ns if n >= 10 or len(ns) == 1]
    return max(ns) if ns else None


rows = []
for ti, kind in TABLES.items():
    t = T[ti].copy()
    t.columns = [c if isinstance(c, str) else (c[0] if c[0] == c[1] or c[1] == "" else c[1]) for c in t.columns]
    for _, r in t.iterrows():
        cell = lambda x: x if isinstance(x, tuple) else ("", None)
        name, link = cell(r.iloc[0])
        if not name:
            continue
        yrs = years(cell(r.iloc[1])[0])
        conflict = cell(r.iloc[2])[0] or ""
        cas = [high(cell(x)[0]) for x in r.iloc[3:]]
        cas = [c for c in cas if c is not None]
        title = unquote(link.split("/wiki/")[-1]).replace("_", " ") if link and link.startswith("/wiki/") else ""
        cand = []
        for key in {norm(title), norm(name)}:
            cand += idx.get(key, [])
        best, how = None, ""
        if yrs:
            ok = [i for i in set(cand) if pd.notna(B.year.iloc[i]) and yrs[0] - 3 <= B.year.iloc[i] <= yrs[1] + 3]
            if ok:
                best = max(ok, key=lambda i: (B.lat.notna().iloc[i], B.sitelinks.iloc[i])); how = "label and year"
        rows.append({"table": kind, "name": dash(name), "wikipedia_title": dash(title), "year_from": yrs[0] if yrs else None,
                     "year_to": yrs[1] if yrs else None, "conflict": dash(conflict), "casualties_high": cas[0] if cas else None,
                     "casualties_low": cas[1] if len(cas) > 1 else None, "qid": B.qid.iloc[best] if best is not None else "",
                     "matched_by": how,
                     "lat": round(B.lat.iloc[best], 5) if best is not None and pd.notna(B.lat.iloc[best]) else None,
                     "lon": round(B.lon.iloc[best], 5) if best is not None and pd.notna(B.lon.iloc[best]) else None,
                     "continent": CONTS[int(B.cont.iloc[best])][0] if best is not None and pd.notna(B.cont.iloc[best]) else ""})
C = pd.DataFrame(rows)
C["year_from"] = C.year_from.astype("Int64"); C["year_to"] = C.year_to.astype("Int64")
C.to_csv(f"{DATA}/casualties.csv", index=False)
jsave({"revid": REVID, "n": len(C), "matched": int((C.qid != "").sum()), "mapped": int(C.lat.notna().sum())}, f"{WORK}/cas_meta.json")
print(len(C), "rows; matched", (C.qid != "").sum(), "mapped", C.lat.notna().sum(), "with casualties", C.casualties_high.notna().sum())
print(C.groupby("table").agg(n=("name", "size"), m=("qid", lambda s: (s != "").sum())))
print(C[C.qid == ""].sample(15, random_state=1)[["name", "wikipedia_title", "year_from"]].to_string())
print(C.sort_values("casualties_high", ascending=False).head(12)[["name", "year_from", "casualties_high", "qid"]].to_string())
