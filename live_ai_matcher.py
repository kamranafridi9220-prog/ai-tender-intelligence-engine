"""AEGIS Lesson 25: UK Find a Tender discovery and enrichment.

Backwards-compatible entry points: fetch_tenders(), rank_tenders(),
fetch_consolidated_record(), enrich_tender(), main().
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin, urlparse, parse_qs
from urllib.request import Request, urlopen

BASE_URL = "https://www.find-tender.service.gov.uk"
ENDPOINT = BASE_URL + "/api/1.0/ocdsReleasePackages"
COMPANY_PROFILE = (
    "Professional security services including manned guarding, security officers, "
    "mobile patrols, CCTV monitoring, access control, key holding and "
    "commercial premises protection."
)
SECURITY_PHRASES = (
    "manned guarding", "security guard", "security officer", "guarding services",
    "security services", "mobile patrol", "security patrol", "cctv monitoring",
    "cctv operator", "access control", "key holding", "keyholding",
    "alarm response", "concierge security", "site security",
)
SECURITY_CPV_PREFIXES = ("7971",)  # Investigation and security services family.


def request_json(url, attempts=3, timeout=45):
    for attempt in range(1, attempts + 1):
        try:
            request = Request(url, headers={
                "Accept": "application/json",
                "User-Agent": "AEGIS-Tender-Intelligence/2.0",
            })
            with urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            if attempt == attempts:
                raise
            print(f"Request attempt {attempt}/{attempts} failed: {exc}")
            time.sleep(attempt * 2)


def extract_value(tender):
    value = tender.get("value") or {}
    if not isinstance(value, dict):
        return None, None
    try:
        amount = float(value["amount"]) if value.get("amount") is not None else None
    except (TypeError, ValueError, OverflowError):
        amount = None
    return amount, value.get("currency")


def extract_locations(tender):
    locations = []
    for item in tender.get("items") or []:
        if not isinstance(item, dict):
            continue
        for delivery in item.get("deliveryAddresses") or []:
            if not isinstance(delivery, dict):
                continue
            address = delivery.get("address") or {}
            if not isinstance(address, dict):
                address = {}
            location = (delivery.get("addressLocality") or delivery.get("region")
                        or delivery.get("countryName") or address.get("addressLocality")
                        or address.get("region") or address.get("countryName"))
            if location:
                locations.append(str(location))
    return list(dict.fromkeys(locations))


def extract_cpv_codes(tender):
    codes = []
    for item in tender.get("items") or []:
        if not isinstance(item, dict):
            continue
        classifications = [item.get("classification")] + (item.get("additionalClassifications") or [])
        for classification in classifications:
            if isinstance(classification, dict) and classification.get("id"):
                codes.append(str(classification["id"]))
    return list(dict.fromkeys(codes))


def _extract_releases(data):
    releases = data.get("releases") or []
    if releases:
        return releases
    # Some APIs return a list of release packages instead of one package.
    packages = data.get("results") or []
    combined = []
    for package in packages:
        if isinstance(package, dict):
            combined.extend(package.get("releases") or [])
    return combined


def _next_page_url(data, current_url):
    """Follow an explicitly supplied API next link; never invent pagination."""
    links = data.get("links") or {}
    next_link = links.get("next") if isinstance(links, dict) else None
    if not next_link:
        next_link = data.get("next")
    if isinstance(next_link, dict):
        next_link = next_link.get("href") or next_link.get("url")
    if not isinstance(next_link, str) or not next_link:
        return None
    url = urljoin(current_url, next_link)
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != urlparse(BASE_URL).netloc:
        return None
    return url


def _normalise_release(release):
    tender = release.get("tender") or {}
    if not isinstance(tender, dict):
        return None
    title = tender.get("title") or ""
    if not str(title).strip():
        return None
    value, currency = extract_value(tender)
    description = tender.get("description") or ""
    return {
        "title": str(title),
        "description": str(description),
        "service": str(description) or None,
        "ocid": release.get("ocid") or "Unknown",
        "value": value,
        "currency": currency,
        "locations": extract_locations(tender),
        "location": None,
        "cpv_codes": extract_cpv_codes(tender),
        "deadline": (tender.get("tenderPeriod") or {}).get("endDate"),
        "certifications": None,
        "published_date": release.get("date"),
        "release_id": release.get("id"),
    }


def _security_signals(tender):
    text = (tender.get("title", "") + " " + (tender.get("description") or "")).lower()
    phrases = [phrase for phrase in SECURITY_PHRASES if phrase in text]
    cpv = [code for code in tender.get("cpv_codes", [])
           if str(code).startswith(SECURITY_CPV_PREFIXES)]
    return phrases, cpv


def fetch_tenders(max_records=100, security_only=False, max_pages=5, days_back=None):
    """Fetch releases, deduplicate OCIDs, and optionally shortlist security leads.

    Pagination follows next links only when the API supplies them. A requested
    maximum is a ceiling, not a guarantee of that many results.
    """
    max_records = max(1, min(int(max_records), 5000))
    max_pages = max(1, min(int(max_pages), 50))
    params = {"stages": "tender", "limit": min(100, max_records)}
    url = ENDPOINT + "?" + urlencode(params)
    seen_urls = set()
    by_ocid = {}
    cutoff = None
    if days_back is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, int(days_back)))

    pages = 0
    while url and pages < max_pages and len(by_ocid) < max_records:
        if url in seen_urls:
            break
        seen_urls.add(url)
        data = request_json(url)
        pages += 1
        releases = _extract_releases(data)
        for release in releases:
            if not isinstance(release, dict):
                continue
            record = _normalise_release(release)
            if record is None:
                continue
            if cutoff and record.get("published_date"):
                try:
                    published = datetime.fromisoformat(record["published_date"].replace("Z", "+00:00"))
                    if published.tzinfo is None:
                        published = published.replace(tzinfo=timezone.utc)
                    if published < cutoff:
                        continue
                except (TypeError, ValueError):
                    pass
            phrases, cpv = _security_signals(record)
            record["discovery_phrases"] = phrases
            record["discovery_cpv_codes"] = cpv
            record["discovery_match"] = bool(phrases or cpv)
            if security_only and not record["discovery_match"]:
                continue
            key = record["ocid"]
            if key == "Unknown":
                key = "title:" + record["title"].casefold()
            # Keep first release for each procurement. No false extra counts.
            if key not in by_ocid:
                by_ocid[key] = record
            if len(by_ocid) >= max_records:
                break
        url = _next_page_url(data, url)
        if not releases:
            break

    print(f"Discovery: {pages} page(s), {len(by_ocid)} unique tenders, security_only={security_only}")
    if max_pages > 1 and pages == 1:
        print("Note: API did not supply a next-page link; no additional pages assumed.")
    return list(by_ocid.values())


def rank_tenders(tenders):
    if not tenders:
        return []
    # Lazy import keeps ordinary API discovery independent of the AI model.
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    texts = [COMPANY_PROFILE] + [
        str(t.get("title") or "") + ". " + str(t.get("description") or "")
        for t in tenders
    ]
    embeddings = model.encode(texts, convert_to_tensor=True)
    scores = util.cos_sim(embeddings[0], embeddings[1:])[0].tolist()
    return sorted(
        [{**t, "similarity": round(float(score) * 100, 2)} for t, score in zip(tenders, scores)],
        key=lambda item: item["similarity"], reverse=True,
    )


def fetch_consolidated_record(ocid):
    if not ocid or ocid == "Unknown":
        return None
    url = BASE_URL + "/api/1.0/ocdsRecordPackages/" + quote(str(ocid), safe="")
    data = request_json(url)
    for record in data.get("records") or []:
        compiled = record.get("compiledRelease")
        if isinstance(compiled, dict):
            return compiled
    return None


def enrich_tender(tender):
    record = fetch_consolidated_record(tender.get("ocid"))
    if not record:
        return {**tender, "enrichment_status": "NOT AVAILABLE"}
    details = record.get("tender") or {}
    lots = [lot for lot in (details.get("lots") or []) if isinstance(lot, dict)]
    value, currency = extract_value(details)
    return {
        **tender,
        "description": details.get("description") or tender.get("description") or "",
        "lot_descriptions": [lot["description"] for lot in lots if lot.get("description")],
        "contract_periods": [lot["contractPeriod"] for lot in lots if isinstance(lot.get("contractPeriod"), dict)],
        "deadline": (details.get("tenderPeriod") or {}).get("endDate") or tender.get("deadline"),
        "value": value if value is not None else tender.get("value"),
        "currency": currency or tender.get("currency"),
        "locations": extract_locations(details) or tender.get("locations") or [],
        "location": None,
        "cpv_codes": extract_cpv_codes(details) or tender.get("cpv_codes") or [],
        "enrichment_status": "ENRICHED",
    }


def main():
    print("AEGIS | Lesson 25 | Targeted Security Tender Discovery")
    tenders = fetch_tenders(max_records=100, security_only=False)
    leads = [t for t in tenders if t.get("discovery_match")]
    print(f"Unique tenders: {len(tenders)} | Security discovery leads: {len(leads)}")
    for tender in leads[:10]:
        print(f"- {tender['title']} | {tender['ocid']} | {tender['discovery_phrases']}")
    print("Discovery matches are NOT verified security contracts.")


if __name__ == "__main__":
    main()
