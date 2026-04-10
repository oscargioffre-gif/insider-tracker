"""OS OpenInSider v13 — OpenInsider only, password protected"""

import streamlit as st
import requests, re, json, time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

ROME = ZoneInfo("Europe/Rome")

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

# ─── COSTANTI ─────────────────────────────────────────────────────────────────
CACHE_FILE = "last_known_data.json"

# ─── EDGAR CONSTANTS ─────────────────────────────────────────────────────────
EDGAR_EFTS   = "https://efts.sec.gov/LATEST/search-index"
EDGAR_BASE   = "https://www.sec.gov/Archives/edgar/data"
EDGAR_HEADERS = {
    "User-Agent":      "OS-OpenInSider-Tracker contact@os-insider.com",
    "Accept-Encoding": "gzip, deflate",
    "Accept":          "application/json, text/xml, */*",
}
SEEN_FILE = "edgar_seen.json"   # accession IDs già processati

# ─── EDGAR: carica/salva seen set ────────────────────────────────────────────
def _load_seen() -> set:
    try:
        data = json.loads(Path(SEEN_FILE).read_text())
        return set(data.get("ids", []))
    except:
        return set()

def _save_seen(seen: set):
    try:
        # Tieni solo gli ultimi 5000 per non crescere indefinitamente
        ids = list(seen)[-5000:]
        Path(SEEN_FILE).write_text(json.dumps({"ids": ids}))
    except:
        pass

# ─── EDGAR: fetch XML di un singolo Form 4 ───────────────────────────────────
def _edgar_fetch_xml(accession_raw: str) -> str | None:
    try:
        acc_nodash = accession_raw.replace("-", "")
        cik = str(int(accession_raw.split("-")[0]))
        # Tentativo 1: filename standard
        r = requests.get(
            f"{EDGAR_BASE}/{cik}/{acc_nodash}/form4.xml",
            headers=EDGAR_HEADERS, timeout=6
        )
        if r.status_code == 200:
            return r.text
        # Tentativo 2: indice JSON
        ri = requests.get(
            f"{EDGAR_BASE}/{cik}/{acc_nodash}/{accession_raw}-index.json",
            headers=EDGAR_HEADERS, timeout=6
        )
        if ri.status_code == 200:
            for doc in ri.json().get("documents", []):
                if doc.get("type") == "4" and doc.get("document","").endswith(".xml"):
                    r2 = requests.get(
                        f"{EDGAR_BASE}/{cik}/{acc_nodash}/{doc['document']}",
                        headers=EDGAR_HEADERS, timeout=6
                    )
                    if r2.status_code == 200:
                        return r2.text
    except:
        pass
    return None

# ─── EDGAR: parse Form 4 XML → trade dict ────────────────────────────────────
def _parse_form4_xml(xml_text: str, filing_date: str, filing_time: str, vl_val: float) -> list:
    try:
        root = ET.fromstring(xml_text)
    except:
        return []

    issuer = root.find("issuer")
    if issuer is None:
        return []
    ticker  = re.sub(r"[^A-Z.]", "",
                     issuer.findtext("issuerTradingSymbol","").upper().strip())
    company = issuer.findtext("issuerName","").strip()
    if not ticker or len(ticker) > 6:
        return []

    nd_table = root.find("nonDerivativeTable")
    if nd_table is None:
        return []

    results = []
    for owner in root.findall("reportingOwner"):
        owner_id = owner.find("reportingOwnerId")
        if owner_id is None:
            continue
        insider = owner_id.findtext("rptOwnerName","").strip()
        rel     = owner.find("reportingOwnerRelationship")
        if rel is None:
            continue
        is_officer  = rel.findtext("isOfficer","0")     == "1"
        is_10pct    = rel.findtext("isTenPercentOwner","0") == "1"
        is_director = rel.findtext("isDirector","0")    == "1"
        if not (is_officer or is_10pct or is_director):
            continue
        title = rel.findtext("officerTitle","").strip()
        if is_10pct and not title:
            title = "10% Owner"
        elif is_director and not title:
            title = "Director"

        role_abbr, role_full = extract_role(title)

        for txn in nd_table.findall("nonDerivativeTransaction"):
            coding = txn.find("transactionCoding")
            if coding is None:
                continue
            if coding.findtext("transactionCode","") != "P":
                continue
            amounts = txn.find("transactionAmounts")
            if amounts is None:
                continue
            if amounts.findtext("transactionAcquiredDisposedCode/value","A") == "D":
                continue
            td_el      = txn.find("transactionDate")
            trade_date = td_el.findtext("value","") if td_el else ""
            qty_el     = amounts.find("transactionShares/value")
            price_el   = amounts.find("transactionPricePerShare/value")
            qty   = clean_num(qty_el.text   if qty_el   is not None else "0")
            price = clean_num(price_el.text if price_el is not None else "0")
            if qty == 0 or price <= 0:
                continue
            value = qty * price
            if value < vl_val:
                continue
            results.append({
                "ticker":      ticker,
                "company":     company,
                "insider":     insider,
                "title":       title,
                "role_abbr":   role_abbr,
                "role_full":   role_full,
                "price":       price,
                "qty":         f"{int(qty):,}",
                "value":       value,
                "trade_date":  trade_date,
                "trade_time":  "",
                "filing_date": filing_date,
                "filing_time": filing_time,
                "sector":      classify_sector(company),
            })
    return results

