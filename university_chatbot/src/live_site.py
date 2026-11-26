"""Live sync with the college website (https://www.abes.ac.in/courses-offered.html).

How it works
  1. A background thread downloads the page (fixed URL, host allow-listed, nothing from the student is sent).
  2. The HTML is parsed into facts (fees, hostel fees, seats, documents, refund, ...).
  3. If anything fails (no internet, page layout changed) the bot silently uses the last good copy
     (data/live_cache.json) or the bundled snapshot (data/abes_snapshot.json).
Run  `python src/live_site.py --check`  to test the live download + parsing on your machine."""
import re, json, time, threading, pathlib, datetime as dt
from urllib.parse import urlparse
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:                      # bot still works from the snapshot
    requests = BeautifulSoup = None

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = "https://www.abes.ac.in/courses-offered.html"
ALLOWED_HOSTS = {"www.abes.ac.in", "abes.ac.in"}
SNAPSHOT = ROOT / "data" / "abes_snapshot.json"
CACHE = ROOT / "data" / "live_cache.json"
REFRESH_HOURS = 6

# ---------------------------------------------------------------- helpers
def money(text):
    m = re.sub(r"[^\d.]", "", str(text).replace(",", ""))
    if not m or m == ".": return None
    v = float(m); return int(v) if v == int(v) else v

def inr(n):
    """1181200 -> 'Rs. 11,81,200' (Indian digit grouping)."""
    s = str(int(n)); head, tail = s[:-3], s[-3:]
    if head:
        parts = []
        while len(head) > 2: parts.insert(0, head[-2:]); head = head[:-2]
        if head: parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return "Rs. " + s

def fetch_html(url=PAGE, timeout=8):
    if requests is None: raise RuntimeError("requests / beautifulsoup4 not installed")
    if urlparse(url).hostname not in ALLOWED_HOSTS or urlparse(url).scheme != "https": raise ValueError("URL not allowed")
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Abes Assist-student-project/1.0 (educational prototype)"})
    r.raise_for_status()
    if len(r.content) > 3_000_000: raise ValueError("page too large")
    return r.text

# ---------------------------------------------------------------- parsing
def parse_sections(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript"]): t.decompose()
    cur = {"heading": "", "texts": [], "tables": []}; sections = [cur]
    for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "p", "li", "table"]):
        if el.name == "table":
            if el.find_parent("table"): continue
            rows = [[c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])] for tr in el.find_all("tr")]
            cur["tables"].append([r for r in rows if any(r)])
        elif el.name[0] == "h" and el.name != "hr":
            cur = {"heading": el.get_text(" ", strip=True), "texts": [], "tables": []}; sections.append(cur)
        elif not el.find_parent("table"):
            t = el.get_text(" ", strip=True)
            if t and t not in cur["texts"]: cur["texts"].append(t)
    lines = [l.strip() for l in soup.get_text("\n", strip=True).split("\n") if l.strip()]
    return sections, lines

def _sec(sections, pattern):
    return [s for s in sections if re.search(pattern, s["heading"], re.I)]

def _lines_between(lines, start, end):
    out, on = [], False
    for l in lines:
        if re.search(start, l, re.I): on = True; continue
        if on and re.search(end, l, re.I): break
        if on: out.append(l)
    return out

def parse_fee_table(tb):
    """rows -> {'heads': [[name, amount]...], 'extras': [...rows after the total...], 'total': n} or None"""
    heads, extras, total, after = [], [], None, False
    for r in tb:
        label = next((c for c in r if re.search(r"[A-Za-z]", c) and not re.fullmatch(r"(?i)(sr\.? ?no\.?|fee heads|amount.*|particulars|academic fee structure.*)", c.strip())), None)
        amt = money(r[-1]) if len(r) > 1 else None
        if label and re.search(r"(?i)\btotal\b", label):
            total = amt or next((money(c) for c in r[1:] if money(c)), None); after = True
        elif label and amt is not None and re.search(r"fee|support|bank|registration|welfare|deposit|development", label, re.I):
            (extras if after else heads).append([re.sub(r"[*#]+$", "", label).strip(), amt])
    return {"heads": heads, "extras": extras, "total": total} if heads and total else None

TAB_LABELS = {"b.tech": "B.Tech", "btech": "B.Tech", "b.tech-le": "B.Tech-LE", "m.tech": "M.Tech", "mca": "MCA", "bca": "BCA", "b.tech-wp": "B.Tech-WP"}

