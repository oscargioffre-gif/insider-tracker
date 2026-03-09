"""
Insider Buy Tracker  v5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BUG FIXES vs v4:
  • v4 cercava "P - Purchase" come testo → 0 risultati (la parola non esiste
    nei Form 4 XML, il codice è <transactionCode>P</transactionCode>)
  • SOLUZIONE: EFTS search SENZA query testuale, solo form=4 + date range
    poi filtrare transactionCode=P nell'XML
  • CIK estratto da _source.entity_id (più affidabile del prefisso accession)
  • XML filename: {acc_flat}.xml oppure idx JSON per nome esatto
  • Fallback a yfinance insider_transactions se EDGAR fallisce
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import streamlit as st
import requests
import re
import json
from datetime import datetime, timedelta, timezone
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
.sub{font-size:.78rem;color:#6e7681;margin:.2rem 0 0;display:flex;align-items:center;justify-content:center;gap:6px}
.pulse{display:inline-block;width:7px;height:7px;background:#10b981;border-radius:50%;animation:blink 2s ease-in-out infinite}
@keyframes blink{0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,.6);opacity:1}50%{box-shadow:0 0 0 5px rgba(16,185,129,0);opacity:.6}}
.fl{font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#6e7681;margin-bottom:.2rem;display:block}
.stats-bar{display:flex;justify-content:space-around;background:#161b22;border:1px solid #21262d;border-radius:12px;padding:.75rem .5rem;margin-bottom:1rem}
.stat{flex:1;text-align:center}
.stat-n{font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:700;color:#10b981}
.stat-l{font-size:.62rem;color:#6e7681;text-transform:uppercase;letter-spacing:.07em}
.card{background:#161b22;border:1px solid #21262d;border-radius:14px;padding:1rem 1.1rem .9rem;margin-bottom:.8rem;position:relative;overflow:hidden;transition:border-color .18s}
.card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:4px;background:linear-gradient(180deg,#10b981,#059669);border-radius:14px 0 0 14px}
.card:hover{border-color:rgba(16,185,129,.5)}
.card-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:.55rem}
.ticker{font-family:'JetBrains Mono',monospace;font-size:1.6rem;font-weight:700;color:#fff;letter-spacing:-.5px;line-height:1}
.cname{font-size:.72rem;color:#6e7681;margin-top:1px}
.ppill{font-family:'JetBrains Mono',monospace;font-size:1rem;font-weight:600;color:#10b981;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.22);border-radius:8px;padding:3px 11px;white-space:nowrap}
.badges{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:.65rem}
.badge{font-size:.68rem;font-weight:600;padding:2px 8px;border-radius:20px;white-space:nowrap;letter-spacing:.03em}
.bm{background:#1c2128;color:#8b949e;border:1px solid #30363d}
.bs{background:rgba(99,102,241,.1);color:#a5b4fc;border:1px solid rgba(99,102,241,.28)}
.bt{background:rgba(251,191,36,.08);color:#fbbf24;border:1px solid rgba(251,191,36,.25)}
.vrow{display:flex;align-items:baseline;gap:8px;margin-bottom:.65rem}
.va{font-family:'JetBrains Mono',monospace;font-size:1.3rem;font-weight:700;color:#10b981}
.vd{font-size:.71rem;color:#6e7681}
.dgrid{display:grid;grid-template-columns:1fr 1fr;gap:7px}
.dbox{background:#0d1117;border:1px solid #21262d;border-radius:9px;padding:.4rem .6rem}
.dlbl{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#6e7681;margin-bottom:2px}
.dval{font-family:'JetBrains Mono',monospace;font-size:.77rem;font-weight:500;color:#e6edf3;line-height:1.3}
.dtm{font-size:.67rem;color:#6e7681}
.irow{margin-top:.55rem;font-size:.75rem;color:#8b949e;display:flex;align-items:center;gap:5px}
.stale-b{background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.28);border-radius:10px;padding:.55rem 1rem;font-size:.78rem;color:#fbbf24;margin-bottom:.9rem;text-align:center}
.err-b{background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.25);border-radius:10px;padding:.55rem 1rem;font-size:.75rem;color:#fca5a5;margin-bottom:.9rem}
.info-b{background:rgba(56,189,248,.07);border:1px solid rgba(56,189,248,.22);border-radius:10px;padding:.55rem 1rem;font-size:.75rem;color:#7dd3fc;margin-bottom:.9rem;text-align:center}
.empty{text-align:center;padding:3rem 1rem;color:#6e7681}
.empty .ei{font-size:2.5rem;margin-bottom:.5rem}
.divider{border:none;border-top:1px solid #21262d;margin:.8rem 0}
.stSlider > div > div > div > div{background:#10b981!important}
div[data-testid="stButton"] button{width:100%!important;background:linear-gradient(135deg,#10b981,#059669)!important;color:#fff!important;border:none!important;border-radius:10px!important;font-weight:700!important;font-size:.9rem!important;padding:.55rem!important}
div[data-testid="stButton"] button:hover{transform:translateY(-1px)!important;box-shadow:0 6px 20px rgba(16,185,129,.3)!important}
div[data-testid="stSelectbox"] label,div[data-testid="stSlider"] label{font-size:.7rem!important;font-weight:700!important;letter-spacing:.1em!important;text-transform:uppercase!important;color:#6e7681!important}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────
CACHE_FILE = "last_known_data.json"

# SEC requires a descriptive user-agent (per robots policy)
SEC_UA = {"User-Agent": "InsiderBuyTracker/5.0 (educational; contact@example.com)"}

CLEVEL_KW = [
    "chief executive","ceo","chief financial","cfo",
    "chief operating","coo","chairman","cob",
    "general counsel","gc","vice president","vp",
    "president","pres","chief ","officer",
]
EXCL_KW = ["director","10% owner","beneficial owner"]

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
    if any(k in tl for k in EXCL_KW):
        return any(k in tl for k in [
            "ceo","cfo","coo","cob","president","chairman",
            "general counsel","vice president",
            "chief executive","chief financial","chief operating",
        ])
    return True

def num(s) -> float:
    try: return float(re.sub(r"[^\d.]","",str(s)) or "0")
    except: return 0.0

def fmt(v: float) -> str:
    if v >= 1_000_000: return f"${v/1_000_000:.2f}M"
    if v >= 1_000:     return f"${v/1_000:.0f}K"
    return f"${v:.0f}"

def sec_style(sector: str) -> tuple:
    for k,v in SECTOR_THEME.items():
        if k.lower() in sector.lower(): return v
    return ("#94a3b8","rgba(148,163,184,.1)","rgba(148,163,184,.28)")

def utc_now():
    return datetime.now(timezone.utc)

# ── EDGAR: Step 1 — EFTS search (NO text query, just form+date) ──
def efts_search(days: int = 30) -> list:
    """
    Returns raw search hits from EDGAR full-text search.
    KEY FIX: NO 'q' parameter — searching for "P - Purchase" returns 0 hits
    because Form 4 XML stores <transactionCode>P</transactionCode>, not that
    human-readable string. We filter transactionCode in the XML instead.
    """
    end   = utc_now()
    start = end - timedelta(days=days)
    try:
        r = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={
                "forms":     "4",
                "dateRange": "custom",
                "startdt":   start.strftime("%Y-%m-%d"),
                "enddt":     end.strftime("%Y-%m-%d"),
                "from":      "0",
            },
            headers=SEC_UA, timeout=15,
        )
        r.raise_for_status()
        return r.json().get("hits", {}).get("hits", [])
    except Exception:
        return []

# ── EDGAR: Step 2 — Fetch Form 4 XML ──────────────────────────
def get_xml(accession: str, entity_id: str) -> bytes | None:
    """
    Fetch the primary Form 4 XML.
    entity_id from _source is the PADDED 10-digit CIK of the filer.
    Strip leading zeros to get the folder name.
    """
    cik      = str(int(entity_id)) if entity_id else ""
    acc_flat = accession.replace("-", "")

    if not cik:
        # Fallback: extract CIK from accession number prefix
        try:
            cik = str(int(accession.split("-")[0]))
        except Exception:
            return None

    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_flat}/"

    # Attempt 1: most common modern filename
    for fname in [f"{acc_flat}.xml", "form4.xml", "xslForm4X01.xml"]:
        try:
            r = requests.get(base + fname, headers=SEC_UA, timeout=5)
            if r.status_code == 200 and b"<ownershipDocument" in r.content:
                return r.content
        except Exception:
            continue

    # Attempt 2: filing index JSON (reliable filename lookup)
    try:
        idx_url = f"https://data.sec.gov/submissions/CIK{int(entity_id):010d}.json" if entity_id else ""
        # Use the -index.htm approach instead
        idx_r = requests.get(
            f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_flat}/",
            headers=SEC_UA, timeout=5,
        )
        if idx_r.status_code == 200:
            xml_files = [
                m for m in re.findall(r'href="([^"]+\.xml)"', idx_r.text)
                if not m.lower().endswith(".xsd")
            ]
            if xml_files:
                fname = xml_files[0].split("/")[-1]
                r2 = requests.get(base + fname, headers=SEC_UA, timeout=5)
                if r2.status_code == 200:
                    return r2.content
    except Exception:
        pass

    return None

# ── EDGAR: Step 3 — Parse Form 4 XML ──────────────────────────
def parse_xml(xml_bytes: bytes, file_date: str) -> list:
    """Parse Form 4 XML → list of {P} purchase trades."""
    try:
        text = xml_bytes.decode("utf-8", errors="ignore")
        text = re.sub(r'\s+xmlns[^=]*="[^"]*"', "", text)
        root = ET.fromstring(text)
    except Exception:
        return []

    rel   = root.find(".//reportingOwnerRelationship")
    title = (rel.findtext("officerTitle") or "") if rel is not None else ""
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
        shares = num(tx.findtext(".//transactionShares/value")        or "0")
        price  = num(tx.findtext(".//transactionPricePerShare/value") or "0")
        td     = tx.findtext(".//transactionDate/value") or ""
        value  = shares * price
        if value <= 0:
            continue
        trades.append({
            "ticker":      ticker, "company":  company,
            "insider":     insider, "title":   title,
            "price":       price,  "qty":      f"{int(shares):,}",
            "value":       value,
            "trade_date":  td,   "trade_time": "",
            "filing_date": file_date, "filing_time": "",
            "source":      "SEC EDGAR",
        })
    return trades

# ── YFINANCE FALLBACK ─────────────────────────────────────────
# Large-cap watchlist used ONLY if EDGAR is unreachable
WATCHLIST = [
    "AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","BRK-B","LLY","JPM",
    "V","UNH","XOM","MA","HD","JNJ","PG","AVGO","MRK","ABBV","CVX","COST",
    "PEP","BAC","NFLX","AMD","ADBE","TMO","CRM","QCOM","INTC","WMT","DIS",
    "GS","MS","C","WFC","USB","TGT","LOW","HON","CAT","DE","BA","LMT","RTX",
    "AMT","PLD","CCI","SPG","EQIX","DLR","O","PSA","EXR","WELL",
]

@st.cache_data(ttl=900, show_spinner=False)
def yf_fallback(vl_k: int, vh_k: int) -> list:
    """Scan watchlist tickers for recent insider purchases via yfinance."""
    import yfinance as yf
    min_v = vl_k * 1_000
    max_v = vh_k * 1_000 if vh_k > 0 else float("inf")
    cutoff = utc_now().date() - timedelta(days=30)
    trades = []

    def check(ticker: str):
        try:
            t = yf.Ticker(ticker)
            df = t.insider_transactions
            if df is None or df.empty:
                return []
            # Filter buys only
            mask = df["Transaction"].str.contains("Buy|Purchase", case=False, na=False)
            df = df[mask]
            if df.empty:
                return []
            info = t.fast_info
            fi   = t.info
            company  = fi.get("longName","")
            sector   = fi.get("sector","—")
            exchange = (fi.get("exchange") or fi.get("fullExchangeName","—")).upper()
            price    = getattr(info,"last_price",None) or fi.get("currentPrice",0)

            rows = []
            for _, row in df.iterrows():
                try:
                    raw_date = row.get("Start Date") or row.get("Date","")
                    if hasattr(raw_date,"date"):
                        d = raw_date.date()
                    else:
                        d = datetime.strptime(str(raw_date)[:10],"%Y-%m-%d").date()
                    if d < cutoff:
                        continue

                    shares   = abs(num(row.get("Shares",0)))
                    val      = abs(num(row.get("Value",0)))
                    if val == 0 and shares > 0 and price:
                        val = shares * float(price)
                    if not (min_v <= val <= max_v):
                        continue

                    title   = str(row.get("Position","Officer")).strip()
                    insider = str(row.get("Insider","")).strip()
                    if not is_clevel(title):
                        continue

                    rows.append({
                        "ticker":      ticker, "company":     company,
                        "insider":     insider,"title":       title,
                        "price":       float(price) if price else 0.0,
                        "qty":         f"{int(shares):,}",
                        "value":       val,
                        "trade_date":  str(d),  "trade_time":  "",
                        "filing_date": str(d),  "filing_time": "",
                        "exchange":    exchange,"sector":      sector,
                        "source":      "yfinance",
                    })
                except Exception:
                    continue
            return rows
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=15) as ex:
        for result in as_completed([ex.submit(check, t) for t in WATCHLIST]):
            try: trades.extend(result.result())
            except: pass

    return trades

# ── MAIN FETCH ─────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_trades(vl_k: int, vh_k: int) -> tuple:
    """Returns (list_of_trades, source_label, error_str)"""
    min_v = vl_k * 1_000
    max_v = vh_k * 1_000 if vh_k > 0 else float("inf")

    # ── Primary: SEC EDGAR ────────────────────────────────────
    hits = efts_search(days=30)

    if hits:
        # Limit to 25 filings max for speed; EDGAR rate limit is 10 req/s
        sample = hits[:25]

        all_trades: list = []
        def process(hit):
            src       = hit.get("_source", {})
            accession = hit.get("_id", "")
            entity_id = src.get("entity_id", "")  # 10-digit padded CIK
            file_date = src.get("file_date", "")
            xml = get_xml(accession, entity_id)
            if xml is None:
                return []
            return parse_xml(xml, file_date)

        with ThreadPoolExecutor(max_workers=15) as ex:
            for fut in as_completed([ex.submit(process, h) for h in sample]):
                try: all_trades.extend(fut.result())
                except: pass

        filtered = [t for t in all_trades if min_v <= t["value"] <= max_v]
        if filtered:
            return filtered, "SEC EDGAR", ""

    # ── Fallback: yfinance ────────────────────────────────────
    yf_trades = yf_fallback(vl_k, vh_k)
    if yf_trades:
        return yf_trades, "yfinance watchlist", ""

    return [], "—", "Nessuna fonte disponibile al momento"

# ── ENRICHMENT (price / exchange / sector from yfinance) ──────
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

# ── DISK CACHE ────────────────────────────────────────────────
def save_disk(trades: list) -> None:
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"trades": trades, "at": utc_now().isoformat()}, f)
    except Exception:
        pass

def load_disk() -> tuple:
    try:
        with open(CACHE_FILE) as f:
            d = json.load(f)
        return d.get("trades", []), d.get("at", "")
    except Exception:
        return [], ""

# ── CARD ──────────────────────────────────────────────────────
def card(t: dict, info: dict) -> None:
    ticker   = t["ticker"]
    price    = t.get("price",0.0) if t.get("source")=="yfinance" else info.get("price",0.0)
    exchange = t.get("exchange","—") if t.get("source")=="yfinance" else info.get("exchange","—")
    sector   = t.get("sector","—")  if t.get("source")=="yfinance" else info.get("sector","—")
    sc, sbg, sbd = sec_style(sector)

    price_str = f"${price:.2f}" if price else "—"
    company   = t.get("company","") or ""
    company   = (company[:36]+"…") if len(company)>36 else company
    title_str = (t.get("title") or "")[:32]
    qty_str   = re.sub(r"[^\d,]","",t.get("qty",""))
    tp_str    = f"@ ${t['price']:.2f}" if t.get("price") else ""

    st.markdown(f"""
