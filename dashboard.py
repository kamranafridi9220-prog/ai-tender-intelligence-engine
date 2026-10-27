
# ============================================================
# AI TENDER INTELLIGENCE ENGINE
# LESSON 21 - COMMERCIAL INTELLIGENCE DASHBOARD
# ============================================================

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from company_tender_matcher import (
    create_company,
    match_company_to_tenders
)
from live_ai_matcher import fetch_tenders
from hybrid_relevance import assess_relevance
from eligibility_engine import evaluate_eligibility


# ------------------------------------------------------------
# PAGE CONFIGURATION
# ------------------------------------------------------------

st.set_page_config(
    page_title="AI Tender Intelligence Engine",
    page_icon="📊",
    layout="wide"
)


# ------------------------------------------------------------
# DATA LOADING
# ------------------------------------------------------------

@st.cache_resource
def load_company():
    return create_company()


@st.cache_data(ttl=3600)
def load_tenders():
    return fetch_tenders()


company = load_company()


# ------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------

def format_value(value, currency):
    if value is None:
        return "Not published"

    try:
        amount = float(value)
    except (TypeError, ValueError):
        return "Not available"

    symbol = {
        "GBP": "£",
        "USD": "$",
        "EUR": "€"
    }.get(currency)

    if symbol:
        return f"{symbol}{amount:,.0f}"

    if currency:
        return f"{amount:,.0f} {currency}"

    return f"{amount:,.0f} (currency unverified)"


def parse_deadline(value):
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    except (TypeError, ValueError):
        return None


def deadline_information(value):
    parsed = parse_deadline(value)

    if parsed is None:
        return "Not available", "UNKNOWN"

    remaining = (
        parsed - datetime.now(timezone.utc)
    ).total_seconds() / 86400

    formatted = parsed.strftime(
        "%d %b %Y, %H:%M UTC"
    )

    if remaining < 0:
        status = "DEADLINE PASSED"
    elif remaining < 7:
        status = "LESS THAN 7 DAYS"
    else:
        status = "OPEN DEADLINE"

    return formatted, status


def prepare_eligibility_input(tender):
    # Only use fields available from the API.
    # Do not invent missing information.

    return {
        "title": tender.get("title", ""),
        "service": tender.get("service") or "",
        "location": tender.get("location"),
        "value": tender.get("value"),
        "certifications": tender.get("certifications")
    }


def assess_commercial_fit(company, tender):
    eligibility_input = prepare_eligibility_input(tender)

    result = evaluate_eligibility(
        company,
        eligibility_input
    )

    # A description is preliminary service evidence,
    # not confirmation of all contract requirements.
    service_text = eligibility_input["service"]

    if not service_text:
        result["service_match"] = None
        result["review_items"].append(
            "Service requirements not verified"
        )

    # Prevent missing information being treated as
    # confirmed commercial eligibility.
    statuses = [
        result["location_status"],
        result["value_status"],
        result["certification_status"]
    ]

    if "FAIL" in statuses:
        result["decision"] = "NOT SUITABLE - REVIEW"

    elif (
        "REVIEW" in statuses
        or not result["service_match"]
    ):
        result["decision"] = "MANUAL REVIEW REQUIRED"

    else:
        result["decision"] = "PRELIMINARY MATCH"

    return result


def bid_recommendation(relevance, eligibility, deadline):
    # This is a preliminary screening recommendation,
    # not a final tender eligibility determination.

    if relevance == "NOT RELEVANT":
        return "NO-BID CANDIDATE"

    _, deadline_status = deadline_information(deadline)

    if deadline_status == "DEADLINE PASSED":
        return "DEADLINE PASSED - VERIFY STATUS"

    if relevance in [
        "MANUAL REVIEW",
        "MIXED SCOPE - REVIEW"
    ]:
        return "INVESTIGATE FURTHER"

    if eligibility["decision"] == "NOT SUITABLE - REVIEW":
        return "COMMERCIAL FIT REVIEW"

    if eligibility["decision"] == "PRELIMINARY MATCH":
        return "POTENTIAL BID CANDIDATE"

    return "BID ELIGIBILITY REVIEW"


# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------

st.sidebar.title("Company Intelligence")

st.sidebar.write(
    "**Company:**",
    company.name
)

st.sidebar.write(
    "**Industry:**",
    company.industry
)

st.sidebar.write(
    "**Services:**",
    ", ".join(company.services)
)

st.sidebar.write(
    "**Operating Locations:**",
    ", ".join(company.locations)
)

st.sidebar.divider()

st.sidebar.caption(
    "AI-powered UK procurement intelligence"
)


# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

st.title("AI Tender Intelligence Engine")

st.caption(
    "UK Public Procurement | "
    "AI-Powered Business Development"
)

st.subheader("Live Tender Discovery")


# ------------------------------------------------------------
# LIVE DISCOVERY
# ------------------------------------------------------------

if st.button(
    "Discover Opportunities",
    type="primary"
):
    try:
        with st.spinner(
            "Discovering and analysing UK tenders..."
        ):

            tenders = load_tenders()

            ranked = match_company_to_tenders(
                company,
                tenders
            )

            results = []

            for tender in ranked:
                relevance = assess_relevance(tender)

                record = {
                    **tender,
                    **relevance
                }

                eligibility = assess_commercial_fit(
                    company,
                    record
                )

                record["eligibility"] = eligibility

                record["bid_recommendation"] = (
                    bid_recommendation(
                        relevance["decision"],
                        eligibility,
                        record.get("deadline")
                    )
                )

                results.append(record)

            st.session_state["tender_results"] = results

        st.success(
            "Tender discovery and commercial "
            "intelligence assessment completed."
        )

    except Exception as error:
        st.error(
            f"Tender discovery failed: {error}"
        )


