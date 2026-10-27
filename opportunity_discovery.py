"""AEGIS — Lesson 26: targeted security opportunity discovery.

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
    """Accept dictionary results without inventing classification fields."""
    return value if isinstance(value, dict) else {}


def get_similarity(tender):
    try:
        return round(float(tender.get("similarity") or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def assess_security(tender):
    """Use the existing evidence-based hybrid classifier."""
    result = as_dict(assess_relevance(tender))
    decision = str(result.get("decision") or "MANUAL REVIEW").strip().upper()
    if decision != TARGET and decision not in REVIEW:
        decision = "NOT RELEVANT"
    return result, decision


def build_eligibility_input(tender):
    return {
        "title": tender.get("title") or "",
        "service": " ".join(
            str(value)
            for value in (
                tender.get("title") or "",
                tender.get("description") or "",
            )
            if value
        ),
        # Broad UK region codes do not establish a company's local coverage.
        "location": tender.get("location"),
        "value": tender.get("value"),
        "certifications": tender.get("certifications"),
    }


def discover_opportunities(max_records=500, max_pages=5, days_back=90):
    company = create_company()
    print("AI OPPORTUNITY DISCOVERY ENGINE — LESSON 26")
    print("Company:", getattr(company, "name", "Company profile"))

    tenders = fetch_tenders(
        max_records=max_records,
        security_only=True,
        max_pages=max_pages,
        days_back=days_back,
    )
    print("Security discovery leads retrieved:", len(tenders))

    if not tenders:
        print("No discovery leads returned. Check API coverage and date window.")
        return []

    # Preserve the company matching model while letting the hybrid classifier
    # decide which notices are actually security-related.
    ranked = match_company_to_tenders(company, tenders)
    opportunities = []
    counts = Counter()

    for tender in ranked:
        evidence, decision = assess_security(tender)
        counts[decision] += 1
        if decision != TARGET and decision not in REVIEW:
            continue

        # Eligibility is preliminary and must not override scope classification.
        assessment = evaluate_eligibility(company, build_eligibility_input(tender))
        assessment = as_dict(assessment)

               opportunities.append({
            "title": title,
            "ocid": ocid,
            "similarity": round(score, 2),
            "category": relevance.get("category", "UNCLASSIFIED"),
            "relevance_decision": decision,
            "assessment": assessment,
            "value": value,
            "currency": tender.get("currency"),
            "locations": locations,
            "deadline": tender.get("deadline"),
            "cpv_codes": tender.get("cpv_codes") or [],
        })
