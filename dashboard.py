
# ============================================================
# AI TENDER INTELLIGENCE ENGINE
# Dashboard - Hybrid Relevance + Commercial Eligibility
# ============================================================

import streamlit as st
import pandas as pd

from company_tender_matcher import (
    create_company,
    match_company_to_tenders
)
from live_ai_matcher import fetch_tenders
from hybrid_relevance import assess_relevance
from eligibility_engine import evaluate_eligibility


st.set_page_config(
    page_title="AI Tender Intelligence Engine",
    page_icon="📊",
    layout="wide"
)


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
    "UK public procurement decision intelligence"
)

st.title("AI Tender Intelligence Engine")
st.caption(
    "UK Public Procurement | AI-Powered Business Development"
)

st.subheader("Live Tender Discovery")


if st.button("Discover Opportunities", type="primary"):
    try:
        with st.spinner(
            "Retrieving and evaluating live UK tenders..."
        ):
            tenders = load_tenders()

            ranked = match_company_to_tenders(
                company, tenders
            )

            results = []

            for tender in ranked:
                relevance = assess_relevance(tender)

                results.append({
                    **tender,
                    **relevance
                })

            st.session_state["tender_results"] = results

        st.success(
            "Tender discovery and relevance assessment completed."
        )

    except Exception as error:
        st.error(f"Discovery failed: {error}")


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

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Tenders Analysed", len(results))
    c2.metric("Relevant Candidates", len(relevant))
    c3.metric("Manual Review", len(review))
    c4.metric("Not Relevant", len(rejected))

    st.divider()
    st.subheader("AI Tender Recommendations")

    selected_filter = st.selectbox(
        "Filter by relevance decision",
        [
            "Relevant Candidates",
            "Manual Review",
            "All Tenders",
            "Not Relevant"
        ]
    )

    if selected_filter == "Relevant Candidates":
        filtered = relevant
    elif selected_filter == "Manual Review":
        filtered = review
    elif selected_filter == "Not Relevant":
        filtered = rejected
    else:
        filtered = results

    if filtered:
        rows = []

        for item in filtered:
            rows.append({
                "Tender": item.get("title", ""),
                "Relevance Decision": item["decision"],
                "Category": item["category"],
                "Similarity (%)": item["similarity"],
                "Evidence": ", ".join(
                    item["guarding_matches"]
                ),
                "OCID": item.get("ocid", "")
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            f"Showing {len(filtered)} tender records."
        )
    else:
        st.info("No tenders found in this category.")

    st.divider()
    st.subheader("Opportunity Assessment")

    candidates = relevant + review

    if candidates:
        selected_index = st.selectbox(
            "Select a tender",
            range(len(candidates)),
            format_func=lambda i: candidates[i].get(
                "title", "Untitled tender"
            )
        )

        tender = candidates[selected_index]

        st.write("**Tender:**", tender.get("title"))
        st.write("**Relevance:**", tender["decision"])
        st.write("**Category:**", tender["category"])
        st.write(
            "**AI Similarity:**",
            f"{tender['similarity']:.2f}%"
        )
        st.write(
            "**Positive Evidence:**",
            ", ".join(tender["guarding_matches"])
            or "No specific evidence identified"
        )
        st.write("**OCID:**", tender.get("ocid"))

        st.divider()
        st.subheader("Commercial Eligibility Assessment")

        # Use verified structured fields only.
        # Do not invent tender service requirements,
        # locations, values or certifications.

        service = tender.get("service")

        if not service:
            st.warning(
                "Tender service requirements have not "
                "been independently verified."
            )

        eligibility_input = {
            "title": tender.get("title", ""),
            "service": service or "",
            "location": tender.get("location"),
            "value": tender.get("value"),
            "certifications": tender.get("certifications")
        }

        eligibility = evaluate_eligibility(
            company,
            eligibility_input
        )

        # A missing service field is unknown,
        # not evidence of service incompatibility.
        if not service:
            eligibility["service_match"] = None
            eligibility["decision"] = (
                "MANUAL REVIEW REQUIRED"
            )
            eligibility["review_items"].append(
                "Service requirements not verified"
            )
            eligibility["reasons"] = [
                reason
                for reason in eligibility["reasons"]
                if reason != (
                    "Service compatibility not confirmed"
                )
            ]

        st.write(
            "**Preliminary Decision:**",
            eligibility["decision"]
        )

        e1, e2, e3, e4 = st.columns(4)

        service_status = (
            "REVIEW"
            if eligibility["service_match"] is None
            else (
                "PASS"
                if eligibility["service_match"]
                else "REVIEW"
            )
        )

        e1.metric("Service", service_status)
        e2.metric(
            "Location",
            eligibility["location_status"]
        )
        e3.metric(
            "Contract Value",
            eligibility["value_status"]
        )
        e4.metric(
            "Certifications",
            eligibility["certification_status"]
        )

        if eligibility["reasons"]:
            st.write("**Assessment Reasons:**")
            for reason in eligibility["reasons"]:
                st.write("-", reason)

        if eligibility["review_items"]:
            st.write("**Items Requiring Verification:**")
            for item in eligibility["review_items"]:
                st.write("-", item)

        st.info(
            "This assessment supports opportunity screening. "
            "It is not a final Bid / No-Bid decision. "
            "Verify the official tender documents before bidding."
        )

    else:
        st.info(
            "No candidates currently available "
            "for commercial eligibility assessment."
        )

else:
    st.info(
        "Click Discover Opportunities to begin."
    )