# ─── EDGAR: fetch incrementale (RSS + XML solo per nuovi filing) ──────────────
def fetch_from_edgar(vl: int) -> tuple[list, str]:
    """
    1. Interroga EFTS per Form 4 degli ultimi 30 giorni (solo metadata, ~1KB)
    2. Scarica XML solo per accession ID non ancora visti
    3. Salva seen set su disco
    Restituisce (trades, source_note)
    """
    vl_val   = vl * 1000
    today    = datetime.utcnow().date()
    start_dt = (today - timedelta(days=30)).isoformat()
    end_dt   = today.isoformat()
    seen     = _load_seen()

    # Step 1: ottieni lista accession IDs da EFTS
    all_hits = []
    from_idx = 0
    while from_idx < 2000:
        try:
            params = {
                "forms": "4",
                "dateRange": "custom",
                "startdt": start_dt,
                "enddt":   end_dt,
                "from":    str(from_idx),
                "size":    "100",
            }
            r = requests.get(EDGAR_EFTS, params=params,
                             headers=EDGAR_HEADERS, timeout=12)
            if r.status_code != 200:
                break
            data  = r.json()
            hits  = data.get("hits", {}).get("hits", [])
            if not hits:
                break
            all_hits.extend(hits)
            total     = data.get("hits",{}).get("total",{}).get("value", 0)
            from_idx += 100
            if from_idx >= total:
                break
        except:
            break

    if not all_hits:
        return [], "EDGAR EFTS non raggiungibile"

    # Step 2: filtra solo i nuovi (non già processati)
    new_hits = [h for h in all_hits if h.get("_id","") not in seen]
    if not new_hits:
        # Tutti già visti — restituisci lista vuota ma EDGAR era raggiungibile
        return [], "edgar_ok_no_new"

    # Step 3: fetch XML parallelo — solo per i nuovi
    def process_hit(hit):
        try:
            src     = hit.get("_source", {})
            acc     = hit.get("_id","")
            fd      = src.get("file_date","")
            filing_date = fd[:10] if fd else ""
            filing_time = fd[11:19] if "T" in fd else ""
            xml = _edgar_fetch_xml(acc)
            if xml:
                return acc, _parse_form4_xml(xml, filing_date, filing_time, vl_val)
            return acc, []
        except:
            return hit.get("_id",""), []

    new_trades = []
    new_seen   = set()
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(process_hit, h): h for h in new_hits}
        for fut in as_completed(futs, timeout=30):
            try:
                acc_id, trades = fut.result(timeout=10)
                new_seen.add(acc_id)
                new_trades.extend(trades)
            except:
                pass

    # Aggiorna seen set
    seen.update(new_seen)
    _save_seen(seen)

    return new_trades, "EDGAR"

OI_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
CLEVEL_KW  = ["chief executive","ceo","chief financial","cfo","chief operating",
               "coo","chairman","cob","general counsel","gc","vice president",
               "vp","president","pres","chief ","officer"]
EXCLUDE_KW = ["beneficial owner"]

REFRESH_OPTIONS = {"5 min":300,"10 min":600,"15 min":900,"30 min":1800}
GIORNI_IT = ["Lun","Mar","Mer","Gio","Ven","Sab","Dom"]


