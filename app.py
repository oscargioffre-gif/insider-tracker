import streamlit as st
import pandas as pd
import requests
import json
import re
from datetime import datetime

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Insider Buy Tracker",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# GLOBAL STYLES  (mobile-first, emerald palette)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 0.8rem 0.9rem 4rem 0.9rem !important;
    max-width: 540px !important;
    margin: auto;
}

/* ── Header ── */
.app-header { text-align: center; padding: 1.4rem 0 0.8rem 0; }
.app-header h1 {
    font-size: 1.75rem; font-weight: 800;
    letter-spacing: -0.6px; color: #fff; margin: 0;
}
.app-header .sub {
    font-size: 0.78rem; color: #6e7681; margin: 0.2rem 0 0;
    display: flex; align-items: center; justify-content: center; gap: 6px;
}
.pulse {
    display: inline-block; width: 7px; height: 7px;
    background: #10b981; border-radius: 50%;
    animation: blink 2s ease-in-out infinite;
}
@keyframes blink {
    0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,.6); opacity:1}
    50%{box-shadow:0 0 0 5px rgba(16,185,129,0); opacity:.6}
}

/* ── Filter bar ── */
.filter-label {
    font-size: 0.7rem; font-weight: 700;
    letter-spacing: .1em; text-transform: uppercase;
    color: #6e7681; margin-bottom: 0.2rem; display: block;
}

/* ── Stats bar ── */
.stats-bar {
    display: flex; justify-content: space-around;
    background: #161b22; border: 1px solid #21262d;
    border-radius: 12px; padding: 0.75rem 0.5rem;
    margin-bottom: 1rem;
}
.stat { flex: 1; text-align: center; }
.stat-n {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.1rem; font-weight: 700; color: #10b981;
}
.stat-l {
    font-size: 0.62rem; color: #6e7681;
    text-transform: uppercase; letter-spacing: .07em;
}

