
# ============================================================
# LESSON 23 - CONSOLIDATED PROCUREMENT INTELLIGENCE
# ============================================================

def fetch_consolidated_record(ocid):
    """
    Retrieve the consolidated procurement record
    for one shortlisted opportunity.
    """
    from urllib.parse import quote

    if not ocid or ocid == "Unknown":
        return None

    url = (
        "https://www.find-tender.service.gov.uk"
        "/api/1.0/ocdsRecordPackages/"
        + quote(str(ocid), safe="")
    )

    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AI-Tender-Intelligence/1.0"
        }
    )

    for attempt in range(1, 4):
        try:
            with urlopen(request, timeout=30) as response:
                data = json.load(response)

            records = data.get("records") or []

            for record in records:
                compiled = record.get("compiledRelease")
                if compiled:
                    return compiled

            return None

        except (HTTPError, URLError, TimeoutError):
            if attempt == 3:
                raise
            time.sleep(attempt * 2)

    return None


def enrich_tender(tender):
    """
    Add consolidated procurement details without
    discarding the existing AI matching results.
    """
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
    items = details.get("items") or []

    lot_descriptions = [
        lot.get("description", "")
        for lot in lots
        if lot.get("description")
    ]

    locations = []

    for item in items:
        for delivery in item.get(
            "deliveryAddresses"
        ) or []:
            region = delivery.get("region")
            if region:
                locations.append(str(region))

    locations = list(dict.fromkeys(locations))

    tender_period = details.get("tenderPeriod") or {}

    contract_periods = [
        lot.get("contractPeriod")
        for lot in lots
        if lot.get("contractPeriod")
    ]

    return {
        **tender,
        "description": (
            details.get("description")
            or tender.get("description")
            or ""
        ),
        "lot_descriptions": lot_descriptions,
        "deadline": (
            tender_period.get("endDate")
            or tender.get("deadline")
        ),
        "value": (
            (details.get("value") or {}).get("amount")
            if details.get("value")
            else tender.get("value")
        ),
        "currency": (
            (details.get("value") or {}).get("currency")
            or tender.get("currency")
        ),
        "locations": (
            locations
            or tender.get("locations")
            or []
        ),
        "contract_periods": contract_periods,
        "enrichment_status": "ENRICHED"
    }
