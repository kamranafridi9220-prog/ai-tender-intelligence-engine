
"""AEGIS: live UK tender retrieval, semantic matching and OCDS enrichment."""
from __future__ import annotations

import json
import random
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen

BASE_URL = "https://www.find-tender.service.gov.uk"
API_URL = BASE_URL + "/api/1.0/ocdsReleasePackages?stages=tender&limit=100"
COMPANY_PROFILE = (
    "Professional security services including manned guarding, security officers, "
    "mobile patrols, CCTV monitoring, access control, key holding and premises protection."
)
SECURITY_TERMS = (
    "security guard", "security officer", "manned guarding", "guarding services",
    "mobile patrol", "key holding", "keyholding", "cctv monitoring",
    "security services", "security personnel", "access control",
    "asset security", "site security", "premises security",
)
SECURITY_CPV_PREFIXES = ("7971",)
_CACHE = {}
_LAST_REQUEST = 0.0


def _retry_delay(value, attempt, maximum=90):
    if value:
        try:
            return min(max(float(value), 0.0), maximum)
        except (ValueError, TypeError):
            try:
                dt = parsedate_to_datetime(value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return min(max((dt - datetime.now(timezone.utc)).total_seconds(), 0), maximum)
            except (ValueError, TypeError, OverflowError):
                pass
    return min(2 ** attempt + random.random(), maximum)


def request_json(url, attempts=4, timeout=45, min_interval=1.5):
    """Cache identical requests within one process and retry transient failures."""
    global _LAST_REQUEST
    if url in _CACHE:
        return _CACHE[url]
    for attempt in range(1, attempts + 1):
        remaining = min_interval - (time.monotonic() - _LAST_REQUEST)
        if remaining > 0:
            time.sleep(remaining)
        request = Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "AEGIS-Tender-Intelligence/1.0",
        })
        try:
            _LAST_REQUEST = time.monotonic()
            with urlopen(request, timeout=timeout) as response:
                data = json.load(response)
            _CACHE[url] = data
            return data
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == attempts:
                raise
            delay = _retry_delay(error.headers.get("Retry-After"), attempt)
            print(f"HTTP {error.code}: retrying in {delay:.1f}s", flush=True)
            time.sleep(delay)
        except (URLError, TimeoutError, ConnectionError) as error:
            if attempt == attempts:
                raise
            delay = _retry_delay(None, attempt)
            print(f"Network error {error}: retrying in {delay:.1f}s", flush=True)
            time.sleep(delay)
    raise RuntimeError("Tender API request failed")


def extract_value(tender):
    value = tender.get("value") or {}
    if not isinstance(value, dict):
        return None, None
    amount = value.get("amount")
    try:
        return (float(amount) if amount is not None else None), value.get("currency")
    except (ValueError, TypeError):
        return None, value.get("currency")


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
            place = next((str(x) for x in (
                delivery.get("addressLocality"), delivery.get("region"),
                delivery.get("countryName"), address.get("addressLocality"),
                address.get("region"), address.get("countryName"),
            ) if x), None)
            if place:
                locations.append(place)
    return list(dict.fromkeys(locations))


def extract_cpv_codes(tender):
    codes = []
    for item in tender.get("items") or []:
        if not isinstance(item, dict):
            continue
        entries = [item.get("classification")] + list(item.get("additionalClassifications") or [])
        for entry in entries:
            if isinstance(entry, dict) and entry.get("id"):
                codes.append(str(entry["id"]))
    return list(dict.fromkeys(codes))


def _parse_date(value):
    if not value:
        return None
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _next_url(data, current):
    """Follow only explicit, same-host API pagination links."""
    candidate = data.get("next") or data.get("nextPage")
    links = data.get("links") or {}
    if not candidate and isinstance(links, dict):
        candidate = links.get("next")
    if not candidate and isinstance(links, list):
        for link in links:
            if isinstance(link, dict) and link.get("rel") == "next":
                candidate = link
                break
    if isinstance(candidate, dict):
        candidate = candidate.get("href") or candidate.get("url")
    if not isinstance(candidate, str) or not candidate:
        return None
    result = urljoin(current, candidate)
    if urlparse(result).netloc != urlparse(BASE_URL).netloc:
        return None
    return result