# ─── SETTORI (classificazione per nome azienda — no API esterne) ──────────────
SECTOR_KEYWORDS = {
    "Semiconductors": [
        "semiconductor","semi ","microchip","integrated circuit","chip ",
        "wafer","fabless","foundry","photovoltaic","solar cell",
        "nvidia","intel","amd","qualcomm","broadcom","texas instrument",
        "applied material","lam research","kla ","asml","marvell","skyworks",
        "qorvo","on semi","onsemi","wolfspeed","lattice","maxim","analog device",
        "microchip tech","silicon lab","monolithic","photronics","axcelis",
        "entegris","cabot micro","kulicke","amkor","cohu","ichor","allegro",
        "power integr","vishay","diodes inc","semtech","indie semi","ceva",
        "magnachip","tower semi","aehr","atomica","pdf solution","ii-vi",
        "coherent","wolfspeed","impinj","macom","inphi","form factor","acm research",
        "cxmt","rapidus","soitec","iqe","sitime","indie","ultra clean","ichor",
    ],
    "Biotech": [
        "biotech","biopharma","bioscience","biomed","therapeut","pharma ",
        "pharmaceutical","drug inc","drug corp","genomic","oncolog",
        "cell therapy","gene therapy","immuno","vaccine","antibod","peptide",
        "clinical stage","clinical-stage","preclinical","biologics","biosimilar",
        "life sciences","lifesciences","molecular","proteom","transcriptom",
        "crispr","rna ","mrna","sirna","oligonucleotide","adeno","aav ",
        "abbvie","pfizer","merck","lilly","amgen","gilead","regeneron",
        "vertex","moderna","biontech","novavax","biogen","alexion","celgene",
        "myovant","natera","guardant","insulet","dexcom","vivani",
        "orasure","haemonetics","harvard bioscience","meridian bio",
        "relay therap","protagonist","arrowhead","athenex","atara",
        "nuvation","arcus","arcutis","omeros","atea","chembio","neogen",
        "medtronic","hologic","becton","baxter","zimmer","edwards life",
        "abiomed","resmed","accuray","enovis","globus","alphatec",
        "intuitive surgical","natus","invacare","labcorp","quest diag",
    ],
    "Technology": [
        "tech","software","cloud","cyber","digital","platform","saas","data",
        "artificial intel","machine learn","network","internet","computing",
        "information","solutions","systems","analytics","automation","robotics",
        "fintech","insurtech","edtech","proptech","legaltech","regtech",
        "microsoft","apple","google","alphabet","meta","amazon","salesforce",
        "servicenow","workday","adobe","oracle","sap","ibm","cisco","palo alto",
        "crowdstrike","fortinet","zscaler","okta","datadog","snowflake","mongodb",
        "elastic","twilio","zendesk","hubspot","veeva","paycom","paylocity",
        "toast","braze","appfolio","duolingo","coursera","box ","dropbox",
        "zoom","slack","asana","monday","freshworks","zenvia","sinch",
        "switch","commvault","progress software","open text","nuance",
        "j2 global","ziff davis","iac ","angi","dotdash","ask.com",
        "quantum","quanta","coherent","itron","trimble","calix","viavi",
        "ciena","infinera","adtran","sycamore","ribbon","comverse","sonus",
    ],
    "Industrials": [
        "industrial","manufactur","aerospace","defense","engineering",
        "construction","machinery","equipment","automotive","logistics",
        "transport","aviation","railroad","shipping","freight","supply chain",
        "auto ","vehicle","truck","trailer","crane","pump","valve","pipe",
        "steel","aluminum","metal","alloy","casting","forging","welding",
        "caterpillar","deere","honeywell","lockheed","raytheon","northrop",
        "boeing","parker hannifin","emerson","rockwell","eaton","dover",
        "illinois tool","ametek","roper","xylem","kennametal","timken",
        "graco","nordson","lincoln electric","flowserve","curtiss","hexcel",
        "spirit aero","heico","transdigm","moog","woodward","kaman","crane",
        "watsco","aaon","comfort systems","insteel","mueller","watts",
        "ducommun","triumph","moog","mercury system","kratos","aerojet",
        "axon","l3harris","bae","textron","general dynamics","huntington",
        "naval","leidos","saic","booz allen","science application","maximus",
        "amscan","ametek","watts","circor","enpro","esab","haynes","kaiser",
        "omega flex","thermon","watts water","zurn","core molding",
    ],
}

# Ordine di priorità: più specifico → meno specifico
_SECTOR_PRIORITY = ["Semiconductors", "Biotech", "Industrials", "Technology"]

def classify_sector(company: str) -> str:
    """Classifica il settore dal nome azienda usando keyword matching.
    Priorità: Semiconductors > Healthcare > Industrials > Technology
    (evita che 'tech' in 'Technologies' sovrascriva settori più specifici)
    """
    if not company:
        return "—"
    cl = company.lower()
    for sector in _SECTOR_PRIORITY:
        keywords = SECTOR_KEYWORDS.get(sector, [])
        if any(kw in cl for kw in keywords):
            return sector
    return "—"

