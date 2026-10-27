
# AI Tender Intelligence Engine
# Lesson 16: Live Tender Eligibility Assessment

import json

from company_tender_matcher import create_company
from live_ai_matcher import fetch_tenders
from eligibility_engine import evaluate_eligibility
from main import classify_tender


def extract_value(tender):
    value = tender.get("value") or {}

    amount = value.get("amount")

    if amount is None:
        return None

    currency = value.get("currency", "GBP")

    if currency != "GBP":
        return None

    try:
        return float(amount)
    except (TypeError, ValueError):
        return None


def extract_location(tender):
    # OCDS tender records can contain multiple
    # delivery locations or address structures.
    # We will implement full parsing later.
    return None


def main():
    company = create_company()

    print("LIVE COMMERCIAL ELIGIBILITY ENGINE")
    print("Company:", company.name)

    releases = fetch_tenders()

    print("Tender releases retrieved:", len(releases))

    results = []

    for release in releases:
        tender = release.get("tender") or {}

        title = tender.get("title") or ""
        description = tender.get("description") or ""

        if not title:
            continue

        category = classify_tender(
            title,
            description
        )

        if category not in [
            "GUARDING OPPORTUNITY",
            "MIXED REQUIREMENTS - REVIEW"
        ]:
            continue

        structured_tender = {
            "title": title,
            "service": title + ". " + description,
            "location": extract_location(tender),
            "value": extract_value(tender),
            "certifications": None
        }

        assessment = evaluate_eligibility(
            company,
            structured_tender
        )

        results.append({
            "title": title,
            "ocid": release.get("ocid"),
            "category": category,
            "assessment": assessment
        })

    print("\nPOTENTIAL BUSINESS OPPORTUNITIES")

    for item in results:
        print("-" * 50)
        print("Title:", item["title"])
        print("OCID:", item["ocid"])
        print("Category:", item["category"])
        print("Decision:", item["assessment"]["decision"])
        print(
            "Location:",
            item["assessment"]["location_status"]
        )
        print(
            "Contract value:",
            item["assessment"]["value_status"]
        )
        print(
            "Certifications:",
            item["assessment"]["certification_status"]
        )
        print(
            "Review items:",
            item["assessment"]["review_items"]
        )

    print("\nTotal potential opportunities:", len(results))


if __name__ == "__main__":
    main()
