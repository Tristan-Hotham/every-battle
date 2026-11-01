"""Shared paths, groupings and helpers for the every-battle project.

Raw inputs (read in place, never modified):
  /home/claude/newdata/raw8/battles/wikidata_battles.tsv
      Wikidata (CC0), fetched in 2026 through the QLever SPARQL endpoint: every item that is an instance of battle (Q178561)
      or of any subclass of it, with English label, number of Wikipedia sitelinks, own coordinates (P625), location (P276)
      label and coordinates, point in time (P585), start time (P580) and "part of" (P361) label. One row per combination
      of location and part-of value, so items repeat and are deduplicated here. Dates are in the RDF export's
      proleptic, astronomical year numbering (year 0 = 1 BCE, -216 = 217 BCE); the date precision was not exported.
  /home/claude/newdata/raw8/battles/wiki_List_of_battles_by_casualties.json
      English Wikipedia, "List of battles by casualties" (parsed HTML of one revision, CC BY-SA 4.0).
  /home/claude/newdata/raw/geo/  Natural Earth 1:50m countries and 1:10m populated places (public domain).
"""
import json, gzip, os, re, math
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("BAT_RAW", "/home/claude/newdata/raw8/battles")
GEO = os.environ.get("BAT_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("BAT_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("BATTMP", "/dev/shm/battles"), "work")
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "every-battle"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

# continents (order = legend order); "At sea" is not used here: naval battles take the continent of the nearest land
CONTS = [("Europe", "#2F5F8A"), ("Asia", "#C0392B"), ("Africa", "#D9A21B"), ("North America", "#3E8E5A"),
         ("South America", "#7A4E9C"), ("Oceania", "#2AA0A4")]
CONT_OF_NE = {"Europe": 0, "Asia": 1, "Africa": 2, "North America": 3, "South America": 4, "Oceania": 5,
              "Seven seas (open ocean)": None, "Antarctica": None}

# eras for the map buttons, collage and tables: (name, from year, to year), astronomical years
ERAS = [("Before 500 BCE", -3500, -500), ("500 BCE to 499 CE", -499, 499), ("500 to 999", 500, 999), ("1000 to 1499", 1000, 1499),
        ("1500 to 1799", 1500, 1799), ("1800 to 1913", 1800, 1913), ("1914 to 1945", 1914, 1945), ("1946 to today", 1946, 2026)]
ESHORT = ["Ancient", "Classical", "Early medieval", "High and late medieval", "Early modern", "Long 19th century", "World wars", "Since 1946"]
ECOL = ["#8C6D46", "#B08A2E", "#6F8F3A", "#2E8B7A", "#2F6F9F", "#5B4EA0", "#B3202A", "#E07B24"]

# the two world wars: theatres and campaigns recorded as "part of" are grouped into the war (only within its years)
WW2 = {"World War II", "Pacific War", "Eastern Front", "1939 Invasion of Poland", "World War II in Yugoslavia", "Battle of the Mediterranean",
       "Western Front", "Western Desert campaign", "Italian Campaign", "Norwegian Campaign", "Syria–Lebanon campaign", "Tunisia campaign",
       "Philippines campaign of 1944–1945", "Operation Overlord", "Battle of Greece", "Battle of the Atlantic", "Battle of Okinawa",
       "Burma Campaign", "New Guinea campaign", "Spring 1945 offensive in Italy", "Operation Barbarossa", "East African Campaign",
       "Battle of the Bulge", "Battle of France", "Siege of Leningrad", "Greco-Italian War", "Battle of Britain", "Battle of Normandy",
       "Operation Bagration", "Battle of Stalingrad", "Battle of Berlin", "Mediterranean and Middle East theatre of World War II",
       "Guadalcanal campaign", "Solomon Islands campaign", "Battle of Moscow", "Battle of the Dnieper", "Western Allied invasion of Germany",
       "Battle of the Philippines (1941–1942)", "Battle of Kursk", "Operation Torch", "Allied invasion of Sicily", "Dutch East Indies campaign",
       "Malayan campaign", "Battle of Hong Kong", "Gothic Line", "Battle of Monte Cassino", "Battle of the Scheldt", "Operation Market Garden",
       "Battle of the Netherlands", "Battle of Belgium", "Battle of Crete", "German invasion of Belgium", "Mariana and Palau Islands campaign",
       "Gilbert and Marshall Islands campaign", "Aleutian Islands campaign", "Battle of the Caribbean", "South-East Asian theatre of World War II",
       "Battle of Iwo Jima", "Vistula–Oder offensive", "East Prussian offensive", "Battle of Leyte"}
