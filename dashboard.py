
# ============================================================
# AI TENDER INTELLIGENCE ENGINE
# LESSON 23 - CONSOLIDATED COMMERCIAL INTELLIGENCE DASHBOARD
# ============================================================

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from company_tender_matcher import (
    create_company,
    match_company_to_tenders
)
from live_ai_matcher import (
    fetch_tenders,
    enrich_tender
)
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
# CACHED DATA
# ------------------------------------------------------------

@st.cache_resource
def load_company():
    return create_company()


@st.cache_data(ttl=3600)
def load_tenders():
    return fetch_tenders()


@st.cache_data(ttl=3600, show_spinner=False)
def load_enriched_tender(ocid, tender):
    return enrich_tender(tender)


company = load_company()


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def format_value(value, currency):
    if value is None:
        return "Not published"

    try:
        amount = float(value)
    except (TypeError, ValueError):
        return "Not available"

    symbols = {
        "GBP": "£",
        "USD": "$",
        "EUR": "€"
    }

    symbol = symbols.get(currency)

    if symbol:
        return f"{symbol}{amount:,.0f}"

    if currency:
        return f"{amount:,.0f} {currency}"

    return f"{amount:,.0f} (currency unverified)"


def parse_date(value):
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(timezone.utc)

    except (TypeError, ValueError):
        return None


def format_date(value):
    parsed = parse_date(value)

    if parsed is None:
        return "Not available"

    return parsed.strftime(
        "%d %b %Y, %H:%M UTC"
    )


def deadline_status(value):
    parsed = parse_date(value)

    if parsed is None:
        return "UNKNOWN"

    remaining = (
        parsed - datetime.now(timezone.utc)
    ).total_seconds() / 86400

    if remaining < 0:
        return "DEADLINE PASSED"

    if remaining < 7:
        return "CLOSING SOON"

    return "DEADLINE UPCOMING"


def unique_locations(tender):
    locations = tender.get("locations") or []

    if isinstance(locations, str):
        locations = [locations]

    return list(dict.fromkeys(
        str(location)
        for location in locations
        if location
    ))


def assess_commercial_fit(company, tender):
    # Keep the original eligibility engine,
    # but avoid treating incomplete API data
    # as confirmed compliance.

    eligibility_input = {
        "title": tender.get("title", ""),
        "service": tender.get("service") or "",
        "location": tender.get("location"),
        "value": tender.get("value"),
        "certifications": tender.get("certifications")
    }

    result = evaluate_eligibility(
        company,
        eligibility_input
    )

    # The hybrid relevance engine provides
    # evidence of potential service compatibility.
    # This does not confirm all tender requirements.

    guarding_evidence = (
        tender.get("guarding_matches") or []
    )

    if guarding_evidence:
        result["service_match"] = None

        result["review_items"].append(
            "Security service evidence identified; "
            "verify detailed scope and requirements"
        )

        result["reasons"] = [
            reason
            for reason in result["reasons"]
            if reason != "Service compatibility not confirmed"
        ]

    elif not eligibility_input["service"]:
        result["service_match"] = None

        result["review_items"].append(
            "Service requirements not verified"
        )

    # Do not treat broad UK region codes as
    # confirmed delivery locations.

    locations = unique_locations(tender)

    if locations and not tender.get("location"):
        result["location_status"] = "REVIEW"

        result["review_items"].append(
            "Regional coverage requires verification"
        )

    statuses = [
        result["location_status"],
        result["value_status"],
        result["certification_status"]
    ]

    if "FAIL" in statuses:
        result["decision"] = "NOT SUITABLE - REVIEW"

    elif (
        "REVIEW" in statuses
        or result["service_match"] is not True
    ):
        result["decision"] = "MANUAL REVIEW REQUIRED"

    else:
        result["decision"] = "PRELIMINARY MATCH"

    result["review_items"] = list(
        dict.fromkeys(result["review_items"])
    )

    return result


def bid_recommendation(tender, eligibility):
    relevance = tender.get("decision")

    if relevance == "NOT RELEVANT":
        return "NO-BID CANDIDATE"

    if deadline_status(
        tender.get("deadline")
    ) == "DEADLINE PASSED":
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
    "UK Public Procurement Decision Intelligence"
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
# DISCOVERY PIPELINE
# ------------------------------------------------------------