<div class="card">
  <div class="card-top">
    <div>
      <div class="ticker">{ticker}</div>
      <div class="cname">{company}</div>
    </div>
    <span class="ppill">{price_str}</span>
  </div>
  <div class="badges">
    <span class="badge bm">📊 {exchange}</span>
    <span class="badge bs" style="color:{sc};background:{sbg};border-color:{sbd};">{sector}</span>
    <span class="badge bt">👤 {title_str}</span>
  </div>
  <div class="vrow">
    <span>🟢</span>
    <span class="va">{fmt(t['value'])}</span>
    <span class="vd">{qty_str} shares {tp_str}</span>
  </div>
  <div class="dgrid">
    <div class="dbox">
      <div class="dlbl">📅 Trade Date</div>
      <div class="dval">{t['trade_date']}</div>
      <div class="dtm">{t['trade_time']}</div>
    </div>
    <div class="dbox">
      <div class="dlbl">🕒 SEC Filing</div>
      <div class="dval">{t['filing_date']}</div>
      <div class="dtm">{t['filing_time']}</div>
    </div>
  </div>
  <div class="irow"><span>👤</span><span>{t['insider']}</span></div>
</div>
""", unsafe_allow_html=True)

# ── MAIN ──────────────────────────────────────────────────────
def main():
    st.markdown("""
