"""AI Tender Intelligence Engine — Executive Dashboard (Lesson 26 UI)."""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
import json
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from company_tender_matcher import create_company, match_company_to_tenders
from live_ai_matcher import fetch_tenders, enrich_tender
from hybrid_relevance import assess_relevance
from eligibility_engine import evaluate_eligibility

st.set_page_config(page_title="Aegis | Tender Intelligence", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

TARGET = "TARGET SECURITY CONTRACT"
RELATED = "SECURITY-RELATED - REVIEW"
MANUAL = "MANUAL REVIEW"
REJECTED = "NOT RELEVANT"
REVIEW_LABELS = {RELATED, MANUAL, "MIXED SCOPE - REVIEW", "RELEVANT CANDIDATE"}
COLORS = {TARGET: "#30D6B0", RELATED: "#F7B955", MANUAL: "#A994FF", REJECTED: "#71809A"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --bg:#080F1D; --panel:#101B2F; --border:#24334D; --muted:#9BAAC4; --text:#ECF3FF; --teal:#30D6B0; }
html, body, [class*="css"], [data-testid="stApp"] { font-family:'DM Sans',sans-serif; }
[data-testid="stAppViewContainer"] { background:radial-gradient(circle at 88% 2%,#14274B 0%,#080F1D 43%); color:var(--text); }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebar"] { background:#0C1527; border-right:1px solid #26344C; }
.block-container { padding-top:2rem; padding-bottom:4rem; max-width:1550px; }
h1,h2,h3 { font-family:'Manrope',sans-serif!important; letter-spacing:-.035em!important; }
h1 { font-size:2.35rem!important; font-weight:800!important; }
h2 { font-size:1.45rem!important; }
h3 { font-size:1.15rem!important; }
p,li,label { color:#D5E0F0; }
[data-testid="stMetric"] { background:linear-gradient(155deg,#14243D,#0E1A2D); border:1px solid #2B3C56; border-radius:17px; padding:18px 20px; min-height:125px; }
[data-testid="stMetricLabel"] { color:#A7B8D1; font-weight:600; }
[data-testid="stMetricValue"] { color:#F4F8FF; font-family:'Manrope',sans-serif; font-weight:800; }
[data-testid="stMetricDelta"] { color:#30D6B0; }
[data-testid="stDataFrame"] { border:1px solid #263955; border-radius:14px; overflow:hidden; }
.stButton>button[kind="primary"] { background:linear-gradient(100deg,#1784E9,#11BDA8); color:white; border:0; border-radius:12px; font-weight:800; padding:.7rem 1.4rem; }
.stButton>button { border-radius:12px; }
[data-testid="stDownloadButton"] button { border:1px solid #346083; border-radius:11px; }
[data-testid="stTabs"] button { font-weight:700; }
[data-testid="stExpander"] { border:1px solid #273A55; border-radius:12px; }
.hero { background:linear-gradient(110deg,#152B4E 0%,#102B3F 62%,#10203B 100%); border:1px solid #2C4A6B; border-radius:23px; padding:29px 33px; margin-bottom:22px; position:relative; }
.eyebrow { color:#62E4D0; text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:800; }
.hero-title { color:#F7FAFF; font-family:'Manrope',sans-serif; font-weight:800; font-size:clamp(1.7rem,3vw,2.7rem); line-height:1.2; margin:10px 0; }
.hero-sub { color:#B6C9E1; font-size:.99rem; max-width:790px; line-height:1.65; }
.section-label { color:#72DDE2; font-weight:800; text-transform:uppercase; letter-spacing:.13em; font-size:.72rem; margin-top:15px; }
.glass { background:#111F34; border:1px solid #2A3C58; border-radius:15px; padding:19px 21px; margin:10px 0; }
.mini { color:#91A6C4; font-size:.82rem; }
.big { color:#F2F8FF; font-size:1.13rem; font-weight:800; font-family:'Manrope',sans-serif; }
.pill { display:inline-block; padding:6px 11px; border-radius:999px; font-size:.72rem; font-weight:800; border:1px solid currentColor; margin:3px 4px 3px 0; }
.pill-target { color:#30D6B0; background:#10372F; }
.pill-review { color:#F7B955; background:#40311F; }
.pill-muted { color:#A8B7D0; background:#202D40; }
.notice { background:#12233A; border-left:3px solid #30D6B0; border-radius:9px; padding:13px 16px; color:#C9D8EC; font-size:.9rem; }
hr { border-color:#2A3850!important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def html_safe(value):
    return escape(str(value if value is not None else ""))


def as_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (tuple, list, set)):
        return [str(x) for x in value if x is not None and str(x).strip()]
    return []


def fmt_list(value, empty="Not published"):
    values = as_list(value)
    return ", ".join(dict.fromkeys(values)) if values else empty



def dt(value):
    if not value:
        return None

    try:
        date = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if date.tzinfo is None:
            return date.replace(tzinfo=timezone.utc)

        return date.astimezone(timezone.utc)

    except (ValueError, TypeError):
        return None