SECTOR_COLORS = {
    "Semiconductors":  ("#f59e0b","rgba(245,158,11,.12)","rgba(245,158,11,.3)"),
    "Biotech":      ("#34d399","rgba(52,211,153,.12)","rgba(52,211,153,.3)"),
    "Technology":      ("#818cf8","rgba(99,102,241,.12)","rgba(99,102,241,.3)"),
    "Industrials":     ("#a78bfa","rgba(167,139,250,.12)","rgba(167,139,250,.3)"),
}
FILTER_SECTORS = list(SECTOR_COLORS.keys())

def sector_badge_style(sector: str) -> tuple:
    return SECTOR_COLORS.get(sector, ("#6b7280","rgba(107,114,128,.12)","rgba(107,114,128,.3)"))


# SIC ranges ufficiali SEC per ogni settore — usati per fetch settoriale su OI
# Fonte: https://www.sec.gov/info/edgar/siccodes.htm
# SIC ranges per fetch settoriale su OpenInsider — fonte SEC ufficiale
# Biotech usa TUTTI i range healthcare/biotech/pharma/medical per copertura totale
SECTOR_SIC_RANGES = {
    "Biotech": [
        # Pharma & biologics
        (2830, 2836),   # pharmaceutical preparations, biologicals
        (2860, 2869),   # industrial chemicals (excl. basic) — molte biotech
        # Medical devices & instruments
        (3826, 3826),   # laboratory analytical instruments
        (3827, 3827),   # optical instruments
        (3841, 3841),   # surgical & medical instruments
        (3842, 3842),   # orthopedic, prosthetic, surgical appliances
        (3843, 3843),   # dental equipment & supplies
        (3844, 3844),   # x-ray apparatus & tubes
        (3845, 3845),   # electromedical equipment
        (3851, 3851),   # ophthalmic goods
        # Wholesale healthcare
        (5047, 5047),   # medical & hospital equipment wholesale
        (5122, 5122),   # drugs, drug proprietaries wholesale
        # Health services
        (8000, 8011),   # offices & clinics of doctors
        (8020, 8049),   # offices of other health practitioners
        (8050, 8059),   # nursing & personal care
        (8060, 8069),   # hospitals
        (8070, 8079),   # medical & dental labs
        (8080, 8099),   # health services NEC
        # Biotech R&D
        (8731, 8731),   # commercial physical & biological research
        (8734, 8734),   # testing laboratories
        (8099, 8099),   # health services NEC
    ],
    "Semiconductors": [
        (3674, 3674),   # semiconductors & related devices (SIC core)
        (3670, 3679),   # electronic components broad
        (3825, 3826),   # instruments for measuring electronic
        (3559, 3559),   # special industry machinery (includes chip equipment)
    ],
    "Technology": [
        (7372, 7372),   # prepackaged software
        (7371, 7371),   # computer programming services
        (7373, 7374),   # computer integrated systems & data processing
        (7375, 7379),   # computer related services NEC
        (3570, 3579),   # computer & office equipment
        (3669, 3669),   # communications equipment NEC
        (4813, 4813),   # telephone communications
        (4899, 4899),   # communications services NEC
    ],
    "Industrials": [
        (3400, 3499),   # fabricated metal products
        (3500, 3599),   # industrial machinery & equipment
        (3710, 3716),   # motor vehicles & equipment
        (3720, 3729),   # aircraft & parts
        (3730, 3743),   # ship building, railroad equipment
        (3760, 3769),   # guided missiles & space vehicles
        (4400, 4499),   # water transportation
        (4500, 4599),   # air transportation
        (4210, 4215),   # trucking & warehousing
    ],
}

# ─── ROLE EXTRACTOR ───────────────────────────────────────────────────────────
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
    if not title or not title.strip(): return "INS","Insider"
    tl = title.lower().strip()
    # 10% owner check
    if "10%" in tl and "owner" in tl: return "10%","10% Owner"
    for abbr,kws in _ROLE_MAP:
        if kws and any(k in tl for k in kws): return abbr,title.strip()
    # Titolo non mappato — mostra i primi 8 caratteri
    return title.strip()[:8].upper(),title.strip()

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def is_clevel(title):
    # OpenInsider filtra già per ruolo tramite i flag dell'URL.
    # Accettiamo tutto — Director, Officer, 10%own, Other inclusi.
    return True

def clean_num(s):
    try: return float(re.sub(r"[^\d.]","",str(s)) or "0")
    except: return 0.0

def fmt_usd(v):
    if v>=1_000_000: return f"${v/1_000_000:.2f}M"
    if v>=1_000:     return f"${v/1_000:.0f}K"
    return f"${v:.0f}"