WW1 = {"World War I", "Western Front", "Middle Eastern theater of World War I", "WWI Eastern Front", "East African Campaign",
       "Mesopotamian campaign", "Caucasus campaign", "Battle of the Somme", "Third Battle of Ypres", "Kamerun campaign", "Gallipoli Campaign",
       "Romania in World War I", "Macedonian Front", "Battles of the Isonzo", "Sinai and Palestine Campaign", "Battle of the Frontiers",
       "Persian Campaign", "Italian Front", "Hundred Days Offensive", "Race to the Sea", "Eastern Front", "Serbian campaign",
       "Serbian campaign of World War I", "German Spring Offensive", "Battle of Verdun", "Brusilov offensive", "Battle of Arras (1917)",
       "Battle of Galicia", "Gorlice–Tarnów offensive", "South West Africa campaign", "Togoland campaign", "Senussi campaign",
       "Asian and Pacific theatre of World War I", "Battle of Jutland", "North Sea", "Atlantic U-boat campaign of World War I",
       "Mediterranean naval operations of World War I"}


def conflict_of(wars, year):
    """Grouped conflict: a theatre or campaign of a world war becomes the war, inside its years; else the primary war."""
    if year is not None and 1939 <= year <= 1945 and any(w in WW2 or "World War II" in w for w in wars):
        return "World War II"
    if year is not None and 1914 <= year <= 1918 and any(w in WW1 or re.search(r"World War I\b(?! I)", w) for w in wars):
        return "World War I"
    return None


# what kind of event the item is, from words in its English label (first match wins)
KINDS = [("Battle", r"\bbattles?\b|\bschlacht\b|\bbataille\b|\bbatalla\b|\bbatalha\b|\bbitwa\b|\bbitka\b|\bbattaglia\b"),
         ("Siege", r"\bsieges?\b|\bblockade\b|\binvestment of\b|\bdefen[cs]e of\b|\bstand of\b"),
         ("Skirmish or action", r"\bskirmish|\baction (at|of|off|near)\b|\bengagement\b|\bclash\b|\bcombat of\b|\bambush\b|\bfight (at|of)\b|\baffair\b|\bencounter\b|\bcombate\b|\bfights?\b|\bcombat\b|\bactions? in\b"),
         ("Raid, attack or capture", r"\braids?\b|\battacks?\b|\bconquest\b|\bseizure\b|\bdestruction of\b|\bsinking\b|\bbreakthrough\b|\bpocket\b|\bsack of\b|\bcapture of\b|\bfall of\b|\bstorming\b|\bassault\b|\battack (on|at)\b|\boccupation of\b|\bliberation of\b|\blanding\b|\binvasion\b"),
         ("Bombing or bombardment", r"\bbomb|\bair raid|\bshelling\b|\bairstrike|\bstrike on\b"),
         ("Massacre", r"\bmassacre\b|\bpogrom\b"),
         ("Operation or offensive", r"\boperation\b|\boffensive\b|\bcampaign\b|\bexpedition\b|\buprising\b|\brevolt\b|\brebellion\b|\bmutiny\b|\bincident\b|\bconflict\b|\bwar\b"),
         ("Other or no English label", r".")]
KCOL = ["#1D2128", "#B3202A", "#E07B24", "#7A4E9C", "#2F7FB8", "#8A1C1C", "#2E8B7A", "#A39C8E"]


def kind_of(label):
    s = (label or "").lower()
    if not s:
        return len(KINDS) - 1
    for i, (n, rx) in enumerate(KINDS[:-1]):
        if re.search(rx, s):
            return i
    return len(KINDS) - 1


def era_of(y):
    for i, (n, a, b) in enumerate(ERAS):
        if a <= y <= b:
            return i
    return 0 if y < ERAS[0][1] else None


def century_of(y):
    """Ordinal century of an astronomical year: 1 = 1 to 100 CE, 20 = 1901 to 2000, -1 = 100 BCE to 1 BCE (years -99 to 0).
    Ordinal centuries put round values such as 1300 (how Wikidata stores '13th century') in the right century."""
    if y >= 1:
        return (y - 1) // 100 + 1
    return -((1 - y - 1) // 100 + 1)


def cname(c):
    """Name of an ordinal century."""
    n = abs(c)
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf} century" + (" BCE" if c < 0 else "")


def cshort(c):
    n = abs(c)
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}" + (" BCE" if c < 0 else "")


def ytxt(y):
    """Astronomical year to text: -216 -> '217 BCE', 1066 -> '1066'."""
    return f"{1 - y} BCE" if y <= 0 else str(y)


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