def _normalise_release(release):
    tender = release.get("tender") or {}
    if not isinstance(tender, dict):
        return None
    title = str(tender.get("title") or "").strip()
    if not title:
        return None
    description = str(tender.get("description") or "")
    value, currency = extract_value(tender)
    return {
        "title": title, "description": description, "service": description or None,
        "ocid": release.get("ocid") or "Unknown", "value": value,
        "currency": currency, "locations": extract_locations(tender),
        "location": None, "cpv_codes": extract_cpv_codes(tender),
        "deadline": (tender.get("tenderPeriod") or {}).get("endDate"),
        "certifications": None,
    }


def _security_lead(tender):
    text = (tender["title"] + " " + tender["description"]).lower()
    return any(term in text for term in SECURITY_TERMS) or any(
        str(code).startswith(SECURITY_CPV_PREFIXES)
        for code in tender.get("cpv_codes") or []
    )


def fetch_tenders(max_records=100, security_only=False, max_pages=5, days_back=None):
    """Fetch deduplicated tender notices; security_only is lead discovery, not classification."""
    max_records = max(1, int(max_records))
    max_pages = max(1, int(max_pages))
    cutoff = None if days_back is None else datetime.now(timezone.utc) - timedelta(days=max(0, int(days_back)))
    results = {}
    url = API_URL
    visited = set()
    pages = 0
    while url and url not in visited and pages < max_pages and len(results) < max_records:
        visited.add(url)
        data = request_json(url)
        pages += 1
        for release in data.get("releases") or []:
            if not isinstance(release, dict):
                continue
            date = _parse_date(release.get("date"))
            if cutoff and date and date < cutoff:
                continue
            tender = _normalise_release(release)
            if not tender or (security_only and not _security_lead(tender)):
                continue
            key = tender["ocid"] if tender["ocid"] != "Unknown" else tender["title"].casefold()
            if key not in results:
                results[key] = tender
            if len(results) >= max_records:
                break
        url = _next_url(data, url)
    print(f"Discovery: {pages} page(s), {len(results)} unique tenders, security_only={security_only}", flush=True)
    return list(results.values())


def rank_tenders(tenders):
    """Rank notices against the security company profile using MiniLM."""
    if not tenders:
        return []
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    texts = [COMPANY_PROFILE] + [
        str(t.get("title") or "") + ". " + str(t.get("description") or "")
        for t in tenders
    ]
    embeddings = model.encode(texts, convert_to_tensor=True)
    scores = util.cos_sim(embeddings[0], embeddings[1:])[0].tolist()
    ranked = [{**t, "similarity": round(float(score) * 100, 2)} for t, score in zip(tenders, scores)]
    return sorted(ranked, key=lambda t: t["similarity"], reverse=True)


def fetch_consolidated_record(ocid):
    if not ocid or ocid == "Unknown":
        return None
    url = BASE_URL + "/api/1.0/ocdsRecordPackages/" + quote(str(ocid), safe="")
    data = request_json(url)
    for record in data.get("records") or []:
        if isinstance(record, dict) and isinstance(record.get("compiledRelease"), dict):
            return record["compiledRelease"]
    return None


def enrich_tender(tender):
    record = fetch_consolidated_record(tender.get("ocid"))
    if not record:
        return {**tender, "enrichment_status": "NOT AVAILABLE"}
    details = record.get("tender") or {}
    lots = [lot for lot in details.get("lots") or [] if isinstance(lot, dict)]
    amount, currency = extract_value(details)
    description = details.get("description") or tender.get("description") or ""
    return {
        **tender,
        "description": description,
        "service": description,
        "lot_descriptions": [lot["description"] for lot in lots if lot.get("description")],
        "contract_periods": [lot["contractPeriod"] for lot in lots if isinstance(lot.get("contractPeriod"), dict)],
        "deadline": (details.get("tenderPeriod") or {}).get("endDate") or tender.get("deadline"),
        "value": amount if amount is not None else tender.get("value"),
        "currency": currency or tender.get("currency"),
        "locations": extract_locations(details) or tender.get("locations") or [],
        "location": None,
        "cpv_codes": extract_cpv_codes(details) or tender.get("cpv_codes") or [],
        "enrichment_status": "ENRICHED",
    }


def main():
    print("AEGIS — LIVE UK TENDER MATCHER")
    tenders = fetch_tenders()
    print("Tenders retrieved:", len(tenders))
    for tender in tenders[:5]:
        print("Title:", tender["title"])
        print("Value:", tender["value"], tender["currency"])
        print("Deadline:", tender["deadline"])


if __name__ == "__main__":
    main()
