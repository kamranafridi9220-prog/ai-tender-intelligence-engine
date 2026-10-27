
"""AEGIS Lesson 26 — targeted security opportunity discovery.

Run: python opportunity_discovery.py
"""
from __future__ import annotations

from collections import Counter

from company_tender_matcher import create_company, match_company_to_tenders
from eligibility_engine import evaluate_eligibility
from hybrid_relevance import assess_relevance
from live_ai_matcher import fetch_tenders

TARGET = "TARGET SECURITY CONTRACT"
REVIEW = {
    "SECURITY-RELATED - REVIEW",
    "MANUAL REVIEW",
    "MIXED SCOPE - REVIEW",
    "RELEVANT CANDIDATE",
}


def as_dict(value):
    return value if isinstance(value, dict) else {}


def similarity_percent(value):
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return 0.0
    return round(number, 2)


def build_eligibility_input(tender):
    title = str(tender.get("title") or "")
    description = str(tender.get("description") or "")
    return {
        "title": title,
        "service": f"{title}. {description}",
        "location": (
            tender.get("location")
            if isinstance(tender.get("location"), str)
            else None
        ),
        "value": tender.get("value"),
        "certifications": tender.get("certifications"),
    }


def discover_opportunities(max_records=500, max_pages=5, days_back=90):
    company = create_company()
    print("AI OPPORTUNITY DISCOVERY ENGINE — LESSON 26", flush=True)
    print("Company:", getattr(company, "name", "Company profile"), flush=True)

    tenders = fetch_tenders(
        max_records=max_records,
        security_only=True,
        max_pages=max_pages,
        days_back=days_back,
    )
    print("Security discovery leads retrieved:", len(tenders), flush=True)

    ranked = match_company_to_tenders(company, tenders) if tenders else []
    opportunities = []
    counts = Counter()
    seen = set()

    for tender in ranked:
        if not isinstance(tender, dict):
            continue

        title = str(tender.get("title") or "")
        ocid = tender.get("ocid")
        identity = (
            ocid if ocid and ocid != "Unknown"
            else title.casefold()
        )
        if identity in seen:
            continue
        seen.add(identity)

        relevance = as_dict(assess_relevance(tender))
        decision = str(
            relevance.get("decision") or "MANUAL REVIEW"
        ).strip().upper()

        if decision != TARGET and decision not in REVIEW:
            decision = "NOT RELEVANT"

        counts[decision] += 1

        if decision != TARGET and decision not in REVIEW:
            continue

        assessment = as_dict(
            evaluate_eligibility(
                company,
                build_eligibility_input(tender)
            )
        )
        score = similarity_percent(
            tender.get("similarity", relevance.get("similarity"))
        )

        opportunities.append({
            "title": title,
            "ocid": ocid,
            "similarity": score,
            "category": relevance.get("category", "UNCLASSIFIED"),
            "relevance_decision": decision,
            "assessment": assessment,
            "value": tender.get("value"),
            "currency": tender.get("currency"),
            "locations": tender.get("locations") or [],
            "deadline": tender.get("deadline"),
            "cpv_codes": tender.get("cpv_codes") or [],
        })

    opportunities.sort(
        key=lambda item: (
            item["relevance_decision"] == TARGET,
            item["similarity"],
        ),
        reverse=True,
    )

    print("\nCLASSIFICATION SUMMARY", flush=True)
    print("Target security contracts:", counts[TARGET], flush=True)
    print(
        "Security-related / manual review:",
        sum(counts[key] for key in REVIEW),
        flush=True
    )
    print("Not relevant:", counts["NOT RELEVANT"], flush=True)
    print("Total classified:", sum(counts.values()), flush=True)
    print("Total shortlisted:", len(opportunities), flush=True)

    print("\nSHORTLISTED SECURITY OPPORTUNITIES", flush=True)

    if not opportunities:
        print("No target or review opportunities found in this scan.", flush=True)

    for item in opportunities[:20]:
        print("-" * 55)
        print("Title:", item["title"])
        print("Relevance:", item["relevance_decision"])
        print("AI similarity:", item["similarity"], "%")
        print(
            "Commercial screening:",
            item["assessment"].get("decision", "REVIEW")
        )
        print("Value:", item["value"], item["currency"] or "")
        print("Deadline:", item["deadline"] or "Not published")
        print("OCID:", item["ocid"])

    return opportunities


if __name__ == "__main__":
    discover_opportunities()