# ------------------------------------------------------------
# RESULTS
# ------------------------------------------------------------

if "tender_results" in st.session_state:

    results = st.session_state["tender_results"]

    relevant = [
        tender for tender in results
        if tender["decision"] == "RELEVANT CANDIDATE"
    ]

    review = [
        tender for tender in results
        if tender["decision"] in [
            "MANUAL REVIEW",
            "MIXED SCOPE - REVIEW"
        ]
    ]

    rejected = [
        tender for tender in results
        if tender["decision"] == "NOT RELEVANT"
    ]

    st.divider()

    st.subheader("Commercial Intelligence Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Tenders Analysed", len(results))
    c2.metric("Relevant Candidates", len(relevant))
    c3.metric("Manual Review", len(review))
    c4.metric("Not Relevant", len(rejected))

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    st.divider()

    st.subheader("Tender Opportunity Explorer")

    selected_filter = st.selectbox(
        "Relevance classification",
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

    # --------------------------------------------------------
    # COMMERCIAL DATA TABLE
    # --------------------------------------------------------

    if filtered:

        rows = []

        for tender in filtered:

            deadline, deadline_status = (
                deadline_information(
                    tender.get("deadline")
                )
            )

            rows.append({
                "Tender": tender.get("title", ""),
                "Relevance": tender["decision"],
                "AI Similarity (%)": tender["similarity"],
                "Contract Value": format_value(
                    tender.get("value"),
                    tender.get("currency")
                ),
                "Location": ", ".join(
                    tender.get("locations") or []
                ) or "Not available",
                "Deadline": deadline,
                "Deadline Status": deadline_status,
                "CPV Codes": ", ".join(
                    tender.get("cpv_codes") or []
                ) or "Not available",
                "Bid Screening": tender[
                    "bid_recommendation"
                ],
                "OCID": tender.get("ocid", "")
            })

        dataframe = pd.DataFrame(rows)

        st.dataframe(
            dataframe,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Tender Intelligence CSV",
            data=dataframe.to_csv(index=False),
            file_name="tender_intelligence.csv",
            mime="text/csv"
        )

        st.caption(
            f"Showing {len(filtered)} opportunities."
        )

    else:
        st.info(
            "No opportunities found for this filter."
        )

    # --------------------------------------------------------
    # DETAILED ASSESSMENT
    # --------------------------------------------------------

    st.divider()

    st.subheader("Commercial Opportunity Assessment")

    candidates = relevant + review

    if candidates:

        selected_index = st.selectbox(
            "Select a tender for detailed assessment",
            range(len(candidates)),
            format_func=lambda i: candidates[i].get(
                "title", "Untitled"
            )
        )

        tender = candidates[selected_index]

        eligibility = tender["eligibility"]

        st.write(
            "**Tender:**",
            tender.get("title")
        )

        st.write(
            "**Relevance Decision:**",
            tender["decision"]
        )

        st.write(
            "**AI Similarity:**",
            f"{tender['similarity']:.2f}%"
        )

        st.write(
            "**Positive Evidence:**",
            ", ".join(
                tender["guarding_matches"]
            ) or "None identified"
        )

        st.write(
            "**CPV Classifications:**",
            ", ".join(
                tender.get("cpv_codes") or []
            ) or "Not available"
        )

        st.write(
            "**Estimated Contract Value:**",
            format_value(
                tender.get("value"),
                tender.get("currency")
            )
        )

        st.write(
            "**Delivery Locations:**",
            ", ".join(
                tender.get("locations") or []
            ) or "Not available"
        )

        deadline, deadline_status = (
            deadline_information(
                tender.get("deadline")
            )
        )

        st.write(
            "**Submission Deadline:**",
            deadline
        )

        st.write(
            "**Deadline Status:**",
            deadline_status
        )

        st.write(
            "**OCID:**",
            tender.get("ocid", "")
        )

        # ----------------------------------------------------
        # ELIGIBILITY
        # ----------------------------------------------------

        st.divider()

        st.subheader("Commercial Eligibility")

        st.write(
            "**Preliminary Eligibility:**",
            eligibility["decision"]
        )

        e1, e2, e3, e4 = st.columns(4)

        service_status = (
            "PASS"
            if eligibility["service_match"]
            else "REVIEW"
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

        # ----------------------------------------------------
        # BID / NO-BID SCREENING
        # ----------------------------------------------------

        st.divider()

        st.subheader("AI Bid / No-Bid Screening")

        st.write(
            "**Recommendation:**",
            tender["bid_recommendation"]
        )

        st.info(
            "This recommendation is preliminary. "
            "AI relevance does not establish legal, "
            "technical or commercial eligibility. "
            "Verify the official procurement documents "
            "before making a final bidding decision."
        )

    else:
        st.info(
            "No relevant or manual-review tenders "
            "are available for detailed assessment."
        )

else:
    st.info(
        "Click Discover Opportunities to analyse "
        "live UK procurement tenders."
    )