def days_ago_label(ds):
    try:
        diff=(datetime.now(ROME).date()-datetime.strptime(ds,"%Y-%m-%d").date()).days
        return "Oggi" if diff==0 else("Ieri" if diff==1 else f"{diff}gg fa")
    except: return ""

def is_fresh(ds):
    try: return (datetime.now(ROME).date()-datetime.strptime(ds,"%Y-%m-%d").date()).days<=1
    except: return False

# ─── OPENINSIDER FETCH ────────────────────────────────────────────────────────
def oi_safe_fetch(url, retries=3, delay=4):
    for attempt in range(1,retries+1):
        try:
            r = requests.get(url,headers=OI_HEADERS,timeout=20)
            if r.status_code==200: return r
        except: pass
        if attempt<retries: time.sleep(delay*attempt)
    return None

def build_url(vl, vh, days=10):
    vh_s = str(vh) if vh>0 else ""
    return (
        f"http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh="
        f"&fd={days}&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago="
        f"&xp=1&xs=0&xa=0&xd=0&xg=0&xf=0&xm=0&xx=0&xo=0"
        f"&vl={vl}&vh={vh_s}"
        f"&ocl=&och=&sic1=-1&sicl=100&sich=9999"
        f"&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h="
        f"&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1"
        f"&isdirector=1&is10percent=1&isother=1"
        f"&sortcol=0&cnt=1000&Action=Submit"
    )

def _detect_columns(header_row):
    cols={}
    for i,th in enumerate(header_row.find_all(["th","td"])):
        txt=th.get_text(strip=True).lower()
        if "trade" in txt and "date" in txt and "trade_date" not in cols: cols["trade_date"]=i
        elif "filing" in txt and "date" in txt and "filing_date" not in cols: cols["filing_date"]=i
        elif "ticker" in txt and "ticker" not in cols: cols["ticker"]=i
        elif "company" in txt and "company" not in cols: cols["company"]=i
        elif "insider" in txt and "insider" not in cols: cols["insider"]=i
        elif "title" in txt and "title" not in cols: cols["title"]=i
        elif ("trade type" in txt or txt=="type") and "type" not in cols: cols["type"]=i
        elif "price" in txt and "price" not in cols: cols["price"]=i
        elif "qty" in txt and "qty" not in cols: cols["qty"]=i
        elif "value" in txt and "value" not in cols: cols["value"]=i
    for k,v in {"filing_date":1,"trade_date":2,"ticker":3,"company":4,
                "insider":5,"title":6,"type":7,"price":8,"qty":9,"value":12}.items():
        if k not in cols: cols[k]=v
    return cols

def _find_table(soup):
    for t in soup.find_all("table"):
        if any(c in " ".join(t.get("class",[])) for c in ["tinytable","sortable"]): return t
    tables=soup.find_all("table")
    return max(tables,key=lambda t:len(t.find_all("tr")),default=None) if tables else None

def _parse_table(soup, cutoff):
    table=_find_table(soup)
    if not table: return []
    all_rows=table.find_all("tr")
    if not all_rows: return []
    cols=_detect_columns(all_rows[0])
    results=[]
    for tr in all_rows[1:]:
        tds=tr.find_all("td")
        if len(tds)<8: continue
        try:
            def get(key,default=""):
                idx=cols.get(key,-1)
                if idx<0 or idx>=len(tds): return default
                return tds[idx].get_text(strip=True)
            ttype=get("type")
            if (ttype.split(" ")[0].upper() if ttype else "")!="P": continue
            trade_raw=get("trade_date"); filing_raw=get("filing_date")
            trade_dt_s=trade_raw[:10] if trade_raw else ""
            filing_dt_s=filing_raw[:10] if filing_raw else ""
            trade_time=trade_raw[10:].strip() if len(trade_raw)>10 else ""
            filing_time=filing_raw[10:].strip() if len(filing_raw)>10 else ""
            # cutoff opzionale sulla trade_date (usiamo filing_date come filtro primario nell'UI)
            if cutoff and trade_dt_s:
                try:
                    if datetime.strptime(trade_dt_s,"%Y-%m-%d") < cutoff: continue
                except ValueError:
                    pass  # se la data è malformata, non scartare
            ticker_td=tds[cols.get("ticker",3)]; ticker_a=ticker_td.find("a")
            ticker=re.sub(r"[^A-Z.]","",((ticker_a.get_text(strip=True) if ticker_a
                          else ticker_td.get_text(strip=True)).upper().strip()))
            if not ticker or len(ticker)>6: continue
            company=tds[cols.get("company",4)].get_text(strip=True)
            insider_td=tds[cols.get("insider",5)]; insider_a=insider_td.find("a")
            insider=(insider_a.get_text(strip=True) if insider_a
                     else insider_td.get_text(strip=True)).strip()
            title=get("title")
            role_abbr, role_full = extract_role(title)
            price = clean_num(re.sub(r"[$,+\s]","",get("price","0").strip()))
            qty   = clean_num(re.sub(r"[$,+\s]","",get("qty",  "0").strip()))
            val_s = re.sub(r"[$,+\s]","",get("value","0").strip())
            # Calcola value: prima dalla colonna Value, poi da qty*price
            try:
                value = float(val_s) if val_s and val_s not in ("0","") else 0.0
            except:
                value = 0.0
            if value <= 0 and qty > 0 and price > 0:
                value = abs(qty) * price
            if value <= 0:
                continue  # scarta solo se non riusciamo a calcolare nessun valore
            results.append({
                "ticker":ticker,"company":company,"insider":insider,
                "title":title,"role_abbr":role_abbr,"role_full":role_full,
                "price":price,"qty":f"{int(qty):,}","value":value,
                "trade_date":trade_dt_s,"trade_time":trade_time,
                "filing_date":filing_dt_s,"filing_time":filing_time,
                "sector":classify_sector(company),
            })
        except: continue
    return results

