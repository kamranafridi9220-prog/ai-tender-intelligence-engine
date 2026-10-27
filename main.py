
# ============================================================
# AI TENDER INTELLIGENCE ENGINE
# UK Government Tender Discovery & Classification
# Lesson 14A - Reliable API Connection
# ============================================================

import json
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# ============================================================
# UK GOVERNMENT TENDER API
# ============================================================

API_URL = (
    "https://www.find-tender.service.gov.uk"
    "/api/1.0/ocdsReleasePackages"
    "?stages=tender&limit=100"
)


# ============================================================
# BUSINESS RELEVANCE CLASSIFICATION
# ============================================================

GUARDING_TERMS = [
    "manned guarding",
    "security guarding",
    "security officer",
    "security personnel",
    "mobile patrol",
    "key holding",
    "site security",
    "security services",
    "community asset security",
    "building security",
    "premises security"
]

TECHNOLOGY_TERMS = [
    "vehicle telematics",
    "tachograph",
    "cctv installation",
    "camera installation",
    "software licensing"
]


def classify_tender(title, description):

    text = f"{title} {description}".lower()

    guarding_matches = [
        term for term in GUARDING_TERMS
        if term in text
    ]

    technology_matches = [
        term for term in TECHNOLOGY_TERMS
        if term in text
    ]

    if guarding_matches and not technology_matches:
        return "GUARDING OPPORTUNITY"

    if technology_matches and not guarding_matches:
        return "TECHNOLOGY / EQUIPMENT"

    if guarding_matches and technology_matches:
        return "MIXED REQUIREMENTS - REVIEW"

    return "UNCLASSIFIED"


# ============================================================
# RELIABLE API CONNECTION WITH AUTOMATIC RETRIES
# ============================================================

def fetch_tenders():

    request = Request(
        API_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "AI-Tender-Intelligence-Engine/1.0"
        }
    )

    max_attempts = 3

    for attempt in range(1, max_attempts + 1):

        try:
            print(
                f"Connecting to UK Tender API "
                f"(attempt {attempt}/{max_attempts})"
            )

            with urlopen(request, timeout=60) as response:
                data = json.load(response)

            print("API connection successful")

            return data.get("releases", [])

        except (TimeoutError, URLError, HTTPError) as error:

            print(f"API request failed: {error}")

            if attempt == max_attempts:
                print("All connection attempts failed")
                raise

            wait_time = attempt * 5

            print(f"Retrying in {wait_time} seconds...")

            time.sleep(wait_time)


# ============================================================
# MAIN TENDER INTELLIGENCE ENGINE
# ============================================================

def main():

    print("=" * 55)
    print("AI TENDER INTELLIGENCE ENGINE")
    print("=" * 55)

    print("Searching UK government tenders...")

    releases = fetch_tenders()

    print(f"Tender releases received: {len(releases)}")

    guarding_count = 0
    technology_count = 0
    mixed_count = 0
    unclassified_count = 0

    for release in releases:

        tender = release.get("tender") or {}

        title = tender.get("title") or ""
        description = tender.get("description") or ""

        if not title.strip():
            continue

        category = classify_tender(
            title,
            description
        )

        if category == "GUARDING OPPORTUNITY":
            guarding_count += 1

        elif category == "TECHNOLOGY / EQUIPMENT":
            technology_count += 1

        elif category == "MIXED REQUIREMENTS - REVIEW":
            mixed_count += 1

        else:
            unclassified_count += 1

        if category != "UNCLASSIFIED":

            print("-" * 55)
            print("Tender:", title)
            print("Category:", category)
            print("OCID:", release.get("ocid", "Unknown"))

    print("\n" + "=" * 55)
    print("TENDER CLASSIFICATION SUMMARY")
    print("=" * 55)

    print("Guarding opportunities:", guarding_count)
    print("Technology contracts:", technology_count)
    print("Mixed requirements:", mixed_count)
    print("Unclassified tenders:", unclassified_count)

    print("=" * 55)
    print("Tender intelligence processing completed")
    print("=" * 55)


# ============================================================
# EXECUTE ENGINE
# ============================================================

if __name__ == "__main__":
    main()