class NpEnc(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, np.integer): return int(o)
        if isinstance(o, np.floating): return float(o)
        if isinstance(o, np.ndarray): return o.tolist()
        if isinstance(o, np.bool_): return bool(o)
        return super().default(o)


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(json.loads(json.dumps(obj, cls=NpEnc)))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"), cls=NpEnc)


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "x1": return f"{float(v):.1f}"
    raise ValueError(f)


# hexagon grid in the Equal Earth projection (EPSG:8857), so every hexagon covers the same area
HEX_R = 60000.0           # circumradius in metres: about 9,350 km2 per hexagon, roughly the size of Flanders


def hex_of(x, y, r=HEX_R):
    """Pointy-top axial hex coordinates (q, r) of projected points."""
    q = (math.sqrt(3) / 3 * x - y / 3) / r
    rr = (2 / 3 * y) / r
    s = -q - rr
    rq, rr2, rs = np.round(q), np.round(rr), np.round(s)
    dq, dr, ds = np.abs(rq - q), np.abs(rr2 - rr), np.abs(rs - s)
    a = (dq > dr) & (dq > ds)
    b = ~a & (dr > ds)
    rq = np.where(a, -rr2 - rs, rq)
    rr2 = np.where(b, -rq - rs, rr2)
    return rq.astype(int), rr2.astype(int)


def hex_centre(q, rr, r=HEX_R):
    return r * math.sqrt(3) * (q + rr / 2), r * 1.5 * rr


def hex_ring(q, rr, r=HEX_R):
    cx, cy = hex_centre(q, rr, r)
    return [(cx + r * math.cos(math.radians(60 * k - 30)), cy + r * math.sin(math.radians(60 * k - 30))) for k in range(6)]


# names for the most fought-over hexagons (axial q, r), from the places and battles inside each (see 04_results.py)
HEXNAME = {(-31, 67): "Arras, Artois and southern Flanders", (8, 44): "Jerusalem, Gaza and the coastal plain", (-22, 61): "Verona and the Mincio",
           (7, 46): "Acre, Tyre and Galilee", (-32, 63): "Cholet and the Vendée", (-31, 68): "Antwerp, Ghent and the Scheldt",
           (-33, 63): "Nantes and the Pays de Retz", (90, 48): "Kyoto, Osaka and Nara", (-31, 66): "Amiens and the Somme",
           (-23, 61): "Milan, Pavia and the Adda", (-30, 67): "Brussels, Waterloo and Leuven", (-19, 69): "Warsaw",
           (-27, 57): "Barcelona and central Catalonia", (-6, 55): "Gallipoli and the Dardanelles", (-18, 57): "Rome",
           (-31, 58): "Vitoria and the Basque Country", (-37, 69): "The Welsh Marches", (-7, 51): "Pylos and Messenia",
           (-30, 50): "Strait of Gibraltar and Cádiz", (6, 50): "Aleppo", (-31, 65): "Paris", (-33, 64): "Laval and eastern Brittany",
           (-32, 68): "Dunkirk and Ypres", (-34, 64): "Auray and southern Brittany", (-26, 57): "Girona and Empordà",
           (79, 52): "Seoul and the Imjin", (-91, 54): "Antietam and Harpers Ferry", (-8, 53): "Thermopylae and Boeotia",
           (-21, 60): "Modena and Bologna", (-17, 51): "Carthage and Tunis", (-16, 56): "Benevento and Capua", (15, 46): "Baghdad",
           (-17, 56): "Naples, Cumae and the Garigliano", (9, 55): "Yerevan and the Ararat plain", (-24, 61): "Turin, Novara and Marengo",
           (-31, 69): "The Hague and Rotterdam", (6, 49): "Hama, Apamea and Idlib", (5, 50): "Antioch", (7, 47): "Beirut and Damascus road",
           (-8, 52): "Patras and the Gulf of Corinth", (-29, 51): "Málaga"}
# names for the most fought-over regions (a hexagon and its six neighbours), keyed by the centre hexagon
REGNAME = {(-31, 67): "Flanders, Artois and Brabant", (-33, 64): "Western France, from the Vendée to Normandy", (8, 45): "The southern Levant: Galilee, Jerusalem, Gaza and Damascus",
           (-22, 61): "Lombardy and the Po valley", (-36, 69): "The Welsh Marches and the English Midlands", (-27, 57): "Catalonia",
           (-7, 52): "Southern and central Greece", (-18, 68): "Masovia and Little Poland", (-26, 65): "Alsace and the Upper Rhine",
           (-90, 52): "Richmond and eastern Virginia", (-40, 74): "Central Scotland and the Highlands", (-31, 58): "The Basque Country and Navarre",
           (-22, 67): "Bohemia and Silesia", (-30, 69): "The Lower Rhine and Gelderland", (-17, 57): "Rome to Naples"}
