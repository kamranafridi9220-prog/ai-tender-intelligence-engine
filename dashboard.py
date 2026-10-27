"""Aegis — AI Tender Intelligence Engine | Streamlit enterprise dashboard.

Run: streamlit run dashboard.py
The page renders before optional AI modules load. Tender assessment is preliminary.
"""
from __future__ import annotations

import html
from collections import Counter
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Aegis | Tender Intelligence", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# Only style existing elements; do not hide Streamlit containers.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
html,body,[data-testid="stAppViewContainer"] {font-family:'DM Sans',sans-serif;}
[data-testid="stAppViewContainer"] {background:linear-gradient(135deg,#080f1f,#0d1b33 65%,#10213a);color:#eaf2ff;}
[data-testid="stSidebar"] {background:#0b1529;border-right:1px solid #273b56;}
h1,h2,h3 {font-family:'Manrope',sans-serif!important;letter-spacing:-.03em;color:#f4f8ff!important;}
h1 {font-weight:800!important;}
[data-testid="stMetric"] {background:linear-gradient(145deg,#172943,#111e34);border:1px solid #2b4260;border-radius:16px;padding:18px;}
[data-testid="stMetricLabel"] {color:#a6bdd9!important;}
[data-testid="stMetricValue"] {color:#f5faff!important;font-family:'Manrope',sans-serif;font-weight:800;}
[data-testid="stButton"] button[kind="primary"] {background:linear-gradient(100deg,#197cfa,#0bb8b0);color:white;border:0;border-radius:11px;font-weight:700;}
[data-testid="stButton"] button {border-radius:11px;}
.hero {border:1px solid #2e4c70;border-radius:22px;padding:29px 33px;margin:12px 0 23px;background:radial-gradient(circle at 90% 0%,#17547b,transparent 40%),linear-gradient(110deg,#173050,#101c33);}
.hero-kicker {color:#66e4d7;letter-spacing:.16em;font-size:.76rem;font-weight:800;text-transform:uppercase;}
.hero-heading {font-family:'Manrope',sans-serif;color:#f7fbff;font-size:2.4rem;line-height:1.2;font-weight:800;margin:10px 0;}
.hero-desc {color:#b7cce6;font-size:1rem;line-height:1.6;max-width:800px;}
.pill {display:inline-block;border:1px solid #367b92;border-radius:20px;color:#99e9e5;padding:5px 13px;margin-top:13px;font-size:.77rem;}
.info-card {background:#14243b;border:1px solid #2d4565;border-radius:14px;padding:16px 19px;margin:9px 0;}
.info-card small {display:block;color:#a3bbda;font-size:.78rem;text-transform:uppercase;letter-spacing:.07em;}
.info-card strong {display:block;color:#f4f9ff;font-size:1.02rem;margin-top:5px;overflow-wrap:anywhere;}
.caption-soft {color:#a9bdd9;font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

TARGET = "TARGET SECURITY CONTRACT"
REVIEW = {"SECURITY-RELATED - REVIEW", "MANUAL REVIEW", "MIXED SCOPE - REVIEW", "RELEVANT CANDIDATE"}
REJECT = "NOT RELEVANT"


def text_value(value, default="Not published"):
    if value is None or value == "" or value == []:
        return default
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(v) for v in value if v is not None and v != "") or default
    return str(value)


def parse_date(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def date_label(value):
    parsed = parse_date(value)
    return parsed.strftime("%d %b %Y, %H:%M UTC") if parsed else "Not published"


def deadline_label(value):
    parsed = parse_date(value)
    if parsed is None:
        return "Unknown"
    days = (parsed - datetime.now(timezone.utc)).total_seconds() / 86400
    if days < 0:
        return "Deadline passed"
    if days <= 7:
        return "Closing within 7 days"
    return "Open by published deadline"


def value_label(value, currency=None):
    if isinstance(value, dict):
        currency = value.get("currency") or currency
        value = value.get("amount")
    if value is None:
        return "Not published"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "Not published"
    if currency == "GBP":
        return f"£{number:,.0f}"
    return f"{number:,.0f} {currency or '(currency unverified)'}"


def card(label, value):
    st.markdown(
        '<div class="info-card"><small>' + html.escape(str(label)) + '</small><strong>'
        + html.escape(text_value(value)) + '</strong></div>', unsafe_allow_html=True
    )


def get_company():
    """Company imports happen only after a scan, not at page startup."""
    from company_tender_matcher import create_company
    return create_company()


def normalize_tender(tender):
    """Keep field names stable across versions of the enrichment module."""
    record = dict(tender)
    if not record.get("deadline"):
        period = record.get("tenderPeriod") or record.get("tender_period") or {}
        if isinstance(period, dict):
            record["deadline"] = period.get("endDate")
    if not record.get("cpv_codes"):
        record["cpv_codes"] = record.get("cpv") or []
    if not record.get("locations"):
        record["locations"] = record.get("delivery_locations") or []
    return record


def run_scan():
    from company_tender_matcher import match_company_to_tenders
    from live_ai_matcher import fetch_tenders
    from hybrid_relevance import assess_relevance

    company = get_company()
    tenders = fetch_tenders()
    ranked = match_company_to_tenders(company, tenders)
    results = []
    for tender in ranked:
        record = normalize_tender(tender)
        assessment = assess_relevance(record)
        record.update(assessment)
        results.append(record)
    return company, results


def bid_screen(record):
    decision = record.get("decision")
    if deadline_label(record.get("deadline")) == "Deadline passed":
        return "Deadline passed — verify notice"
    if decision == TARGET:
        return "Priority eligibility review"
    if decision in REVIEW:
        return "Investigate service scope"
    return "Not a target opportunity"


def build_table(records):
    rows = []
    for record in records:
        rows.append({
            "Tender": text_value(record.get("title"), "Untitled"),
            "Relevance": text_value(record.get("decision")),
            "Security services": text_value(record.get("service_groups"), "Not identified"),
            "Similarity (%)": round(float(record.get("similarity") or 0), 2),
            "Contract value": value_label(record.get("value"), record.get("currency")),
            "Locations": text_value(record.get("locations")),
            "Deadline": date_label(record.get("deadline")),
            "Screening": bid_screen(record),
            "OCID": text_value(record.get("ocid"), "Unknown"),
        })
    return pd.DataFrame(rows)


# ── Visible UI starts immediately; no model loading above this point. ──
st.markdown("""
<div class="hero">
 <div class="hero-kicker">AEGIS · PROCUREMENT COMMAND CENTRE</div>
 <div class="hero-heading">AI Tender Intelligence Engine</div>
 <div class="hero-desc">Discover and screen UK public-sector opportunities for professional security services. Separate guarding, CCTV monitoring and patrol contracts from ambiguous security-related work.</div>
 <div class="pill">LIVE UK PROCUREMENT · HUMAN-VERIFIED BID DECISIONS</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🛡️ AEGIS")
    st.caption("Enterprise procurement intelligence")
    st.divider()
    st.subheader("Company intelligence")
    st.write("**Example Security Services Ltd**")
    st.caption("Private security · London / Greater London")
    st.write("**Target services**")
    st.write("Manned guarding · Security officers · CCTV monitoring · Mobile patrols · Access control · Key holding")
    st.divider()
    st.caption("AI classifications indicate possible relevance, not procurement eligibility or an approved bid decision.")
    if st.button("Clear scan results", use_container_width=True):
        st.session_state.pop("aegis_results", None)
        st.session_state.pop("aegis_company", None)
        st.rerun()

left, right = st.columns([2.7, 1], vertical_alignment="bottom")
with left:
    st.subheader("Live opportunity discovery")
    st.markdown('<div class="caption-soft">Run a new scan of UK Find a Tender notices and rank them against your security service profile.</div>', unsafe_allow_html=True)
with right:
    scan_clicked = st.button("🚀 Run intelligence scan", type="primary", use_container_width=True)

if scan_clicked:
    try:
        with st.spinner("Fetching tenders, calculating AI similarity and classifying security relevance..."):
            company, results = run_scan()
        st.session_state["aegis_company"] = company
        st.session_state["aegis_results"] = results
        st.success(f"Scan completed: {len(results)} tender records analysed.")
    except Exception as exc:
        st.error("The scan could not be completed. The dashboard itself is working.")
        st.exception(exc)

results = st.session_state.get("aegis_results")
if results is None:
    st.divider()
    st.subheader("Executive overview")
    a, b, c, d = st.columns(4)
    a.metric("Tenders analysed", "—")
    b.metric("Target contracts", "—")
    c.metric("Require review", "—")
    d.metric("Not relevant", "—")
    st.info("The dashboard is ready. Click **Run intelligence scan** to populate the intelligence workspace.")
    st.stop()

targets = [r for r in results if r.get("decision") == TARGET]
reviews = [r for r in results if r.get("decision") in REVIEW]
rejected = [r for r in results if r.get("decision") == REJECT]
other = [r for r in results if r.get("decision") not in ({TARGET, REJECT} | REVIEW)]

st.divider()
st.subheader("Executive intelligence overview")
a, b, c, d = st.columns(4)
a.metric("Tenders analysed", len(results))
b.metric("Target security contracts", len(targets))
c.metric("Review required", len(reviews) + len(other))
d.metric("Not relevant", len(rejected))

st.subheader("Procurement analytics")
chart_left, chart_right = st.columns(2)
try:
    import plotly.express as px
    with chart_left:
        chart_data = pd.DataFrame({
            "Classification": ["Target contracts", "Review", "Not relevant"],
            "Count": [len(targets), len(reviews) + len(other), len(rejected)],
        })
        fig = px.pie(chart_data, names="Classification", values="Count", hole=0.68,
                     color="Classification", color_discrete_map={"Target contracts": "#14c8b0", "Review": "#f5b94f", "Not relevant": "#47739c"})
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=25, b=10),
                          legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig, use_container_width=True)
    with chart_right:
        top = sorted(targets + reviews, key=lambda r: float(r.get("similarity") or 0), reverse=True)[:8]
        if top:
            plot_df = pd.DataFrame({"Tender": [str(r.get("title") or "Untitled")[:42] for r in top],
                                    "Similarity (%)": [float(r.get("similarity") or 0) for r in top]})
            fig = px.bar(plot_df.iloc[::-1], x="Similarity (%)", y="Tender", orientation="h",
                         color_discrete_sequence=["#31a8ec"])
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=25, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No security-related tenders to chart in this sample.")
except ImportError:
    st.warning("Plotly charts unavailable. Check the Plotly dependency; all tender records remain accessible.")

st.divider()
st.subheader("Tender opportunity explorer")
filter_col, search_col = st.columns([1, 2])
with filter_col:
    category = st.selectbox("Relevance filter", ["Target security contracts", "Security-related / review", "All tenders", "Not relevant"])
with search_col:
    keyword = st.text_input("Search tender title or description", placeholder="e.g. guarding, CCTV, security officer")

if category == "Target security contracts":
    filtered = targets
elif category == "Security-related / review":
    filtered = reviews + other
elif category == "Not relevant":
    filtered = rejected
else:
    filtered = results
if keyword.strip():
    term = keyword.casefold().strip()
    filtered = [r for r in filtered if term in f"{r.get('title', '')} {r.get('description', '')}".casefold()]

if filtered:
    table = build_table(filtered)
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.download_button("⬇️ Export tender intelligence (CSV)", data=table.to_csv(index=False).encode("utf-8-sig"),
                       file_name="aegis_tender_intelligence.csv", mime="text/csv")
    st.caption(f"Showing {len(filtered)} of {len(results)} analysed records.")
else:
    st.info("No tenders match the selected filter in this scan. Try All tenders or run a new scan later.")

st.divider()
st.subheader("Opportunity assessment workspace")
shortlist = targets + reviews + other
if not shortlist:
    st.info("No security-related opportunities were identified in this scan.")
else:
    selected = st.selectbox("Select an opportunity", range(len(shortlist)),
                            format_func=lambda i: f"{shortlist[i].get('title', 'Untitled')} · {shortlist[i].get('decision', 'Unclassified')}")
    record = shortlist[selected]
    st.markdown(f"### {html.escape(text_value(record.get('title'), 'Untitled'))}")
    d1, d2, d3 = st.columns(3)
    with d1:
        card("Relevance decision", record.get("decision"))
        card("AI similarity", f"{float(record.get('similarity') or 0):.2f}%")
    with d2:
        card("Contract value", value_label(record.get("value"), record.get("currency")))
        card("Submission deadline", date_label(record.get("deadline")))
    with d3:
        card("Matched service groups", record.get("service_groups"))
        card("Bid screening", bid_screen(record))

    st.write("**Positive professional security evidence:**", text_value(record.get("guarding_matches"), "No specific target phrase identified"))
    st.write("**Related or ambiguous security terms:**", text_value(record.get("related_matches"), "None identified"))
    st.write("**Potentially unrelated terms:**", text_value(record.get("unrelated_matches"), "None identified"))
    st.write("**Published delivery locations:**", text_value(record.get("locations")))
    st.write("**CPV codes:**", text_value(record.get("cpv_codes")))
    st.write("**Deadline status:**", deadline_label(record.get("deadline")))
    st.write("**OCID:**", text_value(record.get("ocid")))

    with st.expander("Tender description and scope", expanded=False):
        st.write(text_value(record.get("description"), "No description provided in the retrieved record."))
        lot_desc = record.get("lot_descriptions") or []
        if lot_desc:
            st.write("**Lot descriptions**")
            for item in lot_desc:
                st.write(str(item))

    st.subheader("Commercial eligibility — verification checklist")
    checks = [
        ("Service scope", "Verify the specification requires guarding, CCTV monitoring or other services actually offered"),
        ("Geographic coverage", "Confirm exact service delivery sites; broad region codes are not proof of fit"),
        ("Contract value", "Verify published value and whether it fits company commercial thresholds"),
        ("Licensing and insurance", "Verify applicable SIA, insurance and certification requirements"),
        ("Bid documents", "Review the official notice, ITT, selection criteria and submission instructions"),
    ]
    for label, detail in checks:
        st.markdown(f"**{label} — REVIEW** · {detail}")
    st.warning("Preliminary AI screening only. No final Bid / No-Bid or commercial eligibility decision is made without reviewing official tender documents.")

st.divider()
st.caption("AEGIS · AI Tender Intelligence Engine | UK public procurement · Automated screening is not a substitute for official procurement due diligence.")
