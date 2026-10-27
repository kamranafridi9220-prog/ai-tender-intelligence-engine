
# ============================================================
# AI TENDER INTELLIGENCE ENGINE
# Live Tender Data Enrichment
# ============================================================

import json
import time

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from sentence_transformers import (
    SentenceTransformer,
    util
)


API_URL = (
    "https://www.find-tender.service.gov.uk"
    "/api/1.0/ocdsReleasePackages"
    "?stages=tender&limit=100"
)

COMPANY_PROFILE = (
    "Professional security services including "
    "manned guarding, security officers, "
    "mobile patrols, key holding and "
    "commercial premises protection."
)


# ------------------------------------------------------------
# SAFE API REQUEST
# ------------------------------------------------------------

def request_tender_data():

    request = Request(
        API_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "AI-Tender-Intelligence/1.0"
        }
    )

    for attempt in range(1, 4):

        try:
            print(f"API request attempt {attempt}/3")

            with urlopen(request, timeout=60) as response:
                return json.load(response)

        except (
            HTTPError,
            URLError,
            TimeoutError
        ) as error:

            print("API error:", error)

            if attempt == 3:
                raise

            time.sleep(attempt * 5)


# ------------------------------------------------------------
# VALUE EXTRACTION
# ------------------------------------------------------------

def extract_value(tender):

    value = tender.get("value") or {}

    amount = value.get("amount")
    currency = value.get("currency")

    if amount is None:
        return None, currency

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return None, currency

    return amount, currency


# ------------------------------------------------------------
# LOCATION EXTRACTION
# ------------------------------------------------------------

def extract_locations(tender):

    locations = []

    for item in tender.get("items") or []:

        for delivery in item.get(
            "deliveryAddresses"
        ) or []:

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
# CPV CLASSIFICATION
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
# TENDER DATA EXTRACTION
# ------------------------------------------------------------

def fetch_tenders():

    data = request_tender_data()

    tenders = []

    for release in data.get("releases", []):

        tender = release.get("tender") or {}

        title = tender.get("title") or ""
        description = tender.get("description") or ""

        if not title.strip():
            continue

        value, currency = extract_value(tender)

        locations = extract_locations(tender)

        cpv_codes = extract_cpv_codes(tender)

        tender_period = (
            tender.get("tenderPeriod") or {}
        )

        deadline = tender_period.get("endDate")

        tenders.append({
            "title": title,
            "description": description,
            "service": description or None,
            "ocid": release.get("ocid", "Unknown"),
            "value": value,
            "currency": currency,
            "locations": locations,
            "location": (
                locations[0] if locations else None
            ),
            "cpv_codes": cpv_codes,
            "deadline": deadline,
            "certifications": None
        })

    return tenders


# ------------------------------------------------------------
# AI SEMANTIC RANKING
# ------------------------------------------------------------

def rank_tenders(tenders):

    if not tenders:
        return []

    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    texts = [
        COMPANY_PROFILE
    ] + [
        tender["title"] + ". "
        + tender["description"]
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
                score * 100, 2
            )
        })

    return sorted(
        results,
        key=lambda item: item["similarity"],
        reverse=True
    )


# ------------------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------------------

def main():

    print("AI TENDER DATA ENRICHMENT")

    tenders = fetch_tenders()

    print("Tenders retrieved:", len(tenders))

    if not tenders:
        print("No tenders returned")
        return

    for tender in tenders[:5]:

        print("-" * 55)
        print("Title:", tender["title"])
        print("Value:", tender["value"])
        print("Currency:", tender["currency"])
        print("Locations:", tender["locations"])
        print("CPV:", tender["cpv_codes"])
        print("Deadline:", tender["deadline"])

    print("Data enrichment completed")


if __name__ == "__main__":
    main()
