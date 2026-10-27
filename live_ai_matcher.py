"""AEGIS — live UK procurement retrieval, targeted discovery and enrichment.

Compatible with existing calls to fetch_tenders(), rank_tenders(),
fetch_consolidated_record() and enrich_tender().
"""
from __future__ import annotations

import json
import random
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin, urlparse, parse_qs
from urllib.request import Request, urlopen

BASE_URL = "https://www.find-tender.service.gov.uk"
API_ENDPOINT = BASE_URL + "/api/1.0/ocdsReleasePackages"
API_URL = API_ENDPOINT + "?stages=tender&limit=100"
COMPANY_PROFILE = (
    "Professional security services including manned guarding, security officers, "
    "mobile patrols, CCTV monitoring, access control, key holding and "
    "commercial premises protection."
)

# Cache is per Python process; it prevents duplicate requests within one workflow step.
_RESPONSE_CACHE = {}
_LAST_REQUEST_AT = 0.0
MIN_REQUEST_INTERVAL = 1.5
MAX_RETRY_WAIT = 120

SECURITY_TERMS = (
    "manned guarding", "security guard", "security officer", "security personnel",
    "guarding services", "security services", "mobile patrol", "key holding",
    "keyholding", "cctv monitoring", "security monitoring", "access control",
    "alarm response", "concierge security", "site security", "security patrol",
    "asset security",  # Discovery lead only; classifier must verify actual scope.
)
SECURITY_CPV_PREFIXES = ("7971", "7972")


def _retry_after_seconds(header_value):
    if not header_value:
        return None
    try:
        return max(0.0, float(header_value))
    except (TypeError, ValueError):
        try:
            retry_at = parsedate_to_datetime(header_value)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


def request_json(url, attempts=5, timeout=45, use_cache=True):
    """Retrieve JSON with throttling, bounded retries and 429 Retry-After support."""
    global _LAST_REQUEST_AT
    if use_cache and url in _RESPONSE_CACHE:
        return _RESPONSE_CACHE[url]

    attempts = max(1, int(attempts))
    for attempt in range(1, attempts + 1):
        elapsed = time.monotonic() - _LAST_REQUEST_AT
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        request = Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "AEGIS-Tender-Intelligence/1.1 (public procurement research)",
        })
        _LAST_REQUEST_AT = time.monotonic()
        try:
            with urlopen(request, timeout=timeout) as response:
                data = json.load(response)
            if use_cache:
                _RESPONSE_CACHE[url] = data
            return data
        except HTTPError as error:
            retryable = error.code in (429, 500, 502, 503, 504)
            if not retryable or attempt == attempts:
                raise
            retry_after = _retry_after_seconds(error.headers.get("Retry-After"))
            backoff = min(MAX_RETRY_WAIT, (2 ** (attempt - 1)) * 3 + random.uniform(0, 1))
            delay = min(MAX_RETRY_WAIT, retry_after if retry_after is not None else backoff)
            print(f"API HTTP {error.code}; retry {attempt}/{attempts} after {delay:.1f}s", flush=True)
            time.sleep(delay)
        except (URLError, TimeoutError, OSError) as error:
            if attempt == attempts:
                raise
            delay = min(MAX_RETRY_WAIT, (2 ** (attempt - 1)) * 2 + random.uniform(0, 1))
            print(f"API connection error: {error}; retrying in {delay:.1f}s", flush=True)
            time.sleep(delay)
    raise RuntimeError("API request retries exhausted")

