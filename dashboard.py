"""AI Tender Intelligence Engine — Enterprise Streamlit Dashboard.

Run with: streamlit run dashboard.py
The UI loads before optional AI modules are imported.
"""
from __future__ import annotations

import html
import io
from collections import Counter
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Aegis | Tender Intelligence", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# Keep CSS limited to typography and visual styling. Never hide Streamlit containers.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
html, body, [class*="css"], [data-testid="stAppViewContainer"] {font-family:'DM Sans',sans-serif;}
[data-testid="stAppViewContainer"] {background:linear-gradient(140deg,#090f20 0%,#0d1830 58%,#101d32 100%);color:#eaf2ff;}
[data-testid="stSidebar"] {background:#0b1428;border-right:1px solid #24354e;}
h1,h2,h3 {font-family:'Manrope',sans-serif!important;letter-spacing:-.035em;}
h1 {font-size:2.55rem!important;font-weight:800!important;color:#f6f9ff!important;}
h2 {font-size:1.5rem!important;color:#eaf2ff!important;}
h3 {color:#eaf2ff!important;}
[data-testid="stMetric"] {background:linear-gradient(150deg,#15243e,#111b31);border:1px solid #2a3e5d;border-radius:16px;padding:20px 18px;}
[data-testid="stMetricLabel"] {color:#a6b9d6!important;}
[data-testid="stMetricValue"] {color:#f3f8ff!important;font-family:'Manrope',sans-serif;font-weight:800;}
[data-testid="stButton"] button[kind="primary"] {background:linear-gradient(100deg,#1689f7,#11b9b5);border:0;color:white;font-weight:700;border-radius:10px;}
[data-testid="stButton"] button {border-radius:10px;}
[data-testid="stDataFrame"] {border:1px solid #2a3e5d;border-radius:12px;overflow:hidden;}
.hero {border:1px solid #2a4467;border-radius:22px;padding:30px 34px;margin:10px 0 24px;background:radial-gradient(circle at 90% 10%,#194c6e 0%,transparent 38%),linear-gradient(110deg,#152d50,#101b33);}
.eyebrow {color:#56d9d3;font-size:.77rem;letter-spacing:.17em;font-weight:800;text-transform:uppercase;}
.hero-title {font-family:'Manrope',sans-serif;font-size:2.25rem;line-height:1.2;font-weight:800;color:#f7faff;margin:12px 0;}
.hero-sub {color:#b6c8e2;font-size:1rem;max-width:750px;line-height:1.65;}
.tag {display:inline-block;border:1px solid #2b6680;color:#8ce4e3;border-radius:20px;padding:5px 12px;font-size:.75rem;margin-top:14px;}
.section-caption {color:#a9bbd4;font-size:.93rem;margin-top:-7px;margin-bottom:15px;}
.detail-card {border:1px solid #2c405d;border-radius:14px;background:#111e34;padding:17px 20px;margin:12px 0;}
.detail-label {color:#8da7c9;font-size:.79rem;text-transform:uppercase;letter-spacing:.08em;}
.detail-value {color:#edf5ff;font-weight:700;font-size:1.02rem;margin-top:5px;}
.footer-note {font-size:.82rem;color:#92a8c6;line-height:1.6;}
</style>
""", unsafe_allow_html=True)

TARGET = "TARGET SECURITY CONTRACT"
REVIEW = {"SECURITY-RELATED - REVIEW", "MANUAL REVIEW", "MIXED SCOPE - REVIEW", "RELEVANT CANDIDATE"}
REJECT = "NOT RELEVANT"


def safe_text(value, default="Not published"):
    if value is None or value == "" or value == []:
        return default
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(x) for x in value if x) or default
    if isinstance(value, dict):
        return str(value)
    return str(value)


def parse_date(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def date_label(value):
    dt = parse_date(value)
    return dt.strftime("%d %b %Y · %H:%M UTC") if dt else "Not published"


def deadline_label(value):
    dt = parse_date(value)
    if not dt:
        return "Unknown"
    delta = (dt - datetime.now(timezone.utc)).total_seconds()
    if delta < 0:
        return "Deadline passed"
    if delta < 7 * 86400:
        return "Closing within 7 days"
    return "Open (based on deadline)"


def value_label(value, currency="GBP"):
    if isinstance(value, dict):
        currency = value.get("currency") or currency
        value = value.get("amount")
    try:
        if value is None:
            return "Not published"
