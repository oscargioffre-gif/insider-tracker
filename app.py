"""
Insider Buy Tracker  v5
Data source: SEC EDGAR RSS feed + direct Form 4 XML
  Primary:  https://www.sec.gov/cgi-bin/browse-edgar?type=4&action=getcurrent&output=atom
  Enrichment: yfinance (price / sector / exchange)
All endpoints are .gov — no firewall issues on Streamlit Cloud.
"""

import streamlit as st
import requests
import re
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from xml.etree import ElementTree as ET

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
.card{background:#161b22;border:1px solid #21262d;border-radius:14px;padding:1rem 1.1rem .9rem;margin-bottom:.8rem;position:relative;overflow:hidden;transition:border-color .18s}
.card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:4px;background:linear-gradient(180deg,#10b981,#059669);border-radius:14px 0 0 14px}
.card:hover{border-color:rgba(16,185,129,.5)}
.card-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:.55rem}
.ticker{font-family:'JetBrains Mono',monospace;font-size:1.6rem;font-weight:700;color:#fff;letter-spacing:-.5px;line-height:1}
.company-name{font-size:.72rem;color:#6e7681;margin-top:1px}
.price-pill{font-family:'JetBrains Mono',monospace;font-size:1rem;font-weight:600;color:#10b981;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.22);border-radius:8px;padding:3px 11px;white-space:nowrap}
.badges{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:.65rem}
.badge{font-size:.68rem;font-weight:600;padding:2px 8px;border-radius:20px;white-space:nowrap;letter-spacing:.03em}
.b-market{background:#1c2128;color:#8b949e;border:1px solid #30363d}
.b-sector{background:rgba(99,102,241,.1);color:#a5b4fc;border:1px solid rgba(99,102,241,.28)}
.b-title{background:rgba(251,191,36,.08);color:#fbbf24;border:1px solid rgba(251,191,36,.25)}
.value-row{display:flex;align-items:baseline;gap:8px;margin-bottom:.65rem}
.v-icon{font-size:1rem}
.v-amount{font-family:'JetBrains Mono',monospace;font-size:1.3rem;font-weight:700;color:#10b981}
.v-detail{font-size:.71rem;color:#6e7681}
.dates-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px}
.date-box{background:#0d1117;border:1px solid #21262d;border-radius:9px;padding:.4rem .6rem}
.date-lbl{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#6e7681;margin-bottom:2px}
.date-val{font-family:'JetBrains Mono',monospace;font-size:.77rem;font-weight:500;color:#e6edf3;line-height:1.3}
.date-time{font-size:.67rem;color:#6e7681}
.insider-row{margin-top:.55rem;font-size:.75rem;color:#8b949e;display:flex;align-items:center;gap:5px}
.stale-banner{background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.28);border-radius:10px;padding:.55rem 1rem;font-size:.78rem;color:#fbbf24;margin-bottom:.9rem;text-align:center}
.error-banner{background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.25);border-radius:10px;padding:.55rem 1rem;font-size:.75rem;color:#fca5a5;margin-bottom:.9rem}
.info-banner{background:rgba(56,189,248,.07);border:1px solid rgba(56,189,248,.22);border-radius:10px;padding:.55rem 1rem;font-size:.75rem;color:#7dd3fc;margin-bottom:.9rem;text-align:center}
.empty-state{text-align:center;padding:3rem 1rem;color:#6e7681}
.empty-state .ei{font-size:2.5rem;margin-bottom:.5rem}
.divider{border:none;border-top:1px solid #21262d;margin:.8rem 0}
.stSlider > div > div > div > div{background:#10b981!important}
div[data-testid="stButton"] button{width:100%!important;background:linear-gradient(135deg,#10b981,#059669)!important;color:#fff!important;border:none!important;border-radius:10px!important;font-weight:700!important;font-size:.9rem!important;padding:.55rem!important}
div[data-testid="stButton"] button:hover{transform:translateY(-1px)!important;box-shadow:0 6px 20px rgba(16,185,129,.3)!important}
div[data-testid="stSelectbox"] label,div[data-testid="stSlider"] label{font-size:.7rem!important;font-weight:700!important;letter-spacing:.1em!important;text-transform:uppercase!important;color:#6e7681!important}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────
CACHE_FILE = "last_known_data.json"

# SEC requires descriptive User-Agent
SEC_UA = "InsiderBuyTracker/5.0 (educational; contact@example.com)"
SEC_H  = {"User-Agent": SEC_UA, "Accept": "application/json, text/xml, */*"}

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
    "Consumer":      ("#f472b6","rgba(244,114,182,.1)","rgba(244,114,182,.28)"),
    "Industrials":   ("#a78bfa","rgba(167,139,250,.1)","rgba(167,139,250,.28)"),
    "Materials":     ("#4ade80","rgba(74,222,128,.1)","rgba(74,222,128,.28)"),
    "Utilities":     ("#facc15","rgba(250,204,21,.1)","rgba(250,204,21,.28)"),
    "Real Estate":   ("#f87171","rgba(248,113,113,.1)","rgba(248,113,113,.28)"),
    "Communication": ("#38bdf8","rgba(56,189,248,.1)","rgba(56,189,248,.28)"),
}

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

def clean_num(s) -> float:
    try:   return float(re.sub(r"[^\d.]","",str(s)) or "0")
    except: return 0.0

def fmt_usd(v: float) -> str:
    if v >= 1_000_000: return f"${v/1_000_000:.2f}M"
    if v >= 1_000:     return f"${v/1_000:.0f}K"
    return f"${v:.0f}"

def sector_style(sector: str) -> tuple:
    for k, v in SECTOR_THEME.items():
        if k.lower() in sector.lower(): return v
    return ("#94a3b8","rgba(148,163,184,.1)","rgba(148,163,184,.28)")

# ── STEP 1: RSS feed — get latest Form 4 filing URLs ─────────
def get_filing_links(max_count: int = 100) -> list[dict]:
    """
    Calls the EDGAR current-filings RSS (Atom) feed filtered to Form 4.
    Returns list of {accession, file_date, link} dicts.
    This endpoint is always open to the public.
    """
    url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcurrent&type=4&dateb=&owner=include"
        f"&count={max_count}&search_text=&output=atom"
    )
    try:
        r = requests.get(url, headers=SEC_H, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return []

    # Strip Atom namespace so ElementTree can parse easily
    text = re.sub(r'\s*xmlns[^=]*="[^"]*"', "", r.text)
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []

    entries = []
    for entry in root.findall(".//entry"):
        link_el   = entry.find("link")
        href      = link_el.get("href","") if link_el is not None else ""
        updated   = (entry.findtext("updated") or "")[:10]
        # Skip if older than 30 days
        try:
            if datetime.strptime(updated, "%Y-%m-%d") < datetime.utcnow() - timedelta(days=30):
                continue
        except Exception:
            pass
        if href:
            entries.append({"link": href, "file_date": updated})

    return entries

# ── STEP 2: From filing index page → find XML URL ─────────────
def resolve_xml_url(index_url: str) -> str | None:
    """
    Given an EDGAR filing index page URL, find the primary Form 4 XML.
    """
    # Convert index page URL to machine-readable JSON index
    # e.g. .../Archives/edgar/data/CIK/ACC-NO-IDX.htm
    #   → .../Archives/edgar/data/CIK/ACCNO/ACC-NO-index.json  (not always)
    # Easiest: just fetch the HTML index and regex-find the XML link.
    try:
        r = requests.get(index_url, headers=SEC_H, timeout=8)
        if r.status_code != 200:
            return None
        # Find links to XML files (not XSD, not viewer)
        xml_links = re.findall(
            r'href="(/Archives/edgar/data/[^"]+\.xml)"', r.text
        )
        xml_links = [x for x in xml_links if not x.lower().endswith(".xsd")]
        if not xml_links:
            return None
        return "https://www.sec.gov" + xml_links[0]
    except Exception:
        return None

# ── STEP 3: Fetch + parse Form 4 XML ─────────────────────────
def fetch_and_parse(entry: dict) -> list[dict]:
    try:
        index_url = entry["link"]
        file_date = entry["file_date"]

        xml_url = resolve_xml_url(index_url)
        if not xml_url:
            return []

        r = requests.get(xml_url, headers=SEC_H, timeout=8)
        if r.status_code != 200 or b"<ownershipDocument" not in r.content:
            return []

        return _parse_xml(r.content, file_date)
    except Exception:
        return []


def _parse_xml(xml_bytes: bytes, file_date: str) -> list[dict]:
    try:
        text = xml_bytes.decode("utf-8", errors="ignore")
        text = re.sub(r'\s+xmlns[^=]*="[^"]*"', "", text)
        root = ET.fromstring(text)
    except ET.ParseError:
        return []

    # Officer title
    rel   = root.find(".//reportingOwnerRelationship")
    title = ""
    if rel is not None:
        title = rel.findtext("officerTitle") or ""

    if not is_clevel(title):
        return []

    ticker  = (root.findtext(".//issuer/issuerTradingSymbol") or "").strip().upper()
    company = (root.findtext(".//issuer/issuerName")          or "").strip()
    insider = (root.findtext(".//reportingOwner/reportingOwnerId/rptOwnerName") or "").strip()

    if not ticker or not re.match(r"^[A-Z.]{1,6}$", ticker):
        return []

    trades = []
    for tx in root.findall(".//nonDerivativeTransaction"):
        if (tx.findtext(".//transactionCode") or "") != "P":
            continue
        shares    = clean_num(tx.findtext(".//transactionShares/value")       or "0")
        price_per = clean_num(tx.findtext(".//transactionPricePerShare/value") or "0")
        tdate     = tx.findtext(".//transactionDate/value") or ""
        value     = shares * price_per
        if value <= 0 or shares <= 0:
            continue
        trades.append({
            "ticker":      ticker,
            "company":     company,
            "insider":     insider,
            "title":       title,
            "price":       price_per,
            "qty":         f"{int(shares):,}",
            "value":       value,
            "trade_date":  tdate,
            "trade_time":  "",
            "filing_date": file_date,
            "filing_time": "",
        })
    return trades

# ── MAIN FETCH (cached 5 min) ─────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_trades(vl_k: int, vh_k: int) -> tuple[list, str]:
    entries = get_filing_links(max_count=100)
    if not entries:
        return [], "Impossibile raggiungere SEC EDGAR RSS (www.sec.gov)"

    all_trades: list = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(fetch_and_parse, e) for e in entries]
        for fut in as_completed(futures):
            try: all_trades.extend(fut.result())
            except: pass

    min_v = vl_k * 1_000
    max_v = vh_k * 1_000 if vh_k > 0 else float("inf")
    return [t for t in all_trades if min_v <= t["value"] <= max_v], ""

# ── YFINANCE ─────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def enrich(ticker: str) -> dict:
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose",0)
        return {
            "price":    round(float(price),2) if price else 0.0,
            "exchange": (info.get("exchange") or info.get("fullExchangeName") or "—").upper(),
            "sector":   info.get("sector") or info.get("sectorDisp") or "—",
        }
    except:
        return {"price":0.0,"exchange":"—","sector":"—"}

# ── DISK CACHE ────────────────────────────────────────────────
def save_disk(trades):
    try:
        with open(CACHE_FILE,"w") as f:
            json.dump({"trades":trades,"at":datetime.utcnow().isoformat()},f)
    except: pass

def load_disk():
    try:
        with open(CACHE_FILE) as f: d=json.load(f)
        return d.get("trades",[]), d.get("at","")
    except: return [],""

# ── CARD ──────────────────────────────────────────────────────
def render_card(t: dict, info: dict):
    ticker=t["ticker"]; price=info.get("price",0.0)
    exchange=info.get("exchange","—"); sector=info.get("sector","—")
    sc,sbg,sbd=sector_style(sector)
    price_str=f"${price:.2f}" if price else "—"
    co=(t.get("company","") or ""); co=(co[:36]+"…") if len(co)>36 else co
    title_s=(t.get("title","") or "")[:32]
    qty_s=re.sub(r"[^\d,]","",t.get("qty",""))
    tp_s=f"@ ${t['price']:.2f}" if t.get("price") else ""

    st.markdown(f"""
<div class="card">
  <div class="card-top">
    <div><div class="ticker">{ticker}</div><div class="company-name">{co}</div></div>
    <span class="price-pill">{price_str}</span>
  </div>
  <div class="badges">
    <span class="badge b-market">📊 {exchange}</span>
    <span class="badge b-sector" style="color:{sc};background:{sbg};border-color:{sbd};">{sector}</span>
    <span class="badge b-title">👤 {title_s}</span>
  </div>
  <div class="value-row">
    <span class="v-icon">🟢</span>
    <span class="v-amount">{fmt_usd(t['value'])}</span>
    <span class="v-detail">{qty_s} shares {tp_s}</span>
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
</div>""", unsafe_allow_html=True)

# ── MAIN ──────────────────────────────────────────────────────
def main():
    st.markdown("""
<div class="app-header">
  <h1>📈 Insider Buy Tracker</h1>
  <div class="sub"><span class="pulse"></span>C-Level purchases · SEC EDGAR · Form 4</div>
</div>""", unsafe_allow_html=True)

    st.markdown('<span class="filter-label">💰 Min Value (K$)</span>', unsafe_allow_html=True)
    vl = st.slider("min_v", 20, 500, 20, 10, label_visibility="collapsed")

    st.markdown('<span class="filter-label">🔝 Max Value (K$) — 0 = no limit</span>', unsafe_allow_html=True)
    vh = st.slider("max_v", 0, 10_000, 1_000, 100, label_visibility="collapsed")

    col_s,col_b = st.columns([3,1])
    with col_s:
        sort_by = st.selectbox("Sort by",
            ["Value ↓","Filing Date ↓","Trade Date ↓"], label_visibility="visible")
    with col_b:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.session_state.pop("show_count",None)
            st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-banner">🔗 Fonte: <b>SEC EDGAR RSS</b> · www.sec.gov · Form 4 XML</div>',
        unsafe_allow_html=True)

    prog = st.progress(0, text="⏳ Caricamento Form 4 da SEC EDGAR…")
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
        st.markdown(f'<div class="stale-banner">📦 Dati salvati ({stale_ts[:16]} UTC)</div>',
                    unsafe_allow_html=True)

    if not trades:
        st.markdown("""
<div class="empty-state">
  <div class="ei">🔍</div>
  <p>Nessun acquisto C-Level trovato.<br>Prova a ridurre il valore minimo o premi Refresh.</p>
</div>""", unsafe_allow_html=True)
        return

    key_fn = {
        "Value ↓":       lambda x: x["value"],
        "Filing Date ↓": lambda x: x["filing_date"],
        "Trade Date ↓":  lambda x: x["trade_date"],
    }
    trades = sorted(trades, key=key_fn[sort_by], reverse=True)

    total = sum(t["value"] for t in trades)
    ntick = len({t["ticker"] for t in trades})
    st.markdown(f"""
<div class="stats-bar">
  <div class="stat"><div class="stat-n">{len(trades)}</div><div class="stat-l">Trades</div></div>
  <div class="stat"><div class="stat-n">{ntick}</div><div class="stat-l">Tickers</div></div>
  <div class="stat"><div class="stat-n">{fmt_usd(total)}</div><div class="stat-l">Totale</div></div>
</div>""", unsafe_allow_html=True)

    BATCH = 12
    if "show_count" not in st.session_state:
        st.session_state.show_count = BATCH

    for trade in trades[:st.session_state.show_count]:
        render_card(trade, enrich(trade["ticker"]))

    remaining = len(trades) - st.session_state.show_count
    if remaining > 0:
        if st.button(f"⬇️  Carica altri {min(BATCH,remaining)}  ({remaining} rimanenti)"):
            st.session_state.show_count += BATCH
            st.rerun()

    st.markdown(
        f'<p style="text-align:center;color:#6e7681;font-size:.68rem;margin-top:1.4rem;">'
        f'Fonte: SEC EDGAR · Cache 5 min · {datetime.utcnow().strftime("%d %b %Y %H:%M")} UTC</p>',
        unsafe_allow_html=True)

if __name__ == "__main__":
    main()
