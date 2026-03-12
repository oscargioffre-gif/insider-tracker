"""
OS OpenInSider  v9
"""
import streamlit as st
import requests, re, json, time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

st.set_page_config(page_title="OS OpenInSider", page_icon="📈",
                   layout="centered", initial_sidebar_state="collapsed")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important;background:#080c10!important;color:#f0f6fc!important}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:.6rem .85rem 4rem!important;max-width:540px!important;margin:auto}
.app-header{text-align:center;padding:1.6rem 0 1.2rem;position:relative}
.header-glow{position:absolute;top:-20px;left:50%;transform:translateX(-50%);width:300px;height:130px;background:radial-gradient(ellipse,rgba(16,185,129,.22) 0%,transparent 70%);pointer-events:none}
.app-header h1{font-size:2rem;font-weight:900;letter-spacing:-.8px;color:#fff;margin:0;line-height:1.1}
.app-header h1 span{color:#10b981}
.header-sub{font-size:.8rem;color:#8b949e;margin:.4rem 0 0;display:flex;align-items:center;justify-content:center;gap:8px;letter-spacing:.05em;text-transform:uppercase;font-weight:700}
.live-dot{width:7px;height:7px;background:#10b981;border-radius:50%;box-shadow:0 0 0 0 rgba(16,185,129,.7);animation:ping 2s ease infinite}
@keyframes ping{0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,.7)}50%{box-shadow:0 0 0 9px rgba(16,185,129,0)}}
.fc-wrap{background:#0f1419;border:1px solid #2d3748;border-radius:14px;padding:12px 14px 10px;margin-top:4px}
.fc-label{font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#8b949e;margin-bottom:4px}
.fc-value{font-family:'JetBrains Mono',monospace;font-size:1.2rem;font-weight:700;color:#10b981}
.fc-sub{font-size:.72rem;color:#6b7280;margin-top:3px}
.pill-label{font-size:.75rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#8b949e;margin:14px 0 7px;display:flex;align-items:center;gap:6px}
div[data-testid="stPills"]{gap:7px!important;flex-wrap:wrap!important}
button[data-testid="stPillsButton"]{background:#0c1118!important;border:1px solid #1e2d3d!important;border-radius:12px!important;color:#3d4f61!important;font-family:'Inter',sans-serif!important;font-weight:700!important;font-size:.88rem!important;padding:9px 14px!important;min-width:54px!important;text-align:center!important;transition:all .18s cubic-bezier(.4,0,.2,1)!important;cursor:pointer!important;box-shadow:none!important;letter-spacing:.02em!important}
button[data-testid="stPillsButton"]:hover{border-color:#10b981!important;color:#a7f3d0!important;background:#081812!important;box-shadow:0 0 0 1px rgba(16,185,129,.3),0 0 18px rgba(16,185,129,.4),0 0 6px rgba(16,185,129,.2)!important;transform:translateY(-2px) scale(1.05)!important}
button[data-testid="stPillsButton"][aria-selected="true"]{background:rgba(16,185,129,.13)!important;border-color:#10b981!important;color:#6ee7b7!important;box-shadow:0 0 0 1px rgba(16,185,129,.5),0 0 24px rgba(16,185,129,.55),0 0 8px rgba(16,185,129,.3),inset 0 0 20px rgba(16,185,129,.1)!important;text-shadow:0 0 14px rgba(16,185,129,.8)!important;transform:translateY(-1px)!important}
button[data-testid="stPillsButton"][aria-selected="true"]:hover{color:#d1fae5!important;box-shadow:0 0 0 2px rgba(16,185,129,.7),0 0 32px rgba(16,185,129,.7),0 0 14px rgba(16,185,129,.4),inset 0 0 24px rgba(16,185,129,.15)!important;text-shadow:0 0 18px rgba(16,185,129,1)!important;transform:translateY(-3px) scale(1.07)!important}
.ar-bar{display:flex;align-items:center;justify-content:space-between;background:#0a0f14;border:1px solid #2d3748;border-radius:12px;padding:11px 14px;margin-bottom:14px}
.ar-left{display:flex;align-items:center;gap:10px}
.ar-dot-on{width:9px;height:9px;background:#10b981;border-radius:50%;flex-shrink:0;animation:ping 2s ease infinite}
.ar-dot-off{width:9px;height:9px;background:#374151;border-radius:50%;flex-shrink:0}
.ar-title{font-size:.84rem;font-weight:700;color:#f0f6fc}
.ar-sub{font-size:.73rem;color:#8b949e;margin-top:2px}
.stats-bar{display:grid;grid-template-columns:1fr 1fr 1fr;background:#0f1419;border:1px solid #2d3748;border-radius:14px;padding:.85rem .4rem .6rem;margin-bottom:.9rem;overflow:hidden;position:relative}
.stats-bar::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#10b981,transparent)}
.stat{text-align:center;padding:.1rem 0}
.stat+.stat{border-left:1px solid #1a2535}
.stat-n{font-family:'JetBrains Mono',monospace;font-size:1.15rem;font-weight:700;color:#10b981}
.stat-l{font-size:.68rem;color:#8b949e;text-transform:uppercase;letter-spacing:.07em;margin-top:3px}
.stat-ts{grid-column:1/-1;text-align:center;font-size:.67rem;color:#374151;margin-top:.45rem;border-top:1px solid #0f1419;padding-top:.35rem}
.card{background:#0f1419;border:1px solid #2d3748;border-radius:16px;padding:1.1rem 1.2rem 1rem;margin-bottom:.8rem;position:relative;overflow:hidden;transition:border-color .2s,transform .15s,box-shadow .2s}
.card:hover{border-color:rgba(16,185,129,.6);transform:translateY(-1px);box-shadow:0 8px 30px rgba(16,185,129,.1)}
.card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:linear-gradient(180deg,#10b981 0%,#059669 50%,#10b981 100%);background-size:100% 200%;animation:bscroll 3s ease infinite;border-radius:16px 0 0 16px}
@keyframes bscroll{0%,100%{background-position:0% 0%}50%{background-position:0% 100%}}
.card-top{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:.55rem}
.ticker{font-family:'JetBrains Mono',monospace;font-size:1.65rem;font-weight:700;color:#fff;letter-spacing:-.5px;line-height:1}
.company-name{font-size:.8rem;color:#8b949e;margin-top:3px;font-weight:500}
.price-pill{font-family:'JetBrains Mono',monospace;font-size:1rem;font-weight:600;color:#10b981;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3);border-radius:8px;padding:4px 11px;white-space:nowrap;flex-shrink:0}
.role-row{display:flex;align-items:center;gap:8px;margin-bottom:.55rem}
.role-pill{font-family:'JetBrains Mono',monospace;font-size:.84rem;font-weight:700;color:#0a0f14;background:#fbbf24;border-radius:6px;padding:3px 10px;letter-spacing:.05em;text-transform:uppercase;flex-shrink:0}
.role-full{font-size:.82rem;color:#8b949e;font-weight:500}
.badges{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:.6rem}
.badge{font-size:.73rem;font-weight:600;padding:3px 9px;border-radius:20px;white-space:nowrap}
.b-mkt{background:#0a0f14;color:#6b7280;border:1px solid #2d3748}
.value-row{display:flex;align-items:center;gap:10px;margin-bottom:.65rem;padding:.55rem .75rem;background:#080c10;border-radius:10px;border:1px solid #111822}
.v-dot{width:8px;height:8px;background:#10b981;border-radius:50%;flex-shrink:0;box-shadow:0 0 9px rgba(16,185,129,.65)}
.v-amount{font-family:'JetBrains Mono',monospace;font-size:1.3rem;font-weight:700;color:#10b981}
.v-detail{font-size:.77rem;color:#6b7280;margin-top:2px;font-weight:500}
.dates-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:.55rem}
.date-box{background:#080c10;border:1px solid #1e2530;border-radius:10px;padding:.45rem .7rem}
.date-lbl{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;margin-bottom:4px;display:flex;align-items:center;gap:4px}
.date-val{font-family:'JetBrains Mono',monospace;font-size:.84rem;font-weight:600;color:#e2e8f0}
.date-sub{font-size:.72rem;color:#6b7280;margin-top:3px;font-weight:500}
.fresh-badge{font-size:.63rem;font-weight:700;color:#10b981;background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.3);border-radius:4px;padding:1px 5px;letter-spacing:.06em}
.insider-row{display:flex;align-items:center;gap:6px;font-size:.8rem;color:#6b7280;padding-top:.4rem;border-top:1px solid #111822;font-weight:500}
.insider-name{color:#8b949e}
.stale-banner{background:rgba(245,158,11,.09);border:1px solid rgba(245,158,11,.3);border-radius:10px;padding:.55rem 1rem;font-size:.8rem;color:#fbbf24;margin-bottom:.8rem;text-align:center;font-weight:600}
.error-banner{background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.25);border-radius:10px;padding:.55rem 1rem;font-size:.8rem;color:#fca5a5;margin-bottom:.8rem}
.empty-state{text-align:center;padding:2.8rem 1rem}
.empty-state .ei{font-size:2.4rem;margin-bottom:.6rem}
.empty-state p{font-size:.9rem;line-height:1.7;color:#6b7280}
.hr{border:none;border-top:1px solid #111822;margin:.5rem 0 .9rem}
.stSlider>div>div>div>div{background:#10b981!important}
div[data-testid="stSlider"] label{display:none!important}
div[data-testid="stButton"] button{width:100%!important;background:linear-gradient(135deg,#10b981,#059669)!important;color:#fff!important;border:none!important;border-radius:10px!important;font-weight:700!important;font-size:.95rem!important;padding:.55rem!important;letter-spacing:.02em!important;transition:all .15s!important}
div[data-testid="stButton"] button:hover{transform:translateY(-1px)!important;box-shadow:0 6px 22px rgba(16,185,129,.38)!important}
div[data-testid="stSelectbox"]>label{font-size:.72rem!important;font-weight:700!important;letter-spacing:.08em!important;text-transform:uppercase!important;color:#8b949e!important}
</style>
"""

CACHE_FILE = "last_known_data.json"
HEADERS_BROWSER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
CLEVEL_KW  = ["chief executive","ceo","chief financial","cfo","chief operating","coo","chairman","cob","general counsel","gc","vice president","vp","president","pres","chief ","officer"]
EXCLUDE_KW = ["director","10% owner","beneficial owner"]
SECTOR_THEME = {
    "Technology":("#818cf8","rgba(99,102,241,.12)","rgba(99,102,241,.3)"),
    "Healthcare":("#34d399","rgba(52,211,153,.12)","rgba(52,211,153,.3)"),
    "Financials":("#60a5fa","rgba(96,165,250,.12)","rgba(96,165,250,.3)"),
    "Financial Services":("#60a5fa","rgba(96,165,250,.12)","rgba(96,165,250,.3)"),
    "Energy":("#fb923c","rgba(251,146,60,.12)","rgba(251,146,60,.3)"),
    "Consumer Cyclical":("#f472b6","rgba(244,114,182,.12)","rgba(244,114,182,.3)"),
    "Consumer Defensive":("#f9a8d4","rgba(249,168,212,.12)","rgba(249,168,212,.3)"),
    "Industrials":("#a78bfa","rgba(167,139,250,.12)","rgba(167,139,250,.3)"),
    "Basic Materials":("#4ade80","rgba(74,222,128,.12)","rgba(74,222,128,.3)"),
    "Utilities":("#facc15","rgba(250,204,21,.12)","rgba(250,204,21,.3)"),
    "Real Estate":("#f87171","rgba(248,113,113,.12)","rgba(248,113,113,.3)"),
    "Communication Services":("#38bdf8","rgba(56,189,248,.12)","rgba(56,189,248,.3)"),
}
REFRESH_OPTIONS = {"5 min":300,"10 min":600,"15 min":900,"30 min":1800}
GIORNI_IT = ["Lun","Mar","Mer","Gio","Ven","Sab","Dom"]
ALL_SECTORS = [
    "Technology","Healthcare","Financials","Financial Services",
    "Energy","Consumer Cyclical","Consumer Defensive","Industrials",
    "Basic Materials","Utilities","Real Estate","Communication Services",
]

_ROLE_MAP = [
    ("CEO",["chief executive officer","chief executive","ceo"]),
    ("CFO",["chief financial officer","chief financial","cfo"]),
    ("COO",["chief operating officer","chief operating","coo"]),
    ("CTO",["chief technology officer","chief technology","cto"]),
    ("CMO",["chief medical officer","chief medical","cmo"]),
    ("CSO",["chief scientific officer","chief scientific","cso"]),
    ("CLO",["chief legal officer","chief legal","clo"]),
    ("CAO",["chief accounting officer","chief accounting","cao"]),
    ("CBO",["chief business officer","chief business","cbo"]),
    ("CHRO",["chief human resources","chief hr","chro"]),
    ("COB",["chairman of the board","chairman","cob"]),
    ("Pres",["president"]),("GC",["general counsel"]),
    ("EVP",["executive vice president","evp"]),
    ("SVP",["senior vice president","svp"]),
    ("VP",["vice president","vp"]),
    ("Treasurer",["treasurer"]),("Secretary",["secretary"]),("Officer",["officer"]),
]

def extract_role(title):
    if not title or not title.strip():
        return "—", "—"
    tl = title.lower().strip()
    for abbr, kws in _ROLE_MAP:
        if any(k in tl for k in kws):
            return abbr, title.strip()
    return title.strip()[:8].upper(), title.strip()

def is_clevel(title):
    if not isinstance(title, str) or not title.strip():
        return False
    tl = title.lower()
    if not any(k in tl for k in CLEVEL_KW):
        return False
    if any(k in tl for k in EXCLUDE_KW):
        return any(k in tl for k in ["ceo","cfo","coo","cob","president","chairman",
                                      "general counsel","vice president",
                                      "chief executive","chief financial","chief operating"])
    return True

def _oi_parse_num(s):
    return re.sub(r"[$,\s+]", "", s.strip())

def clean_num(s):
    try:
        return float(re.sub(r"[^\d.]", "", str(s)) or "0")
    except:
        return 0.0

def fmt_usd(v):
    if v >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:.0f}"

def sector_style(s):
    for k, v in SECTOR_THEME.items():
        if k.lower() in s.lower():
            return v
    return "#6b7280", "rgba(107,114,128,.12)", "rgba(107,114,128,.3)"

def days_ago_label(ds):
    try:
        diff = (datetime.utcnow().date() - datetime.strptime(ds, "%Y-%m-%d").date()).days
        return "Oggi" if diff == 0 else ("Ieri" if diff == 1 else f"{diff}gg fa")
    except:
        return ""

def is_fresh(ds):
    try:
        return (datetime.utcnow().date() - datetime.strptime(ds, "%Y-%m-%d").date()).days <= 1
    except:
        return False

def oi_safe_fetch(url, retries=3, delay=4):
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS_BROWSER, timeout=20)
            if r.status_code == 200:
                return r
        except:
            pass
        if attempt < retries:
            time.sleep(delay * attempt)
    return None

def _detect_columns(header_row):
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
    for k, v in {"filing_date":1,"trade_date":2,"ticker":3,"company":4,
                 "insider":5,"title":6,"type":7,"price":8,"qty":9,"value":13}.items():
        if k not in cols:
            cols[k] = v
    return cols

def _find_table(soup):
    for t in soup.find_all("table"):
        if any(c in " ".join(t.get("class", [])) for c in ["tinytable","sortable"]):
            return t
    tables = soup.find_all("table")
    return max(tables, key=lambda t: len(t.find_all("tr")), default=None) if tables else None

def _parse_table(soup, cutoff):
    table = _find_table(soup)
    if not table:
        return []
    all_rows = table.find_all("tr")
    if not all_rows:
        return []
    cols = _detect_columns(all_rows[0])
    results = []
    for tr in all_rows[1:]:
        tds = tr.find_all("td")
        if len(tds) < 8:
            continue
        try:
            def get(key, default=""):
                idx = cols.get(key, -1)
                if idx < 0 or idx >= len(tds):
                    return default
                return tds[idx].get_text(strip=True)
            ttype = get("type")
            if (ttype.split(" ")[0].upper() if ttype else "") != "P":
                continue
            trade_raw  = get("trade_date")
            filing_raw = get("filing_date")
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
            ticker = re.sub(r"[^A-Z.]", "", (
                (ticker_a.get_text(strip=True) if ticker_a else ticker_td.get_text(strip=True))
                .upper().strip()
            ))
            if not ticker or len(ticker) > 6:
                continue
            company    = tds[cols.get("company", 4)].get_text(strip=True)
            insider_td = tds[cols.get("insider", 5)]
            insider_a  = insider_td.find("a")
            insider = (insider_a.get_text(strip=True) if insider_a
                       else insider_td.get_text(strip=True)).strip()
            title = get("title")
            if not is_clevel(title):
                continue
            price = clean_num(_oi_parse_num(get("price", "0")))
            qty   = clean_num(_oi_parse_num(get("qty",   "0")))
            val_s = _oi_parse_num(get("value", "0"))
            try:
                value = float(val_s) if val_s else abs(qty) * price
                if value <= 0:
                    value = abs(qty) * price
            except:
                value = abs(qty) * price
            if qty == 0 or price <= 0:
                continue
            role_abbr, role_full = extract_role(title)
            results.append({
                "ticker": ticker, "company": company, "insider": insider,
                "title": title, "role_abbr": role_abbr, "role_full": role_full,
                "price": price, "qty": f"{int(qty):,}", "value": value,
                "trade_date": trade_dt_s, "trade_time": trade_time,
                "filing_date": filing_dt_s, "filing_time": filing_time,
            })
        except:
            continue
    return results

def build_url(vl, vh, days=30):
    vh_s = str(vh) if vh > 0 else ""
    return (
        f"http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh="
        f"&fd={days}&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago="
        f"&xp=1&xs=0&xa=0&xd=0&xg=0&xf=0&xm=0&xx=0&xo=0"
        f"&vl={vl}&vh={vh_s}"
        f"&ocl=&och=&sic1=-1&sicl=100&sich=9999"
        f"&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h="
        f"&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1"
        f"&isdirector=0&is10percent=0&isother=0"
        f"&sortcol=0&cnt=500&Action=Submit"
    )

@st.cache_data(ttl=300, show_spinner=False)
def fetch_trades(vl, vh):
    r = oi_safe_fetch(build_url(vl, vh))
    if r is None:
        return [], "OpenInsider non raggiungibile (3 tentativi falliti)"
    return _parse_table(BeautifulSoup(r.text, "html.parser"),
                        datetime.now() - timedelta(days=31)), ""

@st.cache_data(ttl=600, show_spinner=False)
def enrich(ticker):
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

def save_disk(trades):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"trades": trades, "at": datetime.utcnow().isoformat()}, f)
    except:
        pass

def load_disk():
    try:
        with open(CACHE_FILE) as f:
            d = json.load(f)
        return d.get("trades", []), d.get("at", "")
    except:
        return [], ""

def inject_autorefresh(secs):
    label = next(k for k, v in REFRESH_OPTIONS.items() if v == secs)
    st.markdown(f"""
<div class="ar-bar">
  <div class="ar-left">
    <div class="ar-dot-on"></div>
    <div>
      <div class="ar-title">Live &middot; ogni {label}</div>
      <div class="ar-sub">Prossimo refresh: <span id="ar_cd" style="color:#10b981;font-family:'JetBrains Mono',monospace">--:--</span></div>
    </div>
  </div>
</div>
<script>
(function(){{
  var t={secs},left=t;
  function p(n){{return String(n).padStart(2,'0');}}
  function tick(){{
    var el=document.getElementById('ar_cd');
    if(el) el.textContent=p(Math.floor(left/60))+':'+p(left%60);
    if(left<=0){{window.location.reload();return;}}
    left--;
  }}
  tick(); setInterval(tick,1000);
  setTimeout(function(){{window.location.reload();}},{secs*1000});
}})();
</script>""", unsafe_allow_html=True)

def inject_autorefresh_off():
    st.markdown("""
<div class="ar-bar">
  <div class="ar-left">
    <div class="ar-dot-off"></div>
    <div>
      <div class="ar-title" style="color:#374151">Aggiornamento automatico disattivato</div>
      <div class="ar-sub">Premi Genera Risultati per ricaricare</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

def render_card(t, info):
    ticker    = t["ticker"]
    price     = info.get("price", 0.0)
    exchange  = info.get("exchange", "—")
    sector    = info.get("sector", "—")
    sc, sbg, sbd = sector_style(sector)
    price_str = f"${price:.2f}" if price else "—"
    co = (t.get("company", "") or "")
    co = (co[:34] + "…") if len(co) > 34 else co
    role_abbr = t.get("role_abbr", "—")
    role_full = t.get("role_full", "—")
    qty_s  = re.sub(r"[^\d,]", "", t.get("qty", ""))
    tp_s   = f"@ ${t['price']:.2f}" if t.get("price") else ""
    trade_ago  = days_ago_label(t["trade_date"])
    filing_ago = days_ago_label(t["filing_date"])
    fresh_html = '<span class="fresh-badge">NEW</span>' if is_fresh(t["filing_date"]) else ""
    st.markdown(f"""
<div class="card">
  <div class="card-top">
    <div><div class="ticker">{ticker}</div><div class="company-name">{co}</div></div>
    <span class="price-pill">{price_str}</span>
  </div>
  <div class="role-row">
    <span class="role-pill">{role_abbr}</span>
    <span class="role-full">{role_full}</span>
  </div>
  <div class="badges">
    <span class="badge b-mkt">&#x1F4CA; {exchange}</span>
    <span class="badge" style="color:{sc};background:{sbg};border:1px solid {sbd};">{sector}</span>
  </div>
  <div class="value-row">
    <div class="v-dot"></div>
    <div>
      <div class="v-amount">{fmt_usd(t['value'])}</div>
      <div class="v-detail">{qty_s} azioni {tp_s}</div>
    </div>
  </div>
  <div class="dates-grid">
    <div class="date-box">
      <div class="date-lbl">&#x1F91D; Trade Date</div>
      <div class="date-val">{t['trade_date']}</div>
      <div class="date-sub">{trade_ago}{(' &middot; ' + t['trade_time']) if t['trade_time'] else ''}</div>
    </div>
    <div class="date-box">
      <div class="date-lbl">&#x1F4CB; SEC Filing {fresh_html}</div>
      <div class="date-val">{t['filing_date']}</div>
      <div class="date-sub">{filing_ago}{(' &middot; ' + t['filing_time']) if t['filing_time'] else ''}</div>
    </div>
  </div>
  <div class="insider-row">
    <span>&#x1F464;</span>
    <span class="insider-name">{t['insider']}</span>
  </div>
</div>""", unsafe_allow_html=True)

def main():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("""
<div class="app-header">
  <div class="header-glow"></div>
  <h1>OS <span>OpenInSider</span></h1>
  <div class="header-sub"><div class="live-dot"></div>C-Level Purchases &middot; SEC Form 4</div>
</div>""", unsafe_allow_html=True)

    # Filtri valore
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="fc-label">&#x1F4B0; Valore minimo ($K)</div>', unsafe_allow_html=True)
        vl = st.slider("vl", 15, 10_000, 15, 25, label_visibility="collapsed", format="$%dK")
        st.markdown(
            f'<div class="fc-wrap"><div class="fc-label">Soglia attiva</div>'
            f'<div class="fc-value">${vl}K</div>'
            f'<div class="fc-sub">min. consigliato $15K</div></div>',
            unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="fc-label">&#x1F51D; Valore massimo ($K)</div>', unsafe_allow_html=True)
        vh = st.slider("vh", 0, 10_000, 1_000, 100, label_visibility="collapsed", format="$%dK")
        vh_lbl = "No limite" if vh == 0 else f"${vh}K"
        st.markdown(
            f'<div class="fc-wrap"><div class="fc-label">Soglia attiva</div>'
            f'<div class="fc-value">{vh_lbl}</div>'
            f'<div class="fc-sub">0 = nessun limite</div></div>',
            unsafe_allow_html=True)

    # 7 quadratini giorno
    today = datetime.utcnow().date()
    day_options   = []
    label_to_date = {}
    for i in range(7):
        d = today - timedelta(days=i)
        if   i == 0: lbl = f"Oggi  {d.day:02d}/{d.month:02d}"
        elif i == 1: lbl = f"Ieri  {d.day:02d}/{d.month:02d}"
        else:        lbl = f"{GIORNI_IT[d.weekday()]}  {d.day:02d}/{d.month:02d}"
        day_options.append(lbl)
        label_to_date[lbl] = d.strftime("%Y-%m-%d")

    st.markdown('<div class="pill-label">&#x1F4C5; Giorni &mdash; tocca per selezionare</div>',
                unsafe_allow_html=True)
    sel_day_labels = st.pills(
        "Giorni", day_options,
        selection_mode="multi",
        default=day_options[:2],
        key="day_pills",
        label_visibility="collapsed",
    )
    selected_dates = {label_to_date[l] for l in (sel_day_labels or [])}

    # Settori hardcoded — sempre visibili
    st.markdown('<div class="pill-label">&#x1F3ED; Settori &mdash; tocca per filtrare</div>',
                unsafe_allow_html=True)
    sel_sec_labels = st.pills(
        "Settori", ALL_SECTORS,
        selection_mode="multi",
        default=None,
        key="sector_pills",
        label_visibility="collapsed",
    )
    sel_sectors = sel_sec_labels or []

    # Auto-refresh
    auto_on = st.toggle("&#x1F501; Aggiornamento automatico", value=True)
    if auto_on:
        freq = st.select_slider("Frequenza", options=list(REFRESH_OPTIONS.keys()), value="5 min")
        inject_autorefresh(REFRESH_OPTIONS[freq])
    else:
        inject_autorefresh_off()

    # Pulsante Genera Risultati
    if st.button("&#x1F50D; Genera Risultati"):
        st.cache_data.clear()
        st.session_state["show_results"] = True
        st.session_state.pop("show_count", None)
        st.rerun()

    if not st.session_state.get("show_results", False):
        st.markdown(
            '<div class="empty-state"><div class="ei">&#x1F446;</div>'
            '<p>Seleziona giorni e/o settori,<br>poi premi <b>Genera Risultati</b>.</p></div>',
            unsafe_allow_html=True)
        return

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    # Fetch
    prog = st.progress(0, text="&#x23F3; Caricamento da OpenInsider...")
    trades, err = fetch_trades(vl, vh)
    prog.progress(100, text="OK"); prog.empty()

    using_stale, stale_ts = False, ""
    if trades:
        save_disk(trades)
    else:
        trades, stale_ts = load_disk()
        using_stale = bool(trades)

    if err:
        st.markdown(f'<div class="error-banner">&#x26A0;&#xFE0F; {err}</div>',
                    unsafe_allow_html=True)
    if using_stale:
        st.markdown(
            f'<div class="stale-banner">&#x1F4E6; Dati salvati ({stale_ts[:16]} UTC)</div>',
            unsafe_allow_html=True)

    if not trades:
        st.markdown(
            '<div class="empty-state"><div class="ei">&#x1F50D;</div>'
            '<p>Nessun acquisto C-Level trovato.<br>Riduci il valore minimo o riprova.</p></div>',
            unsafe_allow_html=True)
        return

    # Filtro giorni (filing_date)
    if selected_dates:
        trades = [t for t in trades if t.get("filing_date", "") in selected_dates]
    if not trades:
        st.markdown(
            '<div class="empty-state"><div class="ei">&#x1F4C5;</div>'
            '<p>Nessun filing nei giorni selezionati.<br>Seleziona altri giorni.</p></div>',
            unsafe_allow_html=True)
        return

    # Enrichment yfinance
    enriched_map = {}
    for t in trades:
        if t["ticker"] not in enriched_map:
            enriched_map[t["ticker"]] = enrich(t["ticker"])

    # Filtro settori
    if sel_sectors:
        trades = [t for t in trades
                  if enriched_map[t["ticker"]].get("sector", "—") in sel_sectors]
    if not trades:
        st.markdown(
            '<div class="empty-state"><div class="ei">&#x1F3ED;</div>'
            '<p>Nessun acquisto per i settori selezionati.</p></div>',
            unsafe_allow_html=True)
        return

    # Sort
    trades = sorted(trades, key=lambda x: x["value"], reverse=True)

    # Stats
    total = sum(t["value"] for t in trades)
    ntick = len({t["ticker"] for t in trades})
    now_s = datetime.utcnow().strftime("%d %b %Y %H:%M")
    st.markdown(f"""
<div class="stats-bar">
  <div class="stat"><div class="stat-n">{len(trades)}</div><div class="stat-l">Acquisti</div></div>
  <div class="stat"><div class="stat-n">{ntick}</div><div class="stat-l">Aziende</div></div>
  <div class="stat"><div class="stat-n">{fmt_usd(total)}</div><div class="stat-l">Totale</div></div>
  <div class="stat-ts">{now_s} UTC &middot; openinsider.com &middot; C-Level &middot; Form 4</div>
</div>""", unsafe_allow_html=True)

    # Cards
    BATCH = 12
    if "show_count" not in st.session_state:
        st.session_state.show_count = BATCH
    for trade in trades[:st.session_state.show_count]:
        render_card(trade, enriched_map[trade["ticker"]])
    remaining = len(trades) - st.session_state.show_count
    if remaining > 0:
        if st.button(f"&#x2B07;&#xFE0F;  Carica altri {min(BATCH,remaining)}  ({remaining} rimanenti)"):
            st.session_state.show_count += BATCH
            st.rerun()

if __name__ == "__main__":
    main()