def fee_tabs_from_html(html):
    """Read the tab buttons under 'Fee Structure (2026-27)' and the panel each one points to.
    Returns {tab label: fee dict}; empty dict when the page's tab structure is not recognised (then nothing is guessed)."""
    soup = BeautifulSoup(html, "html.parser"); out = {}
    h = soup.find(lambda t: t.name in ("h1", "h2", "h3", "h4") and re.search(r"fee structure \(\s*\d{4}", t.get_text(" ", strip=True), re.I))
    if not h: return out
    for el in h.find_all_next(["a", "button", "li", "span", "div"], limit=80):
        key = TAB_LABELS.get(re.sub(r"\s+", "", el.get_text(" ", strip=True)).lower())
        if not key or key in out: continue
        target = None
        for attr in ("data-bs-target", "data-target", "href", "aria-controls", "data-tab", "data-id"):
            v = el.get(attr)
            if v and v.strip("#") and v != "#": target = v.strip().lstrip("#"); break
        if not target:
            m = re.findall(r"['\"]([\w-]+)['\"]", el.get("onclick", "") or ""); target = m[-1] if m else None
        pane = soup.find(id=target) if target else None
        if not pane: continue
        for tb in pane.find_all("table"):
            rows = [[c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])] for tr in tb.find_all("tr")]
            fee = parse_fee_table([r for r in rows if any(r)])
            if fee: out[key] = fee; break
    return out if len(out) >= 3 else {}      # need most tabs to trust the mapping

def extract_facts(html):
    sections, lines = parse_sections(html); facts = {}
    # fee tables: tab-aware if the page structure allows, otherwise only the first table (= first tab = B.Tech)
    tabs = fee_tabs_from_html(html)
    for sec in _sec(sections, r"fee structure \(\s*\d{4}\s*-\s*\d{2,4}"):
        m = re.search(r"\d{4}\s*-\s*\d{2,4}", sec["heading"]); session = m.group(0).replace(" ", "")
        first = next((fee for fee in (parse_fee_table(tb) for tb in sec["tables"]) if fee), None)
        base = tabs.get("B.Tech") or first
        if base:
            facts["fee"] = dict(base, session=session, programme="B.Tech", mapping="tabs" if tabs else "assumed-first-table")
            facts["fee_tabs"] = {k: v for k, v in tabs.items()}; break
    # hostel
    for key, pat in (("hostel_boys", r"hostel fee structure for boys"), ("hostel_girls", r"hostel fee structure for girls")):
        for s in _sec(sections, pat):
            for tb in s["tables"]:
                for r in tb:
                    if r and any(re.match(r"(?i)total \(\s*20\d\d", c) for c in r):
                        nums = [money(c) for c in r if re.fullmatch(r"[\d,]{4,}", c.strip())]
                        if nums: facts[key] = nums
    # seats
    progs, group, seen = [], "", set()
    for s in _sec(sections, r"programs? offered"):
        for tb in s["tables"]:
            for r in tb[1:]:
                if len(r) < 2: continue
                if not re.fullmatch(r"\d+", r[1].strip()): group = r[0]; continue
                if (group, r[0]) not in seen: seen.add((group, r[0])); progs.append({"group": group, "name": r[0], "seats": int(r[1])})
    if progs: facts["programs"] = progs
    # documents
    docs = []
    for s in _sec(sections, r"documents required"):
        for tb in s["tables"]:
            for r in tb[1:]:
                n = re.sub(r"\s+", " ", r[0]).strip()
                if n and n not in docs: docs.append(n)
    if docs: facts["documents"] = docs
    # text facts
    allt = [t for s in sections for t in s["texts"]] + lines
    pick = lambda pat: next((t for t in allt if re.search(pat, t, re.I)), None)
    adm = [pick(r"^\s*85% seats"), pick(r"^\s*15% seats")]
    if all(adm): facts["admission"] = adm
    ref = [pick(r"in case of cancellation of admission"), pick(r"in case of withdrawal from hostel")]
    if all(ref): facts["refund"] = ref
    pay = _lines_between(lines, r"permissible mode of payment", r"restricted payment conditions")
    pay = [re.sub(r"(?i)\s*(current )?account no.*$", "", l) for l in pay if not re.fullmatch(r"[\d\W]+", l)]   # never repeat bank account numbers
    restr = pick(r"cheques and cash payments are not accepted")
    if pay: facts["payment"] = {"modes": pay[:8], "restriction": restr}
    enq = []
    for s in _sec(sections, r"admission enquiry"):
        for tb in s["tables"]:
            for r in tb[1:]:
                if len(r) >= 3 and re.search(r"\d{10}", r[-1]): enq.append([r[1], r[-1]])
    if enq: facts["enquiry"] = enq
    return facts

