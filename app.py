"""
Insider Buy Tracker  –  v3
Data source: SEC EDGAR API (efts.sec.gov + data.sec.gov)
Fully accessible from Streamlit Community Cloud.
"""

import streamlit as st
import requests
import re
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from xml.etree import ElementTree as ET

# ──────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Insider Buy Tracker",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────
# STYLES
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0.8rem 0.9rem 4rem !important; max-width: 540px !important; margin: auto; }

.app-header { text-align: center; padding: 1.4rem 0 0.8rem; }
.app-header h1 { font-size: 1.75rem; font-weight: 800; letter-spacing: -0.6px; color: #fff; margin: 0; }
.app-header .sub { font-size: 0.78rem; color: #6e7681; margin: 0.2rem 0 0;
    display: flex; align-items: center; justify-content: center; gap: 6px; }
.pulse { display: inline-block; width: 7px; height: 7px; background: #10b981;
    border-radius: 50%; animation: blink 2s ease-in-out infinite; }
@keyframes blink {
    0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,.6);opacity:1}
    50%{box-shadow:0 0 0 5px rgba(16,185,129,0);opacity:.6}
}
.filter-label { font-size:.7rem; font-weight:700; letter-spacing:.1em;
    text-transform:uppercase; color:#6e7681; margin-bottom:.2rem; display:block; }
.stats-bar { display:flex; justify-content:space-around; background:#161b22;
    border:1px solid #21262d; border-radius:12px; padding:.75rem .5rem; margin-bottom:1rem; }
.stat { flex:1; text-align:center; }
.stat-n { font-family:'JetBrains Mono',monospace; font-size:1.1rem; font-weight:700; color:#10b981; }
.stat-l { font-size:.62rem; color:#6e7681; text-transform:uppercase; letter-spacing:.07em; }
.card { background:#161b22; border:1px solid #21262d; border-radius:14px;
    padding:1rem 1.1rem .9rem; margin-bottom:.8rem; position:relative;
    overflow:hidden; transition:border-color .18s; }
.card::before { content:''; position:absolute; left:0; top:0; bottom:0; width:4px;
    background:linear-gradient(180deg,#10b981,#059669); border-radius:14px 0 0 14px; }
.card:hover { border-color:rgba(16,185,129,.5); }
.card-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:.55rem; }
.ticker { font-family:'JetBrains Mono',monospace; font-size:1.6rem; font-weight:700;
    color:#fff; letter-spacing:-.5px; line-height:1; }
.company-name { font-size:.72rem; color:#6e7681; margin-top:1px; }
.price-pill { font-family:'JetBrains Mono',monospace; font-size:1rem; font-weight:600;
    color:#10b981; background:rgba(16,185,129,.1); border:1px solid rgba(16,185,129,.22);
    border-radius:8px; padding:3px 11px; white-space:nowrap; }
.badges { display:flex; flex-wrap:wrap; gap:5px; margin-bottom:.65rem; }
.badge { font-size:.68rem; font-weight:600; padding:2px 8px; border-radius:20px;
    white-space:nowrap; letter-spacing:.03em; }
.b-market { background:#1c2128; color:#8b949e; border:1px solid #30363d; }
.b-sector { background:rgba(99,102,241,.1); color:#a5b4fc; border:1px solid rgba(99,102,241,.28); }
.b-title  { background:rgba(251,191,36,.08); color:#fbbf24; border:1px solid rgba(251,191,36,.25); }
.value-row { display:flex; align-items:baseline; gap:8px; margin-bottom:.65rem; }
.v-icon { font-size:1rem; }
.v-amount { font-family:'JetBrains Mono',monospace; font-size:1.3rem; font-weight:700; color:#10b981; }
.v-detail { font-size:.71rem; color:#6e7681; }
.dates-grid { display:grid; grid-template-columns:1fr 1fr; gap:7px; }
.date-box { background:#0d1117; border:1px solid #21262d; border-radius:9px; padding:.4rem .6rem; }
.date-lbl { font-size:.62rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em;
    color:#6e7681; margin-bottom:2px; }
.date-val { font-family:'JetBrains Mono',monospace; font-size:.77rem; font-weight:500;
    color:#e6edf3; line-height:1.3; }
.date-time { font-size:.67rem; color:#6e7681; }
.insider-row { margin-top:.55rem; font-size:.75rem; color:#8b949e;
    display:flex; align-items:center; gap:5px; }
.stale-banner { background:rgba(245,158,11,.08); border:1px solid rgba(245,158,11,.28);
    border-radius:10px; padding:.55rem 1rem; font-size:.78rem; color:#fbbf24;
    margin-bottom:.9rem; text-align:center; }
.error-banner { background:rgba(239,68,68,.07); border:1px solid rgba(239,68,68,.25);
    border-radius:10px; padding:.55rem 1rem; font-size:.75rem; color:#fca5a5;
    margin-bottom:.9rem; }
.info-banner { background:rgba(56,189,248,.07); border:1px solid rgba(56,189,248,.22);
    border-radius:10px; padding:.55rem 1rem; font-size:.75rem; color:#7dd3fc;
    margin-bottom:.9rem; text-align:center; }
.empty-state { text-align:center; padding:3rem 1rem; color:#6e7681; }
.empty-state .ei { font-size:2.5rem; margin-bottom:.5rem; }
.divider { border:none; border-top:1px solid #21262d; margin:.8rem 0; }
.stSlider > div > div > div > div { background:#10b981 !important; }
div[data-testid="stButton"] button {
    width:100% !important; background:linear-gradient(135deg,#10b981,#059669) !important;
    color:#fff !important; border:none !important; border-radius:10px !important;
    font-weight:700 !important; font-size:.9rem !important; padding:.55rem !important; }
div[data-testid="stButton"] button:hover {
    transform:translateY(-1px) !important; box-shadow:0 6px 20px rgba(16,185,129,.3) !important; }
div[data-testid="stSelectbox"] label, div[data-testid="stSlider"] label {
    font-size:.7rem !important; font-weight:700 !important; letter-spacing:.1em !important;
    text-transform:uppercase !important; color:#6e7681 !important; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────
CACHE_FILE = "last_known_data.json"

# SEC requires a descriptive User-Agent
SEC_HEADERS = {
    "User-Agent": "InsiderBuyTracker/3.0 (educational; contact@example.com)",
    "Accept":     "application/json, text/html, */*",
}

C_LEVEL_KW = [
    "chief executive", "ceo",
    "chief financial", "cfo",
    "chief operating", "coo",
    "chairman", "cob",
    "general counsel", "gc",
    "vice president", "vp",
    "president", "pres",
    "chief ", "officer",       # generic "Officer" flag
]
EXCLUDE_KW = ["director", "10% owner", "beneficial owner"]

SECTOR_THEME = {
    "Technology":    ("#818cf8", "rgba(99,102,241,.1)",  "rgba(99,102,241,.28)"),
    "Healthcare":    ("#34d399", "rgba(52,211,153,.1)",  "rgba(52,211,153,.28)"),
    "Financials":    ("#60a5fa", "rgba(96,165,250,.1)",  "rgba(96,165,250,.28)"),
    "Energy":        ("#fb923c", "rgba(251,146,60,.1)",  "rgba(251,146,60,.28)"),
    "Consumer":      ("#f472b6", "rgba(244,114,182,.1)", "rgba(244,114,182,.28)"),
    "Industrials":   ("#a78bfa", "rgba(167,139,250,.1)", "rgba(167,139,250,.28)"),
    "Materials":     ("#4ade80", "rgba(74,222,128,.1)",  "rgba(74,222,128,.28)"),
    "Utilities":     ("#facc15", "rgba(250,204,21,.1)",  "rgba(250,204,21,.28)"),
    "Real Estate":   ("#f87171", "rgba(248,113,113,.1)", "rgba(248,113,113,.28)"),
    "Communication": ("#38bdf8", "rgba(56,189,248,.1)",  "rgba(56,189,248,.28)"),
}

# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────
def is_clevel(title: str) -> bool:
    if not isinstance(title, str) or not title.strip():
        return False
    tl = title.lower()
    has_pos = any(k in tl for k in C_LEVEL_KW)
    if not has_pos:
        return False
    has_neg = any(k in tl for k in EXCLUDE_KW)
    if has_neg:
        # Keep only if a strong positive keyword is also present
        return any(k in tl for k in ["ceo", "cfo", "coo", "cob", "president", "chairman",
                                      "general counsel", "vice president", "chief executive",
                                      "chief financial", "chief operating"])
    return True

def clean_num(s) -> float:
    try:
        return float(re.sub(r"[^\d.]", "", str(s)) or "0")
    except ValueError:
        return 0.0

def fmt_usd(v: float) -> str:
    if v >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:.0f}"

def sector_style(sector: str) -> tuple:
    for k, v in SECTOR_THEME.items():
        if k.lower() in sector.lower():
            return v
    return ("#94a3b8", "rgba(148,163,184,.1)", "rgba(148,163,184,.28)")

# ──────────────────────────────────────────────────────────────
# SEC EDGAR – Step 1: Search for recent Form 4 filings
# Uses: https://efts.sec.gov/LATEST/search-index
# ──────────────────────────────────────────────────────────────
def search_form4_filings(days: int = 30, max_hits: int = 120) -> list:
    end_dt   = datetime.utcnow()
    start_dt = end_dt - timedelta(days=days)

    results = []
    for offset in range(0, max_hits, 40):
        url = (
            "https://efts.sec.gov/LATEST/search-index?"
            "forms=4"
            f"&dateRange=custom"
            f"&startdt={start_dt.strftime('%Y-%m-%d')}"
            f"&enddt={end_dt.strftime('%Y-%m-%d')}"
            f"&from={offset}"
        )
        try:
            r = requests.get(url, headers=SEC_HEADERS, timeout=15)
            r.raise_for_status()
            data  = r.json()
            hits  = data.get("hits", {}).get("hits", [])
            results.extend(hits)
            if len(hits) < 40:
                break
        except Exception:
            break
    return results

# ──────────────────────────────────────────────────────────────
# SEC EDGAR – Step 2: Fetch individual Form 4 XML
# Constructs URL from accession number (no extra index request needed
# for most modern filings that follow SEC's naming convention).
# ──────────────────────────────────────────────────────────────
def fetch_form4_xml(accession: str) -> bytes | None:
    """
    Fetch the primary Form 4 XML document.
    Accession format: 0001234567-26-000123
    → CIK = 1234567 (strip leading zeros)
    → Folder = 000123456726000123
    → Try common XML filenames; fallback to directory listing.
    """
    parts    = accession.split("-")
    cik      = str(int(parts[0]))             # strip leading zeros
    acc_flat = accession.replace("-", "")     # 000123456726000123
    base_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_flat}/"

    # Many filers use EDGAR Online Filing System (Workiva / WestFax):
    # the primary Form 4 XML is typically named after the accession number
    candidates = [
        f"{acc_flat}.xml",
        "form4.xml",
        "xslForm4X01.xml",
        "primary_doc.xml",
    ]

    # Try candidates first (fast)
    for fname in candidates:
        try:
            r = requests.get(base_url + fname, headers=SEC_HEADERS, timeout=8)
            if r.status_code == 200 and b"<ownershipDocument" in r.content:
                return r.content
        except Exception:
            continue

    # Fallback: scrape the directory listing for any .xml file
    try:
        r = requests.get(base_url, headers=SEC_HEADERS, timeout=8)
        if r.status_code != 200:
            return None
        # Find links to XML files (not XSD)
        xml_files = [
            m for m in re.findall(r'href="([^"]+\.xml)"', r.text)
            if not m.lower().endswith(".xsd")
        ]
        if not xml_files:
            return None
        fname = xml_files[0].split("/")[-1]
        r2 = requests.get(base_url + fname, headers=SEC_HEADERS, timeout=8)
        if r2.status_code == 200:
            return r2.content
    except Exception:
        pass

    return None

# ──────────────────────────────────────────────────────────────
# SEC EDGAR – Step 3: Parse Form 4 XML
# ──────────────────────────────────────────────────────────────
def parse_form4(xml_bytes: bytes, file_date: str) -> list:
    """
    Returns list of purchase trade dicts (transactionCode = P).
    """
    try:
        # Strip namespace declarations that confuse ElementTree
        text = xml_bytes.decode("utf-8", errors="ignore")
        text = re.sub(r'\s+xmlns[^=]*="[^"]*"', "", text)
        root = ET.fromstring(text)
    except ET.ParseError:
        return []

    # ── Reporting owner role ───────────────────────────────────
    rel    = root.find(".//reportingOwnerRelationship")
    title  = ""
    if rel is not None:
        title = rel.findtext("officerTitle") or rel.findtext("officerTitle") or ""
        is_off = rel.findtext("isOfficer") or "0"
        is_dir = rel.findtext("isDirector") or "0"
        is_ten = rel.findtext("isTenPercentOwner") or "0"
    else:
        is_off = is_dir = is_ten = "0"

    # ── Skip non-C-level ──────────────────────────────────────
    if not is_clevel(title) and not (is_off == "1" and title):
        return []
    if not is_clevel(title):
        return []

    # ── Issuer info ────────────────────────────────────────────
    ticker  = (root.findtext(".//issuer/issuerTradingSymbol") or "").strip().upper()
    company = (root.findtext(".//issuer/issuerName")          or "").strip()
    insider = (root.findtext(".//reportingOwner/reportingOwnerId/rptOwnerName") or "").strip()

    if not ticker or not re.match(r"^[A-Z.]{1,6}$", ticker):
        return []

    # ── Non-derivative transactions (stock purchases) ──────────
    trades = []
    for tx in root.findall(".//nonDerivativeTransaction"):
        code = tx.findtext(".//transactionCode") or ""
        if code != "P":
            continue

        shares     = clean_num(tx.findtext(".//transactionShares/value")         or "0")
        price_per  = clean_num(tx.findtext(".//transactionPricePerShare/value")   or "0")
        trade_date = tx.findtext(".//transactionDate/value") or ""
        value      = shares * price_per

        if value <= 0 or shares <= 0:
            continue

        trades.append({
            "ticker":       ticker,
            "company":      company,
            "insider":      insider,
            "title":        title,
            "price":        price_per,
            "qty":          f"{int(shares):,}",
            "value":        value,
            "trade_date":   trade_date,
            "trade_time":   "",
            "filing_date":  file_date,
            "filing_time":  "",
        })

    return trades

# ──────────────────────────────────────────────────────────────
# MAIN FETCH (cached 5 min)
# ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_trades(vl_k: int, vh_k: int) -> tuple:
    """
    Returns (list_of_trades, error_string)
    vl_k / vh_k are min/max values in K$ (vh_k=0 means no limit)
    """
    # Step 1 – search index
    hits = search_form4_filings(days=30, max_hits=120)
    if not hits:
        return [], "Could not reach SEC EDGAR search API"

    # Step 2+3 – parallel fetch + parse
    def process(hit):
        try:
            accession = hit.get("_id", "")
            src       = hit.get("_source", {})
            file_date = src.get("file_date", "")
            xml_bytes = fetch_form4_xml(accession)
            if xml_bytes is None:
                return []
            return parse_form4(xml_bytes, file_date)
        except Exception:
            return []

    all_trades: list = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(process, h): h for h in hits}
        for fut in as_completed(futures):
            try:
                all_trades.extend(fut.result())
            except Exception:
                pass

    # Step 4 – value filter
    min_v = vl_k * 1_000
    max_v = vh_k * 1_000 if vh_k > 0 else float("inf")
    filtered = [t for t in all_trades if min_v <= t["value"] <= max_v]

    return filtered, ""

# ──────────────────────────────────────────────────────────────
# YFINANCE ENRICHMENT
# ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def enrich(ticker: str) -> dict:
    try:
        import yfinance as yf
        info  = yf.Ticker(ticker).info
        price = (info.get("currentPrice")
                 or info.get("regularMarketPrice")
                 or info.get("previousClose", 0))
        return {
            "price":    round(float(price), 2) if price else 0.0,
            "exchange": (info.get("exchange") or info.get("fullExchangeName") or "—").upper(),
            "sector":   info.get("sector") or info.get("sectorDisp") or "—",
        }
    except Exception:
        return {"price": 0.0, "exchange": "—", "sector": "—"}

# ──────────────────────────────────────────────────────────────
# DISK CACHE (offline fallback)
# ──────────────────────────────────────────────────────────────
def save_disk(trades: list) -> None:
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"trades": trades, "at": datetime.utcnow().isoformat()}, f)
    except Exception:
        pass

def load_disk() -> tuple:
    try:
        with open(CACHE_FILE) as f:
            d = json.load(f)
        return d.get("trades", []), d.get("at", "")
    except Exception:
        return [], ""

# ──────────────────────────────────────────────────────────────
# CARD RENDERER
# ──────────────────────────────────────────────────────────────
def render_card(t: dict, info: dict) -> None:
    ticker   = t["ticker"]
    price    = info.get("price", 0.0)
    exchange = info.get("exchange", "—")
    sector   = info.get("sector", "—")
    sc, sbg, sbd = sector_style(sector)

    price_str = f"${price:.2f}" if price else "—"
    company   = t.get("company", "") or ""
    company   = (company[:36] + "…") if len(company) > 36 else company
    title_str = (t.get("title") or "")[:32]
    qty_str   = re.sub(r"[^\d,]", "", t.get("qty", ""))
    tp_str    = f"@ ${t['price']:.2f}" if t.get("price") else ""

    st.markdown(f"""
<div class="card">
  <div class="card-top">
    <div>
      <div class="ticker">{ticker}</div>
      <div class="company-name">{company}</div>
    </div>
    <span class="price-pill">{price_str}</span>
  </div>
  <div class="badges">
    <span class="badge b-market">📊 {exchange}</span>
    <span class="badge b-sector" style="color:{sc};background:{sbg};border-color:{sbd};">{sector}</span>
    <span class="badge b-title">👤 {title_str}</span>
  </div>
  <div class="value-row">
    <span class="v-icon">🟢</span>
    <span class="v-amount">{fmt_usd(t['value'])}</span>
    <span class="v-detail">{qty_str} shares {tp_str}</span>
  </div>
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
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────
def main():
    st.markdown("""
<div class="app-header">
  <h1>📈 Insider Buy Tracker</h1>
  <div class="sub"><span class="pulse"></span>C-Level purchases · SEC EDGAR · Form 4</div>
</div>
""", unsafe_allow_html=True)

    # ── Filters ──────────────────────────────────────────────
    st.markdown('<span class="filter-label">💰 Min Value (K$)</span>', unsafe_allow_html=True)
    vl = st.slider("min_v", 20, 500, 20, 10, label_visibility="collapsed")

    st.markdown('<span class="filter-label">🔝 Max Value (K$) — 0 = no limit</span>', unsafe_allow_html=True)
    vh = st.slider("max_v", 0, 10_000, 1_000, 100, label_visibility="collapsed")

    col_s, col_b = st.columns([3, 1])
    with col_s:
        sort_by = st.selectbox("Sort by", ["Value ↓", "Filing Date ↓", "Trade Date ↓"],
                               label_visibility="visible")
    with col_b:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.session_state.pop("show_count", None)
            st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="info-banner">🔗 Data source: <b>SEC EDGAR</b> — direct Form 4 XML filings</div>',
                unsafe_allow_html=True)

    # ── Fetch ────────────────────────────────────────────────
    with st.spinner("⏳ Fetching Form 4 filings from SEC EDGAR… (first load ~20s, then cached 5 min)"):
        trades, err_msg = fetch_trades(vl, vh)

    using_stale, stale_ts = False, ""

    if not trades and not err_msg:
        trades, stale_ts = load_disk()
        using_stale = bool(trades)
    elif trades:
        save_disk(trades)
    elif err_msg:
        trades, stale_ts = load_disk()
        using_stale = bool(trades)

    if err_msg:
        st.markdown(f'<div class="error-banner">⚠️ {err_msg[:160]}</div>', unsafe_allow_html=True)
    if using_stale:
        st.markdown(f'<div class="stale-banner">📦 Cached data ({stale_ts[:16]} UTC)</div>',
                    unsafe_allow_html=True)

    if not trades:
        st.markdown("""
<div class="empty-state">
  <div class="ei">🔍</div>
  <p>No C-Level purchases found for the current filters.<br>
  Try lowering the minimum value or tapping Refresh.</p>
</div>""", unsafe_allow_html=True)
        return

    # ── Sort ────────────────────────────────────────────────
    key_fn = {
        "Value ↓":       lambda x: x["value"],
        "Filing Date ↓": lambda x: x["filing_date"],
        "Trade Date ↓":  lambda x: x["trade_date"],
    }
    trades = sorted(trades, key=key_fn[sort_by], reverse=True)

    # ── Stats ───────────────────────────────────────────────
    total = sum(t["value"] for t in trades)
    ntick = len({t["ticker"] for t in trades})
    st.markdown(f"""
<div class="stats-bar">
  <div class="stat"><div class="stat-n">{len(trades)}</div><div class="stat-l">Trades</div></div>
  <div class="stat"><div class="stat-n">{ntick}</div><div class="stat-l">Tickers</div></div>
  <div class="stat"><div class="stat-n">{fmt_usd(total)}</div><div class="stat-l">Total</div></div>
</div>""", unsafe_allow_html=True)

    # ── Paginated cards ─────────────────────────────────────
    BATCH = 12
    if "show_count" not in st.session_state:
        st.session_state.show_count = BATCH

    for trade in trades[: st.session_state.show_count]:
        render_card(trade, enrich(trade["ticker"]))

    remaining = len(trades) - st.session_state.show_count
    if remaining > 0:
        if st.button(f"⬇️  Load {min(BATCH, remaining)} more  ({remaining} remaining)"):
            st.session_state.show_count += BATCH
            st.rerun()

    st.markdown(
        f'<p style="text-align:center;color:#6e7681;font-size:.68rem;margin-top:1.4rem;">'
        f'Source: SEC EDGAR (efts.sec.gov) · Cache 5 min · '
        f'{datetime.utcnow().strftime("%d %b %Y %H:%M")} UTC</p>',
        unsafe_allow_html=True)


if __name__ == "__main__":
    main()