def _build_sic_url(vl: int, sicl: int, sich: int, days: int = 10) -> str:
    """URL OpenInsider filtrato per SIC range — fonte autorevole per settore."""
    return (
        f"http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh="
        f"&fd={days}&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago="
        f"&xp=1&xs=0&xa=0&xd=0&xg=0&xf=0&xm=0&xx=0&xo=0"
        f"&vl={vl}&vh="
        f"&ocl=&och=&sic1=-1&sicl={sicl}&sich={sich}"
        f"&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h="
        f"&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1"
        f"&isdirector=1&is10percent=1&isother=1"
        f"&sortcol=0&cnt=500&Action=Submit"
    )

@st.cache_data(ttl=120, show_spinner=False)
def fetch_trades(vl, vh):
    """
    Fetch principale: 1 chiamata OpenInsider (tutti i settori).
    Per ogni settore con SIC ranges, fetch parallelo addizionale
    che usa i codici SIC SEC come fonte autoritativa.
    Merge + dedup: zero trade persi.
    Cache 2 min.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    cutoff = datetime.now() - timedelta(days=31)
    vl_val = vl * 1000

    # ── Fetch principale ──────────────────────────────────────────────────────
    merged: dict = {}
    r = oi_safe_fetch(build_url(vl, vh))
    if r is None and not SECTOR_SIC_RANGES:
        return [], "OpenInsider non raggiungibile"
    if r is not None:
        soup = BeautifulSoup(r.text, "lxml")
        for t in _parse_table(soup, cutoff):
            if t["value"] >= vl_val:
                key = (t["ticker"], t["insider"], t["trade_date"], round(t["value"], -2))
                merged[key] = t

    # ── Fetch SIC paralleli (un fetch per range) ──────────────────────────────
    def _fetch_sic_range(sector: str, sicl: int, sich: int) -> list:
        try:
            r2 = oi_safe_fetch(_build_sic_url(vl, sicl, sich), retries=2, delay=2)
            if r2 is None:
                return []
            rows = _parse_table(BeautifulSoup(r2.text, "lxml"), cutoff)
            result = []
            for t in rows:
                if t["value"] >= vl_val:
                    t["sector"] = sector  # SIC = fonte autorevole
                    result.append(t)
            return result
        except:
            return []

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = []
        for sector, ranges in SECTOR_SIC_RANGES.items():
            for sicl, sich in ranges:
                futs.append(ex.submit(_fetch_sic_range, sector, sicl, sich))
        for fut in as_completed(futs, timeout=30):
            try:
                for t in fut.result(timeout=12):
                    key = (t["ticker"], t["insider"], t["trade_date"], round(t["value"], -2))
                    if key in merged:
                        # SIC sovrascrive keyword classification — più affidabile
                        merged[key]["sector"] = t["sector"]
                    else:
                        merged[key] = t
            except:
                pass

    if not merged:
        return [], "OpenInsider non raggiungibile (tutti i tentativi falliti)"

    return list(merged.values()), ""

# ─── DISK CACHE ───────────────────────────────────────────────────────────────
def save_disk(trades):
    try:
        with open(CACHE_FILE,"w") as f:
            json.dump({"trades":trades,"at":datetime.now(ROME).isoformat()},f)
    except: pass

def load_disk():
    try:
        with open(CACHE_FILE) as f: d=json.load(f)
        return d.get("trades",[]),d.get("at","")
    except: return [],""

# ─── AUTO-REFRESH ─────────────────────────────────────────────────────────────
def inject_autorefresh(secs):
    label=next(k for k,v in REFRESH_OPTIONS.items() if v==secs)
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




# ─── CARD ────────────────────────────────────────────────────────────────────
def render_card(t):
    ticker    = t["ticker"]
    price_str = f"${t['price']:.2f}" if t.get("price") else "—"
    co        = (t.get("company","") or ""); co=(co[:34]+"…") if len(co)>34 else co
    role_abbr = t.get("role_abbr","—"); role_full=t.get("role_full","—")
    qty_s     = re.sub(r"[^\d,]","",t.get("qty",""))
    tp_s      = f"@ ${t['price']:.2f}" if t.get("price") else ""
    trade_ago = days_ago_label(t["trade_date"])
    filing_ago= days_ago_label(t["filing_date"])
    fresh_html= '<span class="fresh-badge">NEW</span>' if is_fresh(t["filing_date"]) else ""
    sector = t.get("sector","—")
    sc,sbg,sbd = sector_badge_style(sector)
    sector_badge_html = (
        f'<span class="badge" style="color:{sc};background:{sbg};border:1px solid {sbd};'
        f'font-size:.72rem;font-weight:700;padding:2px 9px;border-radius:20px;">{sector}</span>'
        if sector in SECTOR_COLORS else "")
    st.markdown(f"""
