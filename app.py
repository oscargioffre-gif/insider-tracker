"""
Insider Buy Tracker  v6
• http://openinsider.com (HTTP porta 80 + Chrome UA + BeautifulSoup)
• Carica insider role reale da OpenInsider (CEO/CFO/COO/etc.)
• Filtro settore da dati reali yfinance
• Filtro giorni lavorativi (1-7)
"""

import streamlit as st
import requests
import re
import json
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ── PAGE CONFIG ───────────────────────────────────────────────
st.set_page_config(
    page_title="Insider Buy Tracker",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── STYLES ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;background:#0d1117!important;color:#e6edf3!important}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:.8rem .9rem 4rem!important;max-width:540px!important;margin:auto}
.app-header{text-align:center;padding:1.4rem 0 .8rem}
.app-header h1{font-size:1.75rem;font-weight:800;letter-spacing:-.6px;color:#fff;margin:0}
.app-header .sub{font-size:.78rem;color:#6e7681;margin:.2rem 0 0;display:flex;align-items:center;justify-content:center;gap:6px}
.pulse{display:inline-block;width:7px;height:7px;background:#10b981;border-radius:50%;animation:blink 2s ease-in-out infinite}
@keyframes blink{0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,.6);opacity:1}50%{box-shadow:0 0 0 5px rgba(16,185,129,0);opacity:.6}}
.filter-label{font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#6e7681;margin-bottom:.2rem;display:block}
.stats-bar{display:flex;justify-content:space-around;background:#161b22;border:1px solid #21262d;border-radius:12px;padding:.75rem .5rem;margin-bottom:1rem}
.stat{flex:1;text-align:center}
.stat-n{font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:700;color:#10b981}
.stat-l{font-size:.62rem;color:#6e7681;text-transform:uppercase;letter-spacing:.07em}

/* ── Card ── */
.card{background:#161b22;border:1px solid #21262d;border-radius:14px;padding:1rem 1.1rem .9rem;margin-bottom:.8rem;position:relative;overflow:hidden;transition:border-color .18s}
.card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:4px;background:linear-gradient(180deg,#10b981,#059669);border-radius:14px 0 0 14px}
.card:hover{border-color:rgba(16,185,129,.5)}
.card-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:.55rem}
.ticker{font-family:'JetBrains Mono',monospace;font-size:1.6rem;font-weight:700;color:#fff;letter-spacing:-.5px;line-height:1}
.company-name{font-size:.72rem;color:#6e7681;margin-top:1px}
.price-pill{font-family:'JetBrains Mono',monospace;font-size:1rem;font-weight:600;color:#10b981;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.22);border-radius:8px;padding:3px 11px;white-space:nowrap}

/* ── Badges ── */
.badges{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:.65rem}
.badge{font-size:.68rem;font-weight:600;padding:2px 8px;border-radius:20px;white-space:nowrap;letter-spacing:.03em}
.b-market{background:#1c2128;color:#8b949e;border:1px solid #30363d}
.b-sector{background:rgba(99,102,241,.1);color:#a5b4fc;border:1px solid rgba(99,102,241,.28)}

/* ── Role badge — prominente, colore oro ── */
.role-row{display:flex;align-items:center;gap:8px;margin-bottom:.55rem}
.role-pill{
    font-family:'JetBrains Mono',monospace;
    font-size:.85rem;font-weight:700;
    color:#0d1117;
    background:#fbbf24;
    border-radius:6px;
    padding:3px 10px;
    letter-spacing:.04em;
    text-transform:uppercase;
}
.role-full{font-size:.75rem;color:#8b949e}

/* ── Value row ── */
.value-row{display:flex;align-items:baseline;gap:8px;margin-bottom:.65rem}
.v-icon{font-size:1rem}
.v-amount{font-family:'JetBrains Mono',monospace;font-size:1.3rem;font-weight:700;color:#10b981}
.v-detail{font-size:.71rem;color:#6e7681}

/* ── Dates ── */
.dates-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px}
.date-box{background:#0d1117;border:1px solid #21262d;border-radius:9px;padding:.4rem .6rem}
.date-lbl{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#6e7681;margin-bottom:2px}
.date-val{font-family:'JetBrains Mono',monospace;font-size:.77rem;font-weight:500;color:#e6edf3;line-height:1.3}
.date-time{font-size:.67rem;color:#6e7681}
.insider-row{margin-top:.55rem;font-size:.75rem;color:#8b949e;display:flex;align-items:center;gap:5px}

/* ── Banners ── */
.stale-banner{background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.28);border-radius:10px;padding:.55rem 1rem;font-size:.78rem;color:#fbbf24;margin-bottom:.9rem;text-align:center}
.error-banner{background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.25);border-radius:10px;padding:.55rem 1rem;font-size:.75rem;color:#fca5a5;margin-bottom:.9rem}
.info-banner{background:rgba(56,189,248,.07);border:1px solid rgba(56,189,248,.22);border-radius:10px;padding:.55rem 1rem;font-size:.75rem;color:#7dd3fc;margin-bottom:.9rem;text-align:center}
.empty-state{text-align:center;padding:3rem 1rem;color:#6e7681}
.empty-state .ei{font-size:2.5rem;margin-bottom:.5rem}
.divider{border:none;border-top:1px solid #21262d;margin:.8rem 0}

/* ── Streamlit overrides ── */
.stSlider > div > div > div > div{background:#10b981!important}
div[data-testid="stButton"] button{width:100%!important;background:linear-gradient(135deg,#10b981,#059669)!important;color:#fff!important;border:none!important;border-radius:10px!important;font-weight:700!important;font-size:.9rem!important;padding:.55rem!important}
div[data-testid="stButton"] button:hover{transform:translateY(-1px)!important;box-shadow:0 6px 20px rgba(16,185,129,.3)!important}
div[data-testid="stSelectbox"] label,div[data-testid="stSlider"] label,
div[data-testid="stMultiSelect"] label{font-size:.7rem!important;font-weight:700!important;letter-spacing:.1em!important;text-transform:uppercase!important;color:#6e7681!important}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────
CACHE_FILE = "last_known_data.json"

HEADERS_BROWSER = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

CLEVEL_KW = [
    "chief executive","ceo","chief financial","cfo",
    "chief operating","coo","chairman","cob",
    "general counsel","gc","vice president","vp",
    "president","pres","chief ","officer",
]
EXCLUDE_KW = ["director","10% owner","beneficial owner"]

SECTOR_THEME = {
    "Technology":    ("#818cf8","rgba(99,102,241,.1)","rgba(99,102,241,.28)"),
    "Healthcare":    ("#34d399","rgba(52,211,153,.1)","rgba(52,211,153,.28)"),
    "Financials":    ("#60a5fa","rgba(96,165,250,.1)","rgba(96,165,250,.28)"),
    "Energy":        ("#fb923c","rgba(251,146,60,.1)","rgba(251,146,60,.28)"),
    "Consumer Cyclical": ("#f472b6","rgba(244,114,182,.1)","rgba(244,114,182,.28)"),
    "Consumer Defensive":("#f9a8d4","rgba(249,168,212,.1)","rgba(249,168,212,.28)"),
    "Industrials":   ("#a78bfa","rgba(167,139,250,.1)","rgba(167,139,250,.28)"),
    "Basic Materials":("#4ade80","rgba(74,222,128,.1)","rgba(74,222,128,.28)"),
    "Utilities":     ("#facc15","rgba(250,204,21,.1)","rgba(250,204,21,.28)"),
    "Real Estate":   ("#f87171","rgba(248,113,113,.1)","rgba(248,113,113,.28)"),
    "Communication Services":("#38bdf8","rgba(56,189,248,.1)","rgba(56,189,248,.28)"),
    "Financial Services":("#60a5fa","rgba(96,165,250,.1)","rgba(96,165,250,.28)"),
}

# ── GIORNI LAVORATIVI ─────────────────────────────────────────
def business_days_ago(n: int) -> datetime:
    """N giorni lavorativi fa, escludendo sabato e domenica."""
    date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    counted = 0
    while counted < n:
        date -= timedelta(days=1)
        if date.weekday() < 5:
            counted += 1
    return date

# ── ROLE EXTRACTOR ────────────────────────────────────────────
# Estrae la carica abbreviata dal campo title di OpenInsider.
# I valori sono quelli reali che OpenInsider scrive nel DB SEC.
_ROLE_MAP = [
    ("CEO",        ["chief executive officer","chief executive","ceo"]),
    ("CFO",        ["chief financial officer","chief financial","cfo"]),
    ("COO",        ["chief operating officer","chief operating","coo"]),
    ("CTO",        ["chief technology officer","chief technology","cto"]),
    ("CMO",        ["chief medical officer","chief medical","cmo"]),
    ("CSO",        ["chief scientific officer","chief scientific","cso"]),
    ("CLO",        ["chief legal officer","chief legal","clo"]),
    ("CAO",        ["chief accounting officer","chief accounting","cao"]),
    ("CBO",        ["chief business officer","chief business","cbo"]),
    ("CHRO",       ["chief human resources","chief hr","chro"]),
    ("COB",        ["chairman of the board","chairman","cob"]),
    ("Pres",       ["president"]),
    ("GC",         ["general counsel"]),
    ("EVP",        ["executive vice president","evp"]),
    ("SVP",        ["senior vice president","svp"]),
    ("VP",         ["vice president","vp"]),
    ("Treasurer",  ["treasurer"]),
    ("Secretary",  ["secretary"]),
    ("Officer",    ["officer"]),
]

def extract_role(title: str) -> tuple[str, str]:
    """
    Ritorna (abbreviazione, titolo_completo) dal campo title reale di OpenInsider.
    Esempio: "Chief Executive Officer" → ("CEO", "Chief Executive Officer")
    Non inventa nulla: usa solo ciò che c'è nel campo title.
    """
    if not title or not title.strip():
        return "—", "—"
    tl = title.lower().strip()
    for abbr, keywords in _ROLE_MAP:
        if any(kw in tl for kw in keywords):
            return abbr, title.strip()
    return title.strip()[:8].upper(), title.strip()

# ── HELPERS ───────────────────────────────────────────────────
def is_clevel(title: str) -> bool:
    if not isinstance(title, str) or not title.strip():
        return False
    tl = title.lower()
    if not any(k in tl for k in CLEVEL_KW):
        return False
    if any(k in tl for k in EXCLUDE_KW):
        return any(k in tl for k in [
            "ceo","cfo","coo","cob","president","chairman",
            "general counsel","vice president",
            "chief executive","chief financial","chief operating",
        ])
    return True

def _oi_parse_num(s: str) -> str:
    return re.sub(r"[$,\s+]", "", s.strip())

def clean_num(s) -> float:
    try:   return float(re.sub(r"[^\d.]", "", str(s)) or "0")
    except: return 0.0

def fmt_usd(v: float) -> str:
    if v >= 1_000_000: return f"${v/1_000_000:.2f}M"
    if v >= 1_000:     return f"${v/1_000:.0f}K"
    return f"${v:.0f}"

def sector_style(sector: str) -> tuple:
    for k, v in SECTOR_THEME.items():
        if k.lower() in sector.lower(): return v
    return ("#94a3b8","rgba(148,163,184,.1)","rgba(148,163,184,.28)")

# ── FETCH CON RETRY ───────────────────────────────────────────
def oi_safe_fetch(url: str, retries: int = 3, delay: int = 4):
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS_BROWSER, timeout=20)
            if r.status_code == 200:
                return r
        except Exception:
            pass
        if attempt < retries:
            time.sleep(delay * attempt)
    return None

# ── COLUMN DETECTION ─────────────────────────────────────────
def _detect_columns(header_row) -> dict:
    cols = {}
    for i, th in enumerate(header_row.find_all(["th", "td"])):
        txt = th.get_text(strip=True).lower()
        if "trade" in txt and "date" in txt and "trade_date" not in cols:
            cols["trade_date"] = i
        elif "filing" in txt and "date" in txt and "filing_date" not in cols:
            cols["filing_date"] = i
        elif "ticker" in txt and "ticker" not in cols:
            cols["ticker"] = i
        elif "company" in txt and "company" not in cols:
            cols["company"] = i
        elif "insider" in txt and "insider" not in cols:
            cols["insider"] = i
        elif "title" in txt and "title" not in cols:
            cols["title"] = i
        elif ("trade type" in txt or txt == "type") and "type" not in cols:
            cols["type"] = i
        elif "price" in txt and "price" not in cols:
            cols["price"] = i
        elif "qty" in txt and "qty" not in cols:
            cols["qty"] = i
        elif "value" in txt and "value" not in cols:
            cols["value"] = i
    defaults = {
        "filing_date": 1, "trade_date": 2, "ticker": 3, "company": 4,
        "insider": 5, "title": 6, "type": 7, "price": 8, "qty": 9, "value": 13,
    }
    for k, v in defaults.items():
        if k not in cols:
            cols[k] = v
    return cols

def _find_table(soup):
    for tbl in soup.find_all("table"):
        cls = " ".join(tbl.get("class", []))
        if "tinytable" in cls or "sortable" in cls:
            return tbl
    tables = soup.find_all("table")
    return max(tables, key=lambda t: len(t.find_all("tr")), default=None) if tables else None

# ── PARSER TABELLA ────────────────────────────────────────────
def _parse_table(soup, cutoff: datetime) -> list:
    table = _find_table(soup)
    if not table:
        return []
    all_rows = table.find_all("tr")
    if not all_rows:
        return []
    cols    = _detect_columns(all_rows[0])
    results = []

    for tr in all_rows[1:]:
        tds = tr.find_all("td")
        if len(tds) < 8:
            continue
        try:
            def get(key, default=""):
                idx = cols.get(key, -1)
                if idx < 0 or idx >= len(tds): return default
                return tds[idx].get_text(strip=True)

            ttype     = get("type")
            ttype_key = ttype.split(" ")[0].upper() if ttype else ""
            if ttype_key != "P":
                continue

            trade_raw   = get("trade_date")
            filing_raw  = get("filing_date")
            trade_dt_s  = trade_raw[:10]  if trade_raw  else ""
            filing_dt_s = filing_raw[:10] if filing_raw else ""
            trade_time  = trade_raw[10:].strip()  if len(trade_raw)  > 10 else ""
            filing_time = filing_raw[10:].strip() if len(filing_raw) > 10 else ""

            try:
                if cutoff and datetime.strptime(trade_dt_s, "%Y-%m-%d") < cutoff:
                    continue
            except ValueError:
                continue

            ticker_td = tds[cols.get("ticker", 3)]
            ticker_a  = ticker_td.find("a")
            ticker    = (ticker_a.get_text(strip=True) if ticker_a
                         else ticker_td.get_text(strip=True)).upper().strip()
            ticker    = re.sub(r"[^A-Z.]", "", ticker)
            if not ticker or len(ticker) > 6:
                continue

            company   = tds[cols.get("company", 4)].get_text(strip=True)
            insider_td= tds[cols.get("insider", 5)]
            insider_a = insider_td.find("a")
            insider   = (insider_a.get_text(strip=True) if insider_a
                         else insider_td.get_text(strip=True)).strip()
            title     = get("title")

            if not is_clevel(title):
                continue

            price = clean_num(_oi_parse_num(get("price", "0")))
            qty   = clean_num(_oi_parse_num(get("qty",   "0")))
            val_s = _oi_parse_num(get("value", "0"))
            try:
                value = float(val_s) if val_s else abs(qty) * price
                if value <= 0:
                    value = abs(qty) * price
            except Exception:
                value = abs(qty) * price

            if qty == 0 or price <= 0:
                continue

            # Estrae la carica reale dall'SEC title
            role_abbr, role_full = extract_role(title)

            results.append({
                "ticker":       ticker,
                "company":      company,
                "insider":      insider,
                "title":        title,        # testo originale da OpenInsider/SEC
                "role_abbr":    role_abbr,    # es. "CEO"
                "role_full":    role_full,    # es. "Chief Executive Officer"
                "price":        price,
                "qty":          f"{int(qty):,}",
                "value":        value,
                "trade_date":   trade_dt_s,
                "trade_time":   trade_time,
                "filing_date":  filing_dt_s,
                "filing_time":  filing_time,
            })
        except Exception:
            continue

    return results

# ── URL BUILDER ───────────────────────────────────────────────
def build_url(vl: int, vh: int, days: int = 30) -> str:
    vh_s = str(vh) if vh > 0 else ""
    return (
        f"http://openinsider.com/screener?"
        f"s=&o=&pl=&ph=&ll=&lh="
        f"&fd={days}&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago="
        f"&xp=1&xs=0&xa=0&xd=0&xg=0&xf=0&xm=0&xx=0&xo=0"
        f"&vl={vl}&vh={vh_s}"
        f"&ocl=&och=&sic1=-1&sicl=100&sich=9999"
        f"&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h="
        f"&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1"
        f"&isdirector=0&is10percent=0&isother=0"
        f"&sortcol=0&cnt=200&Action=Submit"
    )

# ── FETCH (cached 5 min) ──────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_trades(vl: int, vh: int) -> tuple:
    url = build_url(vl, vh)
    r   = oi_safe_fetch(url)
    if r is None:
        return [], "OpenInsider non raggiungibile (3 tentativi falliti)"
    soup   = BeautifulSoup(r.text, "html.parser")
    cutoff = datetime.now() - timedelta(days=31)
    return _parse_table(soup, cutoff), ""

# ── YFINANCE (price / exchange / sector) ─────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def enrich(ticker: str) -> dict:
    try:
        import yfinance as yf
        info  = yf.Ticker(ticker).info
        price = (info.get("currentPrice") or info.get("regularMarketPrice")
                 or info.get("previousClose", 0))
        return {
            "price":    round(float(price), 2) if price else 0.0,
            "exchange": (info.get("exchange") or info.get("fullExchangeName") or "—").upper(),
            "sector":   info.get("sector") or info.get("sectorDisp") or "—",
        }
    except:
        return {"price": 0.0, "exchange": "—", "sector": "—"}

# ── DISK CACHE ────────────────────────────────────────────────
def save_disk(trades):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"trades": trades, "at": datetime.utcnow().isoformat()}, f)
    except: pass

def load_disk():
    try:
        with open(CACHE_FILE) as f: d = json.load(f)
        return d.get("trades", []), d.get("at", "")
    except: return [], ""

# ── CARD ──────────────────────────────────────────────────────
def render_card(t: dict, info: dict):
    ticker    = t["ticker"]
    price     = info.get("price", 0.0)
    exchange  = info.get("exchange", "—")
    sector    = info.get("sector", "—")
    sc, sbg, sbd = sector_style(sector)

    price_str  = f"${price:.2f}" if price else "—"
    co         = (t.get("company", "") or "")
    co         = (co[:36] + "…") if len(co) > 36 else co
    role_abbr  = t.get("role_abbr", "—")    # es. "CEO" — dato reale da SEC
    role_full  = t.get("role_full",  "—")   # es. "Chief Executive Officer"
    qty_s      = re.sub(r"[^\d,]", "", t.get("qty", ""))
    tp_s       = f"@ ${t['price']:.2f}" if t.get("price") else ""

    st.markdown(f"""
<div class="card">
  <div class="card-top">
    <div>
      <div class="ticker">{ticker}</div>
      <div class="company-name">{co}</div>
    </div>
    <span class="price-pill">{price_str}</span>
  </div>

  <!-- Carica insider: badge giallo prominente + titolo completo -->
  <div class="role-row">
    <span class="role-pill">{role_abbr}</span>
    <span class="role-full">{role_full}</span>
  </div>

  <!-- Mercato + Settore -->
  <div class="badges">
    <span class="badge b-market">📊 {exchange}</span>
    <span class="badge b-sector" style="color:{sc};background:{sbg};border-color:{sbd};">{sector}</span>
  </div>

  <!-- Valore acquisto -->
  <div class="value-row">
    <span class="v-icon">🟢</span>
    <span class="v-amount">{fmt_usd(t['value'])}</span>
    <span class="v-detail">{qty_s} shares {tp_s}</span>
  </div>

  <!-- Date -->
  <div class="dates-grid">
    <div class="date-box">
      <div class="date-lbl">📅 Trade Date</div>
      <div class="date-val">{t['trade_date']}</div>
      <div class="date-time">{t['trade_time']}</div>
    </div>
    <div class="date-box">
      <div class="date-lbl">🕒 SEC Filing</div>
      <div class="date-val">{t['filing_date']}</div>
      <div class="date-time">{t['filing_time']}</div>
    </div>
  </div>

  <div class="insider-row"><span>👤</span><span>{t['insider']}</span></div>
</div>""", unsafe_allow_html=True)

# ── MAIN ──────────────────────────────────────────────────────
def main():
    st.markdown("""
<div class="app-header">
  <h1>📈 Insider Buy Tracker</h1>
  <div class="sub"><span class="pulse"></span>C-Level purchases · OpenInsider · SEC Form 4</div>
</div>""", unsafe_allow_html=True)

    # ── FILTRI ────────────────────────────────────────────────
    st.markdown('<span class="filter-label">💰 Min Value (K$)</span>', unsafe_allow_html=True)
    vl = st.slider("min_v", 20, 500, 20, 10, label_visibility="collapsed")

    st.markdown('<span class="filter-label">🔝 Max Value (K$) — 0 = no limit</span>', unsafe_allow_html=True)
    vh = st.slider("max_v", 0, 10_000, 1_000, 100, label_visibility="collapsed")

    st.markdown('<span class="filter-label">📅 Giorni lavorativi (da oggi indietro)</span>',
                unsafe_allow_html=True)
    bdays = st.slider("bdays", 1, 7, 7, 1, label_visibility="collapsed")
    cutoff_bday = business_days_ago(bdays)
    st.markdown(
        f'<p style="font-size:.72rem;color:#6e7681;margin:-.3rem 0 .6rem 0;">'
        f'Dal <b style="color:#10b981">{cutoff_bday.strftime("%d %b %Y")}</b> ad oggi '
        f'({bdays} giorno{"" if bdays==1 else "i"} lavorativo{"" if bdays==1 else "i"})</p>',
        unsafe_allow_html=True)

    col_s, col_b = st.columns([3, 1])
    with col_s:
        sort_by = st.selectbox("Sort by",
            ["Value ↓", "Filing Date ↓", "Trade Date ↓"], label_visibility="visible")
    with col_b:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.session_state.pop("show_count", None)
            st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-banner">🔗 Fonte: <b>OpenInsider</b> · SEC Form 4 · C-Level only</div>',
        unsafe_allow_html=True)

    # ── FETCH ─────────────────────────────────────────────────
    prog = st.progress(0, text="⏳ Caricamento da OpenInsider…")
    trades, err = fetch_trades(vl, vh)
    prog.progress(100, text="✅ Fatto")
    prog.empty()

    using_stale, stale_ts = False, ""
    if trades:
        save_disk(trades)
    else:
        trades, stale_ts = load_disk()
        using_stale = bool(trades)

    if err:
        st.markdown(f'<div class="error-banner">⚠️ {err}</div>', unsafe_allow_html=True)
    if using_stale:
        st.markdown(
            f'<div class="stale-banner">📦 Dati salvati ({stale_ts[:16]} UTC)</div>',
            unsafe_allow_html=True)

    if not trades:
        st.markdown("""
<div class="empty-state"><div class="ei">🔍</div>
<p>Nessun acquisto C-Level trovato.<br>Prova a ridurre il valore minimo o premi Refresh.</p>
</div>""", unsafe_allow_html=True)
        return

    # ── FILTRO GIORNI LAVORATIVI ──────────────────────────────
    cutoff_str = cutoff_bday.strftime("%Y-%m-%d")
    trades = [t for t in trades if t.get("trade_date", "") >= cutoff_str]

    if not trades:
        st.markdown(f"""
<div class="empty-state"><div class="ei">📅</div>
<p>Nessun acquisto negli ultimi <b>{bdays}</b> giorni lavorativi.<br>
Prova ad aumentare i giorni o abbassare il valore minimo.</p>
</div>""", unsafe_allow_html=True)
        return

    # ── ENRICHMENT (per settore) ─────────────────────────────
    # Arricchisce tutti i trade con settore reale da yfinance (cached)
    enriched_map: dict[str, dict] = {}
    for t in trades:
        tk = t["ticker"]
        if tk not in enriched_map:
            enriched_map[tk] = enrich(tk)

    # ── FILTRO SETTORE (popolato con dati reali da yfinance) ──
    all_sectors = sorted({
        enriched_map[t["ticker"]].get("sector", "—")
        for t in trades
        if enriched_map[t["ticker"]].get("sector", "—") != "—"
    })

    sector_filter: list = []
    if all_sectors:
        st.markdown('<span class="filter-label">🏭 Filtra per Settore</span>',
                    unsafe_allow_html=True)
        sector_filter = st.multiselect(
            "Settore",
            options=all_sectors,
            default=[],
            placeholder="Tutti i settori (lascia vuoto)",
            label_visibility="collapsed",
        )

    # Applica filtro settore
    if sector_filter:
        trades = [
            t for t in trades
            if enriched_map[t["ticker"]].get("sector", "—") in sector_filter
        ]

    if not trades:
        st.markdown("""
<div class="empty-state"><div class="ei">🏭</div>
<p>Nessun acquisto per i settori selezionati.<br>
Deseleziona qualche settore o abbassa il valore minimo.</p>
</div>""", unsafe_allow_html=True)
        return

    # ── SORT ─────────────────────────────────────────────────
    key_fn = {
        "Value ↓":       lambda x: x["value"],
        "Filing Date ↓": lambda x: x["filing_date"],
        "Trade Date ↓":  lambda x: x["trade_date"],
    }
    trades = sorted(trades, key=key_fn[sort_by], reverse=True)

    # ── STATS ─────────────────────────────────────────────────
    total = sum(t["value"] for t in trades)
    ntick = len({t["ticker"] for t in trades})
    st.markdown(f"""
<div class="stats-bar">
  <div class="stat"><div class="stat-n">{len(trades)}</div><div class="stat-l">Trades</div></div>
  <div class="stat"><div class="stat-n">{ntick}</div><div class="stat-l">Tickers</div></div>
  <div class="stat"><div class="stat-n">{fmt_usd(total)}</div><div class="stat-l">Totale</div></div>
</div>""", unsafe_allow_html=True)

    # ── CARDS ─────────────────────────────────────────────────
    BATCH = 12
    if "show_count" not in st.session_state:
        st.session_state.show_count = BATCH

    for trade in trades[:st.session_state.show_count]:
        render_card(trade, enriched_map[trade["ticker"]])

    remaining = len(trades) - st.session_state.show_count
    if remaining > 0:
        if st.button(f"⬇️  Carica altri {min(BATCH, remaining)}  ({remaining} rimanenti)"):
            st.session_state.show_count += BATCH
            st.rerun()

    st.markdown(
        f'<p style="text-align:center;color:#6e7681;font-size:.68rem;margin-top:1.4rem;">'
        f'Fonte: openinsider.com · Cache 5 min · '
        f'{datetime.utcnow().strftime("%d %b %Y %H:%M")} UTC</p>',
        unsafe_allow_html=True)

if __name__ == "__main__":
    main()
