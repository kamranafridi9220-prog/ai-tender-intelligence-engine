"""AEGIS live UK tender retrieval, security discovery and enrichment.

Compatible with older callers of fetch_tenders() and Lesson 25 options.
"""
from __future__ import annotations

import json
import random
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlparse, parse_qs
from urllib.request import Request, urlopen

BASE_URL = "https://www.find-tender.service.gov.uk"
API_URL = BASE_URL + "/api/1.0/ocdsReleasePackages?stages=tender&limit=100"
COMPANY_PROFILE = (
    "Professional security services: manned guarding, security officers, "
    "mobile patrols, CCTV monitoring, access control, key holding and premises protection."
)

# Discovery keywords are leads only; hybrid_relevance decides actual suitability.
SECURITY_TERMS = (
    "security guard", "security officer", "manned guarding", "guarding services",
    "mobile patrol", "key holding", "keyholding", "cctv monitoring",
    "security services", "security personnel", "access control",
    "asset security", "site security", "premises security",
)
SECURITY_CPV_PREFIXES = ("7971",)  # Security services, including guarding.
_CACHE = {}
_LAST_REQUEST = 0.0


def _retry_seconds(header, attempt, cap=90):
    if header:
        try:
            seconds = float(header)
            return max(0.0, min(seconds, cap))
        except (ValueError, TypeError):
            try:
                parsed = parsedate_to_datetime(header)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                seconds = (parsed - datetime.now(timezone.utc)).total_seconds()
                return max(0.0, min(seconds, cap))
            except (ValueError, TypeError, OverflowError):
                pass
    return min(2 ** attempt + random.uniform(0, 1), cap)


def request_json(url, attempts=4, timeout=45, min_interval=1.5):
    """Request JSON with bounded retries, Retry-After and per-process caching."""
    global _LAST_REQUEST
    if url in _CACHE:
        return _CACHE[url]
    for attempt in range(1, attempts + 1):
        wait = min_interval - (time.monotonic() - _LAST_REQUEST)
        if wait > 0:
            time.sleep(wait)
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
            retryable = error.code in (429, 500, 502, 503, 504)
            if not retryable or attempt == attempts:
                raise
            delay = _retry_seconds(error.headers.get("Retry-After"), attempt)
            print(f"API HTTP {error.code}; retry {attempt}/{attempts} in {delay:.1f}s", flush=True)
            time.sleep(delay)
        except (URLError, TimeoutError, ConnectionError) as error:
            if attempt == attempts:
                raise
            delay = _retry_seconds(None, attempt)
            print(f"API connection issue: {error}; retrying in {delay:.1f}s", flush=True)
            time.sleep(delay)
    raise RuntimeError("API request failed")


def extract_value(tender):
    value = tender.get("value") or {}
    if not isinstance(value, dict):
        return None, None
    amount = value.get("amount")
    try:
        return (float(amount) if amount is not None else None), value.get("currency")
    except (TypeError, ValueError):
        return None, value.get("currency")