/* ── Card ── */
.card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 14px;
    padding: 1rem 1.1rem 0.9rem;
    margin-bottom: 0.8rem;
    position: relative;
    overflow: hidden;
    transition: border-color .18s;
}
.card::before {
    content: '';
    position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
    background: linear-gradient(180deg, #10b981 0%, #059669 100%);
    border-radius: 14px 0 0 14px;
}
.card:hover { border-color: rgba(16,185,129,.5); }

/* top row: ticker + price */
.card-top {
    display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 0.55rem;
}
.ticker {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem; font-weight: 700; color: #fff;
    letter-spacing: -0.5px; line-height: 1;
}
.company-name { font-size: 0.72rem; color: #6e7681; margin-top: 1px; }
.price-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem; font-weight: 600; color: #10b981;
    background: rgba(16,185,129,.1);
    border: 1px solid rgba(16,185,129,.22);
    border-radius: 8px; padding: 3px 11px;
    white-space: nowrap;
}

/* badges row */
.badges { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 0.65rem; }
.badge {
    font-size: 0.68rem; font-weight: 600;
    padding: 2px 8px; border-radius: 20px;
    white-space: nowrap; letter-spacing: .03em;
}
.b-market { background:#1c2128; color:#8b949e; border:1px solid #30363d; }
.b-sector { background:rgba(99,102,241,.1); color:#a5b4fc; border:1px solid rgba(99,102,241,.28); }
.b-title  { background:rgba(251,191,36,.08); color:#fbbf24; border:1px solid rgba(251,191,36,.25); }

/* value row */
.value-row {
    display: flex; align-items: baseline; gap: 8px; margin-bottom: 0.65rem;
}
.v-icon { font-size: 1rem; }
.v-amount {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.3rem; font-weight: 700; color: #10b981;
}
.v-detail { font-size: 0.71rem; color: #6e7681; }

/* dates grid */
.dates-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }
.date-box {
    background: #0d1117; border: 1px solid #21262d;
    border-radius: 9px; padding: 0.4rem 0.6rem;
}
.date-lbl {
    font-size: 0.62rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .08em;
    color: #6e7681; margin-bottom: 2px;
}
.date-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.77rem; font-weight: 500; color: #e6edf3; line-height: 1.3;
}
.date-time { font-size: 0.67rem; color: #6e7681; }

/* insider footer */
.insider-row {
    margin-top: 0.55rem; font-size: 0.75rem; color: #8b949e;
    display: flex; align-items: center; gap: 5px;
}

/* ── Banners ── */
.stale-banner {
    background: rgba(245,158,11,.08); border: 1px solid rgba(245,158,11,.28);
    border-radius: 10px; padding: 0.55rem 1rem;
    font-size: 0.78rem; color: #fbbf24;
    margin-bottom: 0.9rem; text-align: center;
}
.error-banner {
    background: rgba(239,68,68,.07); border: 1px solid rgba(239,68,68,.25);
    border-radius: 10px; padding: 0.55rem 1rem;
    font-size: 0.75rem; color: #fca5a5; margin-bottom: 0.9rem;
}
.empty-state { text-align: center; padding: 3rem 1rem; color: #6e7681; }
.empty-state .ei { font-size: 2.5rem; margin-bottom: .5rem; }

/* ── Divider ── */
.divider { border: none; border-top: 1px solid #21262d; margin: 0.8rem 0; }

/* ── Streamlit overrides ── */
.stSlider > div > div > div > div { background: #10b981 !important; }
div[data-testid="stButton"] button {
    width: 100% !important;
    background: linear-gradient(135deg,#10b981,#059669) !important;
    color: #fff !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    font-size: 0.9rem !important; padding: 0.55rem !important;
}
div[data-testid="stButton"] button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(16,185,129,.3) !important;
}
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label {
    font-size: 0.7rem !important; font-weight: 700 !important;
    letter-spacing: .1em !important; text-transform: uppercase !important;
    color: #6e7681 !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
CACHE_FILE = "last_known_data.json"

# C-Level keywords to match against OpenInsider "Title" column
CLEVEL_KW = [
    "ceo", "cfo", "coo", "cob", "gc", "vp", "pres",
    "chief executive", "chief financial", "chief operating",
    "chairman", "general counsel", "vice president", "president",
    "officer",   # covers the generic "Officer" tag OpenInsider uses
]
REJECT_IF_ONLY = ["10% owner", "director"]   # reject unless a C-level kw is ALSO present

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

# ─────────────────────────────────────────────
# URL BUILDER
# Exact parameter set visible in the screenshot URL + form checkboxes:
#   fd=30  → filing date last 30 days
#   td=30  → trade  date last 30 days
#   xp=1   → P-Purchase ONLY
#   xs=xa=xd=xg=xf=xm=xx=xo=0  → all other tx types OFF
#   vl / vh → value range in K$
#   isofficer/iscob/isceo/ispres/iscoo/iscfo/isgc/isvp = 1
#   isdirector / is10percent / isother = 0   (unchecked in screenshot)
# ─────────────────────────────────────────────
def build_url(vl: int, vh: int) -> str:
    vh_str = str(vh) if vh > 0 else ""
    return (
        "https://openinsider.com/screener?"
        "s=&o=&pl=&ph=&ll=&lh="
        f"&fd=30&fdr=&td=30&tdr=&fdlyl=&fdlyh=&daysago="
        # Transaction type: P-Purchase only
        "&xp=1&xs=0&xa=0&xd=0&xg=0&xf=0&xm=0&xx=0&xo=0"
        # Value range
        f"&vl={vl}&vh={vh_str}"
        "&ocl=&och="
        # Industry: all sectors except Funds (default)
        "&sic1=-1&sicl=100&sich=9999"
        "&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h="
        # Insider title checkboxes (matching screenshot)
        "&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1"
        "&isdirector=0&is10percent=0&isother=0"
        # Sort by Filing Date, max 200 results
        "&sortcol=0&cnt=200&Action=Submit"
    )

# ─────────────────────────────────────────────
# SCRAPER  (TTL = 5 min)
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_raw(vl: int, vh: int) -> tuple:
    """Returns (DataFrame | None, error_str)"""
    url = build_url(vl, vh)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 "
            "Mobile/15E148 Safari/604.1"
        ),
        "Accept":          "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         "https://openinsider.com/",
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        tables = pd.read_html(r.text, flavor="bs4")
        if not tables:
            return None, "No HTML tables found"
        df = max(tables, key=len)
        return df, ""
    except Exception as exc:
        return None, str(exc)

# ─────────────────────────────────────────────
# COLUMN DETECTION
# Real OpenInsider table columns (verified from live HTML):
#   X | Filing Date | Trade Date | Ticker | Company Name |
#   Insider Name | Title | Trade Type | Price | Qty | Owned |
#   ΔOwn | Value | ...
# ─────────────────────────────────────────────
_COL_HINTS = {
    "filing_date": ["filing date", "filing"],
    "trade_date":  ["trade date"],
    "ticker":      ["ticker"],
    "company":     ["company name", "company"],
    "insider":     ["insider name", "insider"],
    "title":       ["title"],
    "type":        ["trade type", "type"],
    "price":       ["price"],
    "qty":         ["qty", "shares"],
    "value":       ["value"],
}
_POS_FALLBACK = {
    # key: column index in OpenInsider's 14-column table
    "filing_date": 1,
    "trade_date":  2,
    "ticker":      3,
    "company":     4,
    "insider":     5,
    "title":       6,
    "type":        7,
    "price":       8,
    "qty":         9,
    "value":       13,
}

def build_col_map(columns: list) -> dict:
    col_map = {}
    for key, hints in _COL_HINTS.items():
        for col in columns:
            cl = str(col).lower().strip()
            if any(h in cl for h in hints):
                col_map[key] = col
                break
    # Fill missing with positional fallback
    for key, idx in _POS_FALLBACK.items():
        if key not in col_map and idx < len(columns):
            col_map[key] = columns[idx]
    return col_map

# ─────────────────────────────────────────────
# DATA PROCESSING
# ─────────────────────────────────────────────
def is_clevel(title: str) -> bool:
    if not isinstance(title, str) or not title.strip():
        return False
    tl = title.lower()
    has_positive = any(kw in tl for kw in CLEVEL_KW)
    if not has_positive:
        return False
    # Reject pure Director / 10% Owner entries
    if any(neg in tl for neg in REJECT_IF_ONLY):
        # Only keep if a real C-level term is ALSO present
        return any(kw in tl for kw in CLEVEL_KW if kw not in REJECT_IF_ONLY)
    return True

def clean_money(v) -> float:
    s = re.sub(r"[^\d.]", "", str(v))
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0

def split_dt(raw) -> tuple:
    s = str(raw).strip()
    parts = s.split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    return s, ""

def process(df: pd.DataFrame) -> list:
    cols = [str(c) for c in df.columns]
    cm = build_col_map(cols)

    trades = []
    for _, row in df.iterrows():
        try:
            # ── Transaction type filter ────────────────
            tx = str(row.get(cm.get("type", ""), "")).strip()
            if not (tx == "P - Purchase" or tx.upper() == "P"):
                continue

            # ── C-Level title filter ───────────────────
            title = str(row.get(cm.get("title", ""), "")).strip()
            if not is_clevel(title):
                continue

            # ── Ticker ────────────────────────────────
            ticker = re.sub(r"[^A-Z.]", "", str(row.get(cm.get("ticker", ""), "")).strip().upper())
            if not ticker or len(ticker) > 6:
                continue

            # ── Value ─────────────────────────────────
            # OpenInsider stores Value column as plain $ (e.g. "$1,234,567")
            value = clean_money(row.get(cm.get("value", ""), 0))

            # ── Other fields ──────────────────────────
            company = str(row.get(cm.get("company", ""), "")).strip()
            insider = str(row.get(cm.get("insider", ""), "")).strip()
            price   = clean_money(row.get(cm.get("price", ""), 0))
            qty     = str(row.get(cm.get("qty", ""), "")).strip()

            fd, ft = split_dt(row.get(cm.get("filing_date", ""), ""))
            td, tt = split_dt(row.get(cm.get("trade_date",  ""), ""))

            trades.append({
                "ticker":       ticker,
                "company":      company,
                "insider":      insider,
                "title":        title,
                "price":        price,
                "qty":          qty,
                "value":        value,
                "filing_date":  fd,
                "filing_time":  ft,
                "trade_date":   td,
                "trade_time":   tt,
            })
        except Exception:
            continue
    return trades

# ─────────────────────────────────────────────
# DISK CACHE (offline fallback)
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# YFINANCE ENRICHMENT  (price / exchange / sector)
# ─────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def enrich(ticker: str) -> dict:
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        price = (info.get("currentPrice")
                 or info.get("regularMarketPrice")
                 or info.get("previousClose", 0))
        return {
            "price":    round(float(price), 2) if price else 0.0,
            "exchange": (info.get("exchange") or info.get("fullExchangeName", "—")).upper(),
            "sector":   info.get("sector") or info.get("sectorDisp", "—"),
        }
    except Exception:
        return {"price": 0.0, "exchange": "—", "sector": "—"}

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# CARD RENDERER
# ─────────────────────────────────────────────
def render_card(t: dict, info: dict) -> None:
    ticker   = t["ticker"]
    price    = info.get("price", 0.0)
    exchange = info.get("exchange", "—")
    sector   = info.get("sector", "—")
    sc, sbg, sbd = sector_style(sector)

    price_str   = f"${price:.2f}" if price else "—"
    company     = t.get("company", "") or ""
    company_str = (company[:36] + "…") if len(company) > 36 else company
    title_str   = (t["title"] or "")[:32]
    trade_p_str = f"@ ${t['price']:.2f}" if t.get("price") else ""
    qty_str     = re.sub(r"[^\d,.]", "", t.get("qty", ""))

    st.markdown(f"""
<div class="card">
  <div class="card-top">
    <div>
      <div class="ticker">{ticker}</div>
      <div class="company-name">{company_str}</div>
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
    <span class="v-detail">{qty_str} shares {trade_p_str}</span>
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

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    # ── Header ──────────────────────────────────
    st.markdown("""
<div class="app-header">
  <h1>📈 Insider Buy Tracker</h1>
  <div class="sub"><span class="pulse"></span>C-Level purchases · SEC Form 4 · OpenInsider</div>
</div>
""", unsafe_allow_html=True)

    # ── Filters ─────────────────────────────────
    st.markdown('<span class="filter-label">💰 Min Value (K$)</span>', unsafe_allow_html=True)
    vl = st.slider("min_v", 20, 500, 20, 10, label_visibility="collapsed",
                   help="Minimum trade value in thousands of dollars (default: 20 K$ as per OpenInsider screenshot)")

    st.markdown('<span class="filter-label">🔝 Max Value (K$)  —  0 = no limit</span>', unsafe_allow_html=True)
    vh = st.slider("max_v", 0, 10_000, 1_000, 100, label_visibility="collapsed",
                   help="Maximum trade value in K$ (default: 1,000 K$ = $1M, matching screenshot)")

    col_sort, col_btn = st.columns([3, 1])
    with col_sort:
        sort_by = st.selectbox("Sort by", ["Value ↓", "Filing Date ↓", "Trade Date ↓"],
                               label_visibility="visible")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.session_state.pop("show_count", None)
            st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Fetch ────────────────────────────────────
    with st.spinner("Fetching live insider trades…"):
        raw_df, err_msg = fetch_raw(vl, vh)

    using_stale, stale_ts = False, ""

    if raw_df is not None and len(raw_df) > 2:
        trades = process(raw_df)
        if trades:
            save_disk(trades)
        else:
            trades, stale_ts = load_disk()
            using_stale = bool(trades)
    else:
        trades, stale_ts = load_disk()
        using_stale = bool(trades)

    # ── Banners ──────────────────────────────────
    if err_msg:
        st.markdown(
            f'<div class="error-banner">⚠️ Could not reach OpenInsider: {err_msg[:120]}</div>',
            unsafe_allow_html=True)
    if using_stale:
        st.markdown(
            f'<div class="stale-banner">📦 Showing last saved data ({stale_ts[:16]} UTC)</div>',
            unsafe_allow_html=True)

    if not trades:
        st.markdown("""
<div class="empty-state">
  <div class="ei">🔍</div>
  <p>No C-Level purchases found.<br>Try lowering the minimum value or tapping Refresh.</p>
</div>""", unsafe_allow_html=True)
        return

    # ── Sort ─────────────────────────────────────
    key_map = {
        "Value ↓":        lambda x: x["value"],
        "Filing Date ↓":  lambda x: x["filing_date"],
        "Trade Date ↓":   lambda x: x["trade_date"],
    }
    trades = sorted(trades, key=key_map[sort_by], reverse=True)

    # ── Stats bar ────────────────────────────────
    total = sum(t["value"] for t in trades)
    ntick = len({t["ticker"] for t in trades})
    st.markdown(f"""
<div class="stats-bar">
  <div class="stat"><div class="stat-n">{len(trades)}</div><div class="stat-l">Trades</div></div>
  <div class="stat"><div class="stat-n">{ntick}</div><div class="stat-l">Tickers</div></div>
  <div class="stat"><div class="stat-n">{fmt_usd(total)}</div><div class="stat-l">Total</div></div>
</div>""", unsafe_allow_html=True)

    # ── Paginated cards ──────────────────────────
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
        f'Source: openinsider.com · Refresh every 5 min · '
        f'{datetime.utcnow().strftime("%d %b %Y %H:%M")} UTC</p>',
        unsafe_allow_html=True)


if __name__ == "__main__":
    main()