if st.button(
    "Discover Opportunities",
    type="primary"
):
    try:
        with st.spinner(
            "Retrieving and analysing UK tenders..."
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

                # Fetch detailed records only for
                # shortlisted tenders.

                if relevance["decision"] in [
                    "RELEVANT CANDIDATE",
                    "MANUAL REVIEW",
                    "MIXED SCOPE - REVIEW"
                ]:

                    try:
                        record = load_enriched_tender(
                            str(record.get("ocid", "")),
                            record
                        )

                        # Preserve original classification.
                        record.update(relevance)

                    except Exception as error:
                        record["enrichment_status"] = "FAILED"
                        record["enrichment_error"] = str(error)

                else:
                    record["enrichment_status"] = (
                        "NOT REQUESTED"
                    )

                eligibility = assess_commercial_fit(
                    company,
                    record
                )

                record["eligibility"] = eligibility

                record["bid_recommendation"] = (
                    bid_recommendation(
                        record,
                        eligibility
                    )
                )

                results.append(record)

            st.session_state["tender_results"] = results

        st.success(
            "Tender discovery and consolidated "
            "commercial intelligence completed."
        )

    except Exception as error:
        st.error(
            f"Discovery failed: {error}"
        )


# ------------------------------------------------------------
# RESULTS
# ------------------------------------------------------------

if "tender_results" in st.session_state:

    results = st.session_state["tender_results"]

    relevant = [
        tender
        for tender in results
        if tender["decision"] == "RELEVANT CANDIDATE"
    ]

    review = [
        tender
        for tender in results
        if tender["decision"] in [
            "MANUAL REVIEW",
            "MIXED SCOPE - REVIEW"
        ]
    ]

    rejected = [
        tender
        for tender in results
        if tender["decision"] == "NOT RELEVANT"
    ]

    st.divider()

    st.subheader(
        "Commercial Intelligence Overview"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Tenders Analysed",
        len(results)
    )

    c2.metric(
        "Relevant Candidates",
        len(relevant)
    )

    c3.metric(
        "Manual Review",
        len(review)
    )

    c4.metric(
        "Not Relevant",
        len(rejected)
    )

    # --------------------------------------------------------
    # FILTER
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
    # OPPORTUNITY TABLE
    # --------------------------------------------------------

    if filtered:

        rows = []

        for tender in filtered:

            rows.append({
                "Tender": tender.get("title", ""),
                "Relevance": tender["decision"],
                "Similarity (%)": tender["similarity"],
                "Contract Value": format_value(
                    tender.get("value"),
                    tender.get("currency")
                ),
                "Locations": ", ".join(
                    unique_locations(tender)
                ) or "Not available",
                "Deadline": format_date(
                    tender.get("deadline")
                ),
                "Deadline Status": deadline_status(
                    tender.get("deadline")
                ),
                "CPV Codes": ", ".join(
                    tender.get("cpv_codes") or []
                ) or "Not available",
                "Bid Screening": tender[
                    "bid_recommendation"
                ],
                "Enrichment": tender.get(
                    "enrichment_status",
                    "NOT REQUESTED"
                ),
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
    # DETAILED OPPORTUNITY ASSESSMENT
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "Commercial Opportunity Assessment"
    )

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
        eligibility = tender["eligibility"]

        st.write(
            "**Tender:**",
            tender.get("title")
        )

        st.write(
            "**Relevance:**",
            tender["decision"]
        )

        st.write(
            "**AI Similarity:**",
            f"{tender['similarity']:.2f}%"
        )

        st.write(
            "**Positive Evidence:**",
            ", ".join(
                tender.get("guarding_matches") or []
            ) or "None identified"
        )

        st.write(
            "**Estimated Contract Value:**",
            format_value(
                tender.get("value"),
                tender.get("currency")
            )
        )

        st.write(
            "**Delivery Regions:**",
            ", ".join(
                unique_locations(tender)
            ) or "Not available"
        )

        st.write(
            "**CPV Codes:**",
            ", ".join(
                tender.get("cpv_codes") or []
            ) or "Not available"
        )

        st.write(
            "**Submission Deadline:**",
            format_date(
                tender.get("deadline")
            )
        )

        st.write(
            "**Deadline Status:**",
            deadline_status(
                tender.get("deadline")
            )
        )

        st.write(
            "**OCID:**",
            tender.get("ocid")
        )

        st.write(
            "**Enrichment Status:**",
            tender.get(
                "enrichment_status",
                "NOT REQUESTED"
            )
        )

        if tender.get("enrichment_error"):
            st.warning(
                tender["enrichment_error"]
            )

        # ----------------------------------------------------
        # DETAILED LOT REQUIREMENTS
        # ----------------------------------------------------

        lot_descriptions = (
            tender.get("lot_descriptions") or []
        )

        if lot_descriptions:

            st.divider()

            st.subheader(
                "Detailed Contract Requirements"
            )

            for index, description in enumerate(
                lot_descriptions,
                start=1
            ):

                with st.expander(
                    f"Lot {index} - Requirements"
                ):
                    st.write(description)

        # ----------------------------------------------------
        # CONTRACT PERIOD
        # ----------------------------------------------------

        contract_periods = (
            tender.get("contract_periods") or []
        )

        if contract_periods:

            st.divider()

            st.subheader("Contract Duration")

            for index, period in enumerate(
                contract_periods,
                start=1
            ):

                st.write(
                    f"**Lot {index} Start:**",
                    format_date(
                        period.get("startDate")
                    )
                )

                st.write(
                    f"**Lot {index} End:**",
                    format_date(
                        period.get("endDate")
                    )
                )

        # ----------------------------------------------------
        # COMMERCIAL ELIGIBILITY
        # ----------------------------------------------------

        st.divider()

        st.subheader("Commercial Eligibility")

        st.write(
            "**Preliminary Decision:**",
            eligibility["decision"]
        )

        e1, e2, e3, e4 = st.columns(4)

        service_status = (
            "PASS"
            if eligibility["service_match"] is True
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
        # BID / NO-BID
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "AI Bid / No-Bid Screening"
        )

        st.write(
            "**Recommendation:**",
            tender["bid_recommendation"]
        )

        st.info(
            "This is a preliminary screening result. "
            "Tender relevance does not establish "
            "legal, technical or commercial eligibility. "
            "Review the official procurement documents "
            "before deciding whether to bid."
        )

    else:
        st.info(
            "No shortlisted tenders available "
            "for detailed assessment."
        )

else:

    st.info(
        "Click Discover Opportunities to analyse "
        "live UK public procurement tenders."
    )