def valid(facts): return bool(facts.get("fee") and facts["fee"].get("total") and facts.get("programs"))

# ---------------------------------------------------------------- live service
class LiveSite:
    def __init__(self, auto_refresh=False, url=PAGE):
        self.url, self.lock = url, threading.Lock()
        self.facts, self.meta = {}, {"source": "none", "synced_at": None, "error": None}
        self._load(CACHE, "cache") or self._load(SNAPSHOT, "snapshot")
        if auto_refresh and requests is not None:
            threading.Thread(target=self._loop, daemon=True).start()

    def _load(self, path, label):
        try:
            d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
            if valid(d["facts"]):
                self.facts, self.meta = d["facts"], {"source": label, "synced_at": d["synced_at"], "error": None}; return True
        except Exception: pass
        return False

    def refresh(self):
        try:
            facts = extract_facts(fetch_html(self.url))
            if not valid(facts): raise ValueError("page layout not recognised - kept previous data")
            now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
            with self.lock: self.facts, self.meta = facts, {"source": "live", "synced_at": now, "error": None}
            CACHE.write_text(json.dumps({"synced_at": now, "facts": facts}, ensure_ascii=False, indent=1), encoding="utf-8"); return True
        except Exception as e:
            with self.lock: self.meta["error"] = f"{type(e).__name__}: {e}"[:200]
            return False

    def _loop(self):
        while True:
            self.refresh(); time.sleep(REFRESH_HOURS * 3600)

    # ---------- answer composers (return None if the facts are missing) ----------
    def footer(self):
        m = self.meta; when = ""
        if m["synced_at"]:
            try: when = dt.datetime.strptime(m["synced_at"], "%Y-%m-%d %H:%M").strftime("%d %b %Y, %H:%M")
            except ValueError: when = m["synced_at"]
        if m["source"] == "live": return f"\n\n*Source: abes.ac.in (courses-offered page) · live data synced {when}*"
        return f"\n\n*Source: abes.ac.in (courses-offered page) · saved copy of {when} – live refresh not available right now, please confirm on the website*"

    def compose(self, name, question=""):
        f, fn = self.facts, getattr(self, "_c_" + name, None)
        try: text = fn(f, question) if fn else None
        except Exception: text = None
        return (text + self.footer()) if text else None

    PROGRAMMES = [(r"\bbca\b", "BCA"), (r"\bmca\b", "MCA"), (r"m\.?\s?tech|mtech", "M.Tech"), (r"lateral|\blet?e?\b", "B.Tech-LE"),
                  (r"working professional|\bwp\b", "B.Tech-WP")]

    def _c_fees(self, f, q=""):
        prog = next((n for pat, n in self.PROGRAMMES if re.search(pat, q, re.I)), None)
        tabs, base = f.get("fee_tabs") or {}, f["fee"]
        x = base if prog is None else tabs.get(prog)
        if x is None:     # a programme was asked for but its table cannot be identified for sure -> do not show another programme's fee
            enq = (f.get("enquiry") or [["", "8448494111"]])[0][1].split()[0]
            return (f"I couldn't read the **{prog}** fee table from the website with certainty, so I won't guess. Please open the **{prog}** tab under "
                    f"*Fee Structure ({base['session']})* at abes.ac.in/courses-offered.html, or call admissions on {enq}. "
                    f"(For reference only: the B.Tech total is {inr(base['total'])} per year.)")
        name = prog or "B.Tech"
        lines = [f"**ABES fee structure {base['session']} – {name}**"]
        lines += [f"• {n}: {inr(a)}" for n, a in x["heads"]]
        lines.append(f"**Total: {inr(x['total'])}**" + (" (includes the refundable one-time security deposit)." if any("Security" in n for n, _ in x["heads"]) else "."))
        if prog and prog != "B.Tech" and x["total"] == base["total"] and x["heads"] == base["heads"]:
            enq = (f.get("enquiry") or [["", "8448494111"]])[0][1].split()[0]
            lines.append(f"Note: the website currently lists exactly the same fee table for {prog} as for B.Tech. Please confirm with admissions ({enq}) before paying.")
        if x.get("extras"): lines.append("Also payable: " + "; ".join(f"{n} {inr(a)}" for n, a in x["extras"]))
        if prog is None: lines.append("This is the B.Tech fee. Ask for \"BCA fee\", \"MCA fee\", \"M.Tech fee\", \"lateral entry fee\" or \"working professional fee\" for the other tabs. Hostel fees are separate.")
        return "\n".join(lines)

    def _c_hostel_fee(self, f, q=''):
        b, g = f.get("hostel_boys"), f.get("hostel_girls")
        if not (b and len(b) == 6): return None
        s = ("**ABES hostel fee 2026-27** (includes Rs. 5,000 refundable security; covers registration, laundry, lodging & boarding)\n"
             f"• Boys, 4-seater: Non-AC {inr(b[0])} / AC {inr(b[1])}\n• Boys, 3-seater: Non-AC {inr(b[2])} / AC {inr(b[3])}\n• Boys, 2-seater: Non-AC {inr(b[4])} / AC {inr(b[5])}")
        if g and len(g) == 3: s += f"\n• Girls (AC only), 4-seater {inr(g[0])} / 3-seater {inr(g[1])} / 2-seater {inr(g[2])}"
        return s + "\nRooms are allotted on a first-come, first-served basis."

    def _c_programs(self, f, q=''):
        out, last = ["**Programmes and seats at ABES (current session)**"], None
        for p in f["programs"]:
            if p["group"] != last: out.append(f"\n{p['group']}:"); last = p["group"]
            out.append(f"• {p['name']} – {p['seats']} seats")
        return "\n".join(out)

    def _c_documents(self, f, q=''):
        d = f["documents"]; s = "**Documents to bring at final admission/reporting** (two self-attested photocopies plus originals, as stated on the page):\n" + "\n".join(f"• {x}" for x in d[:14])
        return s + (f"\n…and {len(d)-14} more – see the full list on the website." if len(d) > 14 else "")

    def _c_refund(self, f, q=''):
        return "**Refund policy (new admissions, current session)**\n• " + f["refund"][0] + "\n• " + f["refund"][1]

    def _c_admission(self, f, q=''):
        s = "**How admission works at ABES**\n• " + f["admission"][0] + "\n• " + f["admission"][1]
        if f.get("enquiry"): s += "\nAdmission enquiry: " + "; ".join(f"{c}: {n}" for c, n in f["enquiry"][:3])
        return s + "\nApply online through the ERP enquiry link on the Admissions page."

    def _c_payment(self, f, q=''):
        p = f["payment"]; s = "**How to pay fees at ABES (as listed on the website)**\n" + "\n".join("• " + re.sub(r"^\d+\s*", "", m) for m in p["modes"])
        return s + (("\n" + p["restriction"]) if p.get("restriction") else "")