<div class="card">
  <div class="card-top">
    <div><div class="ticker">{ticker}</div><div class="company-name">{co}</div></div>
    <span class="price-pill">{price_str}</span>
  </div>
  <div class="role-row">
    <span class="role-pill">{role_abbr}</span>
    <span class="role-full">{role_full}</span>
    {sector_badge_html}
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
      <div class="date-sub">{trade_ago}{(' &middot; '+t['trade_time']) if t['trade_time'] else ''}</div>
    </div>
    <div class="date-box">
      <div class="date-lbl">&#x1F4CB; SEC Filing {fresh_html}</div>
      <div class="date-val">{t['filing_date']}</div>
      <div class="date-sub">{filing_ago}{(' &middot; '+t['filing_time']) if t['filing_time'] else ''}</div>
    </div>
  </div>
  <div class="insider-row"><span>&#x1F464;</span><span class="insider-name">{t['insider']}</span></div>
</div>""", unsafe_allow_html=True)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("""
<div class="app-header">
  <div class="header-glow"></div>
  <h1>OS <span>OpenInSider</span></h1>
  <div class="header-sub"><div class="live-dot"></div>C-Level + 10% Owner &middot; SEC Form 4</div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="fc-label">&#x1F4B0; Valore minimo acquisto ($K)</div>', unsafe_allow_html=True)
    vl = st.slider("vl", 15, 10_000, 15, 25, label_visibility="collapsed", format="$%dK")
    st.markdown(
        f'<div class="fc-wrap"><div class="fc-label">Soglia attiva</div>'
        f'<div class="fc-value">${vl}K</div>'
        f'<div class="fc-sub">min. consigliato $15K — nessun limite massimo</div></div>',
        unsafe_allow_html=True)
    vh = 0  # nessun limite massimo

    last_vl = st.session_state.get("last_vl")
    if last_vl is not None and last_vl != vl:
        st.session_state.pop("show_results",None)
        st.session_state.pop("show_count",None)
    st.session_state["last_vl"] = vl

    today         = datetime.now(ROME).date()
    day_options   = []
    label_to_date = {}
    for i in range(7):
        d = today - timedelta(days=i)
        if   i==0: lbl = f"Oggi  {d.day:02d}/{d.month:02d}"
        elif i==1: lbl = f"Ieri  {d.day:02d}/{d.month:02d}"
        else:      lbl = f"{GIORNI_IT[d.weekday()]}  {d.day:02d}/{d.month:02d}"
        day_options.append(lbl)
        label_to_date[lbl] = d.strftime("%Y-%m-%d")

    st.markdown('<div class="pill-label">&#x1F4C5; Giorni &mdash; tocca per selezionare</div>',
                unsafe_allow_html=True)
    sel_day_labels = st.pills("Giorni", day_options, selection_mode="multi",
                               default=day_options[:2], key="day_pills",
                               label_visibility="collapsed")
    selected_dates = {label_to_date[l] for l in (sel_day_labels or [])}



    st.markdown('<div class="pill-label">&#x1F3ED; Settori &mdash; tocca per filtrare</div>',
                unsafe_allow_html=True)
    sel_sec_labels = st.pills("Settori", FILTER_SECTORS, selection_mode="multi",
                               default=None, key="sector_pills",
                               label_visibility="collapsed")
    sel_sectors = sel_sec_labels or []

    auto_on = st.toggle("&#x1F501; Aggiornamento automatico", value=True)
    if auto_on:
        freq = st.select_slider("Frequenza", options=list(REFRESH_OPTIONS.keys()), value="5 min")
        inject_autorefresh(REFRESH_OPTIONS[freq])
    else:
        inject_autorefresh_off()

    if st.button("&#x1F50D; Genera Risultati"):
        st.cache_data.clear()
        st.session_state["show_results"] = True
        st.session_state.pop("show_count",None)
        st.rerun()

    if not st.session_state.get("show_results", False):
        st.markdown(
            '<div class="empty-state"><div class="ei">&#x1F446;</div>'
            '<p>Seleziona giorni e/o settori,<br>poi premi <b>Genera Risultati</b>.</p></div>',
            unsafe_allow_html=True)
        return

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    prog = st.progress(0, text="&#x23F3; Caricamento da OpenInsider...")
    trades, err = fetch_trades(vl, vh)
    data_source = "OpenInsider"
    prog.progress(100, text="&#x2705; Fatto"); prog.empty()

    using_stale, stale_ts = False, ""
    if trades: save_disk(trades)
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
            '<p>Nessun acquisto trovato.<br>Riduci il valore minimo o riprova.</p></div>',
            unsafe_allow_html=True)
        return

    # Contatore: tutti i 7 giorni dell'app accesi, nessun settore
    all_7_dates = set(label_to_date.values())
    trades_7d   = [t for t in trades if t.get("filing_date","") in all_7_dates]
    raw_count   = len(trades_7d)
    raw_tickers = len({t["ticker"] for t in trades_7d})
    st.markdown(
        f'<div style="font-size:.73rem;color:#4b5563;text-align:center;'
        f'padding:.4rem .5rem .25rem;margin-bottom:.4rem;letter-spacing:.02em;">'
        f'&#x1F4E1; <b style="color:#8b949e">7 giorni · tutti i settori</b> &rarr; '
        f'<b style="color:#10b981">{raw_count}</b> acquisti · '
        f'<b style="color:#10b981">{raw_tickers}</b> titoli '
        f'(soglia ${vl}K)'
        f'</div>',
        unsafe_allow_html=True)

    if selected_dates:
        trades = [t for t in trades if t.get("filing_date","") in selected_dates]
    if not trades:
        st.markdown(
            '<div class="empty-state"><div class="ei">&#x1F4C5;</div>'
            '<p>Nessun filing nei giorni selezionati.<br>Seleziona altri giorni.</p></div>',
            unsafe_allow_html=True)
        return



    # Filtro settori — SIC fetch già garantisce copertura totale
    if sel_sectors:
        trades = [t for t in trades if t.get("sector","—") in sel_sectors]
    if not trades:
        st.markdown(
            '<div class="empty-state"><div class="ei">&#x1F3ED;</div>'
            '<p>Nessun acquisto per i settori selezionati.<br>'
            'Deseleziona un settore o aggiungi altri giorni.</p></div>',
            unsafe_allow_html=True)
        return

    trades = sorted(trades, key=lambda x: (x["filing_date"], x["filing_time"]), reverse=True)

    total = sum(t["value"] for t in trades)
    ntick = len({t["ticker"] for t in trades})
    now_s = datetime.now(ROME).strftime("%d %b %Y %H:%M")
    st.markdown(f"""
<div class="stats-bar">
  <div class="stat"><div class="stat-n">{len(trades)}</div><div class="stat-l">Acquisti</div></div>
  <div class="stat"><div class="stat-n">{ntick}</div><div class="stat-l">Aziende</div></div>
  <div class="stat"><div class="stat-n">{fmt_usd(total)}</div><div class="stat-l">Totale</div></div>
  <div class="stat-ts">{now_s} IT &middot; OpenInsider &middot; C-Level + 10% Owner + Director &middot; {data_source} &middot; Form 4</div>
</div>""", unsafe_allow_html=True)

    BATCH = 12
    if "show_count" not in st.session_state:
        st.session_state.show_count = BATCH
    for trade in trades[:st.session_state.show_count]:
        render_card(trade)
    remaining = len(trades) - st.session_state.show_count
    if remaining > 0:
        if st.button(f"&#x2B07;&#xFE0F;  Carica altri {min(BATCH,remaining)}  ({remaining} rimanenti)"):
            st.session_state.show_count += BATCH
            st.rerun()

if __name__ == "__main__":
    main()