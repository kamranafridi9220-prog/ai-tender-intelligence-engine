
# ============================================================
# AI TENDER INTELLIGENCE ENGINE
# Streamlit Dashboard - Hybrid Relevance Integration
# ============================================================

import streamlit as st
import pandas as pd

from company_tender_matcher import (
    create_company,
    match_company_to_tenders
)
from live_ai_matcher import fetch_tenders
from hybrid_relevance import assess_relevance


st.set_page_config(
    page_title="AI Tender Intelligence Engine",
    page_icon="📊",
    layout="wide"
)


# ------------------------------------------------------------
# COMPANY PROFILE
# ------------------------------------------------------------

@st.cache_resource
def load_company():
    return create_company()


@st.cache_data(ttl=3600)
def load_tenders():
    return fetch_tenders()


company = load_company()

st.sidebar.title("Company Intelligence")
st.sidebar.write("**Company:**", company.name)
st.sidebar.write("**Industry:**", company.industry)
st.sidebar.write(
    "**Services:**",
    ", ".join(company.services)
)

st.sidebar.divider()

st.sidebar.caption(
    "AI-powered UK procurement opportunity discovery"
)


# ------------------------------------------------------------
# DASHBOARD HEADER
# ------------------------------------------------------------

st.title("AI Tender Intelligence Engine")

st.caption(
    "UK Public Procurement | AI-Powered Business Development"
)

st.subheader("Live Tender Discovery")


# ------------------------------------------------------------
# DISCOVERY ENGINE
# ------------------------------------------------------------

if st.button(
    "Discover Opportunities",
    type="primary"
):
    try:
        with st.spinner(
            "Retrieving and evaluating UK tender opportunities..."
        ):

            tenders = load_tenders()

            ranked = match_company_to_tenders(
                company,
                tenders
            )

            results = []

            for tender in ranked:

                assessment = assess_relevance(tender)

                results.append({
                    **tender,
                    **assessment
                })

            st.session_state["tender_results"] = results

        st.success(
            "Tender discovery and relevance assessment completed."
        )

    except Exception as error:
        st.error(
            f"Unable to complete tender discovery: {error}"
        )


# ------------------------------------------------------------
# RESULTS
# ------------------------------------------------------------

if "tender_results" in st.session_state:

    results = st.session_state["tender_results"]

    relevant = [
        item for item in results
        if item["decision"] == "RELEVANT CANDIDATE"
    ]

    review = [
        item for item in results
        if item["decision"] in [
            "MANUAL REVIEW",
            "MIXED SCOPE - REVIEW"
        ]
    ]

    rejected = [
        item for item in results
        if item["decision"] == "NOT RELEVANT"
    ]

    st.divider()

    st.subheader("Opportunity Intelligence Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Tenders Analysed",
        len(results)
    )

    col2.metric(
        "Relevant Candidates",
        len(relevant)
    )

    col3.metric(
        "Manual Review",
        len(review)
    )

    col4.metric(
        "Not Relevant",
        len(rejected)
    )

    st.divider()

    # --------------------------------------------------------
    # OPPORTUNITY FILTER
    # --------------------------------------------------------

    st.subheader("AI Tender Recommendations")

    selected = st.selectbox(
        "Filter by decision",
        [
            "Relevant Candidates",
            "Manual Review",
            "All Tenders",
            "Not Relevant"
        ]
    )

    if selected == "Relevant Candidates":
        filtered = relevant

    elif selected == "Manual Review":
        filtered = review

    elif selected == "Not Relevant":
        filtered = rejected

    else:
        filtered = results

    if filtered:

        records = []

        for item in filtered:

            records.append({
                "Tender": item.get("title", ""),
                "Decision": item["decision"],
                "Category": item["category"],
                "AI Similarity (%)": item["similarity"],
                "Matching Evidence": ", ".join(
                    item["guarding_matches"]
                ),
                "OCID": item.get("ocid", "")
            })

        df = pd.DataFrame(records)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            f"Showing {len(filtered)} tender records."
        )

    else:
        st.info(
            "No opportunities found in this category."
        )

    # --------------------------------------------------------
    # EXPLAINABLE AI DETAILS
    # --------------------------------------------------------

    st.divider()

    st.subheader("Opportunity Assessment Details")

    candidates = relevant + review

    if candidates:

        titles = [
            f"{i + 1}. {item.get('title', 'Untitled')}"
            for i, item in enumerate(candidates)
        ]

        selected_index = st.selectbox(
            "Select an opportunity for assessment",
            range(len(candidates)),
            format_func=lambda i: titles[i]
        )

        tender = candidates[selected_index]

        st.write(
            "**Tender:**",
            tender.get("title", "")
        )

        st.write(
            "**Decision:**",
            tender["decision"]
        )

        st.write(
            "**Classification:**",
            tender["category"]
        )

        st.write(
            "**Semantic Similarity:**",
            f"{tender['similarity']:.2f}%"
        )

        st.write(
            "**Positive Evidence:**",
            tender["guarding_matches"]
        )

        st.write(
            "**Potentially Unrelated Requirements:**",
            tender["unrelated_matches"]
        )

        st.write(
            "**OCID:**",
            tender.get("ocid", "")
        )

        st.warning(
            "This is a preliminary relevance assessment, "
            "not confirmation of commercial eligibility "
            "or a final Bid / No-Bid recommendation."
        )

    else:
        st.info(
            "No relevant or manual-review candidates "
            "are available for detailed assessment."
        )

else:

    st.info(
        "Click Discover Opportunities to analyse "
        "live UK procurement opportunities."
    )