if __name__ == "__main__":
    import sys
    if "--check" in sys.argv:
        try:
            facts = extract_facts(fetch_html()); print("download + parse OK" if valid(facts) else "downloaded, but layout NOT recognised")
            print(json.dumps({k: (v if k != "documents" else v[:3]) for k, v in facts.items()}, indent=1, ensure_ascii=False)[:2500])
        except Exception as e: print("FAILED:", type(e).__name__, e)
    elif "--show-tabs" in sys.argv:
        tabs = fee_tabs_from_html(fetch_html())
        if not tabs: print("Tab mapping NOT recognised (only the first table is used, as B.Tech).")
        for k, v in tabs.items(): print(f"{k:10s} total = {v['total']:>9,}   tuition = {dict(v['heads']).get('Tuition Fee')}   rows = {len(v['heads'])}")
        if tabs and len({v['total'] for v in tabs.values()}) < len(tabs): print("Note: some tabs have identical totals - compare with the website's own tabs.")
    elif "--save-html" in sys.argv:
        out = ROOT / "data" / "page_dump.html"; out.write_text(fetch_html(), encoding="utf-8")
        f = extract_facts(out.read_text(encoding="utf-8")); print("saved", out, "| fee tabs recognised:", sorted(f.get("fee_tabs", {})) or "none (only first table used)")
    elif "--make-snapshot" in sys.argv:
        facts = extract_facts((ROOT / "tests" / "fixtures" / "courses_offered_sample.html").read_text(encoding="utf-8")); assert valid(facts)
        SNAPSHOT.write_text(json.dumps({"synced_at": "2026-10-31 23:50", "facts": facts}, ensure_ascii=False, indent=1), encoding="utf-8"); print("snapshot written:", sorted(facts))