<div class="app-header">
  <h1>📈 Insider Buy Tracker</h1>
  <div class="sub"><span class="pulse"></span>C-Level purchases · SEC EDGAR Form 4</div>
</div>
""", unsafe_allow_html=True)

    # Filters
    st.markdown('<span class="fl">💰 Min Value (K$)</span>', unsafe_allow_html=True)
    vl = st.slider("min_v", 20, 500, 20, 10, label_visibility="collapsed")

    st.markdown('<span class="fl">🔝 Max Value (K$) — 0 = no limit</span>', unsafe_allow_html=True)
    vh = st.slider("max_v", 0, 10_000, 1_000, 100, label_visibility="collapsed")

    c1, c2 = st.columns([3, 1])
    with c1:
        sort_by = st.selectbox("Sort by",
            ["Value ↓","Filing Date ↓","Trade Date ↓"],
            label_visibility="visible")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.session_state.pop("show_count", None)
            st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # Fetch with progress
    prog = st.progress(0, text="🔍 Connessione a SEC EDGAR…")

    trades, source, err = fetch_trades(vl, vh)
    prog.progress(100, text=f"✅ Dati caricati da {source}")
    prog.empty()

    # Stale fallback
    using_stale, stale_ts = False, ""
    if not trades:
        trades, stale_ts = load_disk()
        using_stale = bool(trades)
    elif trades:
        save_disk(trades)

    # Banners
    if err:
        st.markdown(f'<div class="err-b">⚠️ {err}</div>', unsafe_allow_html=True)
    if using_stale:
        st.markdown(f'<div class="stale-b">📦 Dati salvati ({stale_ts[:16]} UTC)</div>',
                    unsafe_allow_html=True)
    if source != "—" and not using_stale:
        st.markdown(f'<div class="info-b">🔗 Fonte: <b>{source}</b></div>',
                    unsafe_allow_html=True)

    if not trades:
        st.markdown("""
