
# ============================================================
# AI TENDER INTELLIGENCE ENGINE
# COMPLETE LIVE AI MATCHER + PROCUREMENT ENRICHMENT
# LESSON 23
# ============================================================

import json
import time

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote

from sentence_transformers import SentenceTransformer, util


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

BASE_URL = "https://www.find-tender.service.gov.uk"

API_URL = (
    BASE_URL
    + "/api/1.0/ocdsReleasePackages"
    + "?stages=tender&limit=100"
)

COMPANY_PROFILE = (
    "Professional security services including "
    "manned guarding, security officers, "
    "mobile patrols, key holding and "
    "commercial premises protection."
)


# ------------------------------------------------------------
# API REQUEST HELPER
# ------------------------------------------------------------

def request_json(url, attempts=3, timeout=60):

    for attempt in range(1, attempts + 1):

        try:
            request = Request(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "AI-Tender-Intelligence/1.0"
                }
            )

            with urlopen(request, timeout=timeout) as response:
                return json.load(response)

        except (
            HTTPError,
            URLError,
            TimeoutError
        ) as error:

            print(
                f"API request {attempt}/{attempts} failed: {error}"
            )

            if attempt == attempts:
                raise

            time.sleep(attempt * 2)


# ------------------------------------------------------------
# CONTRACT VALUE EXTRACTION
# ------------------------------------------------------------

def extract_value(tender):

    value = tender.get("value") or {}

    if not isinstance(value, dict):
        return None, None

    amount = value.get("amount")
    currency = value.get("currency")

    if amount is None:
        return None, currency

    try:
        return float(amount), currency

    except (TypeError, ValueError):
        return None, currency


# ------------------------------------------------------------
# DELIVERY LOCATION EXTRACTION
# ------------------------------------------------------------

def extract_locations(tender):

    locations = []

    for item in tender.get("items") or []:

        for delivery in item.get(
            "deliveryAddresses"
        ) or []:

            if not isinstance(delivery, dict):
                continue

            # OCDS deliveryAddresses may contain
            # region codes directly, e.g. UKI.
            location = (
                delivery.get("addressLocality")
                or delivery.get("region")
                or delivery.get("countryName")
            )

            if not location:
                address = delivery.get("address") or {}

                location = (
                    address.get("addressLocality")
                    or address.get("region")
                    or address.get("countryName")
                )

            if location:
                locations.append(str(location))

    return list(dict.fromkeys(locations))


# ------------------------------------------------------------
# CPV EXTRACTION
# ------------------------------------------------------------

def extract_cpv_codes(tender):

    codes = []

    for item in tender.get("items") or []:

        classification = (
            item.get("classification") or {}
        )

        if classification.get("id"):
            codes.append(
                str(classification["id"])
            )

        for extra in item.get(
            "additionalClassifications"
        ) or []:

            if extra.get("id"):
                codes.append(str(extra["id"]))

    return list(dict.fromkeys(codes))


# ------------------------------------------------------------
# FETCH LIVE UK TENDERS
# ------------------------------------------------------------

def fetch_tenders():

    data = request_json(API_URL)

    tenders = []

    for release in data.get("releases") or []:

        tender = release.get("tender") or {}

        title = tender.get("title") or ""
        description = tender.get("description") or ""

        if not title.strip():
            continue

        value, currency = extract_value(tender)

        locations = extract_locations(tender)

        tender_period = (
            tender.get("tenderPeriod") or {}
        )

        tenders.append({
            "title": title,
            "description": description,
            "service": description or None,
            "ocid": release.get("ocid", "Unknown"),
            "value": value,
            "currency": currency,
            "locations": locations,
            "location": None,
            "cpv_codes": extract_cpv_codes(tender),
            "deadline": tender_period.get("endDate"),
            "certifications": None
        })

    return tenders


# ------------------------------------------------------------
# SEMANTIC RANKING
# ------------------------------------------------------------

def rank_tenders(tenders):

    if not tenders:
        return []

    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    texts = [COMPANY_PROFILE] + [
        (
            tender.get("title", "")
            + ". "
            + (tender.get("description") or "")
        )
        for tender in tenders
    ]

    embeddings = model.encode(
        texts,
        convert_to_tensor=True
    )

    scores = util.cos_sim(
        embeddings[0],
        embeddings[1:]
    )[0].tolist()

    results = []

    for tender, score in zip(tenders, scores):

        results.append({
            **tender,
            "similarity": round(
                float(score) * 100,
                2
            )
        })

    return sorted(
        results,
        key=lambda item: item["similarity"],
        reverse=True
    )


# ------------------------------------------------------------
# FETCH CONSOLIDATED PROCUREMENT RECORD
# ------------------------------------------------------------

def fetch_consolidated_record(ocid):

    if not ocid or ocid == "Unknown":
        return None

    url = (
        BASE_URL
        + "/api/1.0/ocdsRecordPackages/"
        + quote(str(ocid), safe="")
    )

    data = request_json(url)

    records = data.get("records") or []

    for record in records:

        compiled = record.get("compiledRelease")

        if isinstance(compiled, dict):
            return compiled

    return None


# ------------------------------------------------------------
# ENRICH SHORTLISTED TENDER
# ------------------------------------------------------------

def enrich_tender(tender):

    record = fetch_consolidated_record(
        tender.get("ocid")
    )

    if not record:
        return {
            **tender,
            "enrichment_status": "NOT AVAILABLE"
        }

    details = record.get("tender") or {}

    lots = details.get("lots") or []

    lot_descriptions = [
        lot.get("description")
        for lot in lots
        if lot.get("description")
    ]

    contract_periods = [
        lot.get("contractPeriod")
        for lot in lots
        if isinstance(lot.get("contractPeriod"), dict)
    ]

    value, currency = extract_value(details)

    locations = extract_locations(details)

    cpv_codes = extract_cpv_codes(details)

    tender_period = (
        details.get("tenderPeriod") or {}
    )

    return {
        **tender,

        "description": (
            details.get("description")
            or tender.get("description")
            or ""
        ),

        "lot_descriptions": lot_descriptions,

        "contract_periods": contract_periods,

        "deadline": (
            tender_period.get("endDate")
            or tender.get("deadline")
        ),

        "value": (
            value
            if value is not None
            else tender.get("value")
        ),

        "currency": (
            currency
            or tender.get("currency")
        ),

        "locations": (
            locations
            or tender.get("locations")
            or []
        ),

        # Do not interpret broad UK region codes
        # as confirmed operating locations.
        "location": None,

        "cpv_codes": (
            cpv_codes
            or tender.get("cpv_codes")
            or []
        ),

        "enrichment_status": "ENRICHED"
    }


# ------------------------------------------------------------
# MAIN - GITHUB ACTIONS COMPATIBILITY
# ------------------------------------------------------------

def main():

    print("=" * 55)
    print("AI TENDER INTELLIGENCE ENGINE")
    print("LIVE PROCUREMENT DATA ENRICHMENT")
    print("=" * 55)

    tenders = fetch_tenders()

    print("Tenders retrieved:", len(tenders))

    for tender in tenders[:5]:

        print("-" * 55)

        print("Title:", tender["title"])
        print("Value:", tender["value"])
        print("Currency:", tender["currency"])
        print("Locations:", tender["locations"])
        print("CPV:", tender["cpv_codes"])
        print("Deadline:", tender["deadline"])

    print("=" * 55)
    print("Live tender extraction completed")


if __name__ == "__main__":
    main()
