
import streamlit as st
import pandas as pd

from company_tender_matcher import (
    create_company,
    match_company_to_tenders
)
from live_ai_matcher import fetch_tenders


st.set_page_config(
    page_title="AI Tender Intelligence Engine",
    page_icon="📊",
    layout="wide"
)

st.title("AI Tender Intelligence Engine")
st.caption(
    "UK Public Procurement | AI-Powered Business Development"
)

st.sidebar.header("Company Intelligence")
company = create_company()

st.sidebar.write("Company:", company.name)
st.sidebar.write("Industry:", company.industry)
st.sidebar.write("Services:", ", ".join(company.services))

st.subheader("Live UK Tender Discovery")

@st.cache_data(ttl=3600)
def load_tenders():
    return fetch_tenders()


@st.cache_resource
def load_company():
    return create_company()


if st.button("Discover Opportunities", type="primary"):
    try:
        with st.spinner("Retrieving and analysing UK tenders..."):
            tenders = load_tenders()
            matches = match_company_to_tenders(
                load_company(), tenders
            )

        if not matches:
            st.warning("No tenders were returned.")
        else:
            st.session_state["matches"] = matches

    except Exception as error:
        st.error(f"Unable to retrieve opportunities: {error}")


if "matches" in st.session_state:
    matches = st.session_state["matches"]

    col1, col2, col3 = st.columns(3)

    col1.metric("Tenders Analysed", len(matches))
    col2.metric(
        "Similarity ≥ 30%",
        sum(
            item["similarity"] >= 30
            for item in matches
        )
    )
    col3.metric(
        "Highest Similarity",
        f"{max(item['similarity'] for item in matches):.1f}%"
    )

    st.subheader("AI-Matched Tender Opportunities")

    records = [
        {
            "Tender": item.get("title", ""),
            "AI Similarity (%)": item["similarity"],
            "OCID": item.get("ocid", "")
        }
        for item in matches
    ]

    df = pd.DataFrame(records)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.info(
        "AI similarity indicates semantic resemblance, "
        "not confirmed tender eligibility or bid suitability."
    )
else:
    st.info(
        "Click Discover Opportunities to begin analysing tenders."
    )