<div class="empty"><div class="ei">🔍</div>
<p>Nessun acquisto C-Level trovato.<br>Prova a ridurre il valore minimo o premi Refresh.</p></div>
""", unsafe_allow_html=True)
        return

    # Sort
    trades = sorted(trades, key={
        "Value ↓":       lambda x: x["value"],
        "Filing Date ↓": lambda x: x["filing_date"],
        "Trade Date ↓":  lambda x: x["trade_date"],
    }[sort_by], reverse=True)

    # Stats bar
    total = sum(t["value"] for t in trades)
    ntick = len({t["ticker"] for t in trades})
    st.markdown(f"""
<div class="stats-bar">
  <div class="stat"><div class="stat-n">{len(trades)}</div><div class="stat-l">Trades</div></div>
  <div class="stat"><div class="stat-n">{ntick}</div><div class="stat-l">Tickers</div></div>
  <div class="stat"><div class="stat-n">{fmt(total)}</div><div class="stat-l">Totale</div></div>
</div>""", unsafe_allow_html=True)

    # Cards
    BATCH = 12
    if "show_count" not in st.session_state:
        st.session_state.show_count = BATCH

    for t in trades[: st.session_state.show_count]:
        # For EDGAR trades, enrich with live price/sector/exchange
        info = enrich(t["ticker"]) if t.get("source") == "SEC EDGAR" else {}
        card(t, info)

    rem = len(trades) - st.session_state.show_count
    if rem > 0:
        if st.button(f"⬇️  Carica altri {min(BATCH,rem)}  ({rem} rimanenti)"):
            st.session_state.show_count += BATCH
            st.rerun()

    st.markdown(
        f'<p style="text-align:center;color:#6e7681;font-size:.68rem;margin-top:1.4rem;">'
        f'Fonte: {source} · Cache 5 min · {utc_now().strftime("%d %b %Y %H:%M")} UTC</p>',
        unsafe_allow_html=True)

if __name__ == "__main__":
    main()
