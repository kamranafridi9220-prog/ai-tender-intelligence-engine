
# AI Tender Intelligence Engine
# Lesson 17: Improved Opportunity Discovery

from company_tender_matcher import (
    create_company,
    match_company_to_tenders
)

from live_ai_matcher import fetch_tenders
from eligibility_engine import evaluate_eligibility
from main import classify_tender


def discover_opportunities():
    company = create_company()

    print("AI OPPORTUNITY DISCOVERY ENGINE")
    print("Company:", company.name)

    tenders = fetch_tenders()
    print("Tender releases retrieved:", len(tenders))

    ranked = match_company_to_tenders(
        company,
        tenders
    )

    opportunities = []

    for tender in ranked:
        category = classify_tender(
            tender["title"],
            tender["description"]
        )

        semantic_score = tender["similarity"]

        # Keep candidates for review, not confirmed matches.
        if (
            category == "UNCLASSIFIED"
            and semantic_score < 30
        ):
            continue

        structured_tender = {
            "title": tender["title"],
            "service": (
                tender["title"] + ". "
                + tender["description"]
            ),
            "location": None,
            "value": None,
            "certifications": None
        }

        assessment = evaluate_eligibility(
            company,
            structured_tender
        )

        opportunities.append({
            "title": tender["title"],
            "ocid": tender["ocid"],
            "similarity": semantic_score,
            "category": category,
            "assessment": assessment
        })

    opportunities.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    print("\nCANDIDATE OPPORTUNITIES FOR REVIEW")

    for item in opportunities[:10]:
        print("-" * 50)
        print("Title:", item["title"])
        print("AI similarity:", item["similarity"], "%")
        print("Category:", item["category"])
        print("Decision:", item["assessment"]["decision"])
        print("OCID:", item["ocid"])

    print("\nTotal candidates:", len(opportunities))


if __name__ == "__main__":
    discover_opportunities()
