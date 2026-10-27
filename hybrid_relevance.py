
# ============================================================
# AI TENDER INTELLIGENCE ENGINE
# Lesson 18 - Hybrid Tender Relevance Engine
# ============================================================

from company_tender_matcher import (
    create_company,
    match_company_to_tenders
)

from live_ai_matcher import fetch_tenders
from main import classify_tender


# Specific commercial service indicators.
# These are intentionally more selective than generic
# words such as "security", "services" or "contract".

GUARDING_PHRASES = [
    "manned guarding",
    "security guarding",
    "security officer",
    "security personnel",
    "mobile patrol",
    "key holding",
    "keyholding",
    "static guarding",
    "concierge security",
    "building security",
    "premises security",
    "site security",
    "asset security",
    "guarding services",
    "security patrol"
    "reception security",
    "security reception",
    "visitor access management",
    "visitor screening",
    "security concierge",
    "front of house security",
    "access control officers",
    "reception and access control"
]

# Strong indicators of unrelated procurement categories.
# A tender containing one of these is not automatically
# rejected if it also has a genuine guarding requirement.

UNRELATED_PHRASES = [
    "teleradiology",
    "medical equipment",
    "injection equipment",
    "banking services",
    "merchant services",
    "internal audit",
    "mental health services",
    "debt advice",
    "electricity meter",
    "tachograph",
    "vehicle telematics",
    "fire suppression systems"
]


def find_phrases(text, phrases):
    return [
        phrase
        for phrase in phrases
        if phrase in text
    ]


def assess_relevance(tender):
    title = tender.get("title") or ""
    description = tender.get("description") or ""

    text = f"{title} {description}".lower()

    guarding_matches = find_phrases(
        text, GUARDING_PHRASES
    )

    unrelated_matches = find_phrases(
        text, UNRELATED_PHRASES
    )

    similarity = float(
        tender.get("similarity", 0)
    )

    category = classify_tender(
        title, description
    )

    # Strong positive service evidence
    if guarding_matches and not unrelated_matches:
        decision = "RELEVANT CANDIDATE"

    # Possible mixed-scope contract
    elif guarding_matches and unrelated_matches:
        decision = "MIXED SCOPE - REVIEW"

    # Strong negative evidence without guarding evidence
    elif unrelated_matches:
        decision = "NOT RELEVANT"

    # Ambiguous contracts require further examination
    elif category in [
        "GUARDING OPPORTUNITY",
        "MIXED REQUIREMENTS - REVIEW"
    ]:
        decision = "MANUAL REVIEW"

    elif similarity >= 40:
        decision = "MANUAL REVIEW"

    else:
        decision = "NOT RELEVANT"

    return {
        "decision": decision,
        "similarity": similarity,
        "category": category,
        "guarding_matches": guarding_matches,
        "unrelated_matches": unrelated_matches
    }


def main():
    company = create_company()

    print("=" * 55)
    print("HYBRID AI TENDER RELEVANCE ENGINE")
    print("=" * 55)
    print("Company:", company.name)

    tenders = fetch_tenders()

    print("Live tenders retrieved:", len(tenders))

    ranked = match_company_to_tenders(
        company, tenders
    )

    relevant = []
    review = []
    rejected = []

    for tender in ranked:
        result = assess_relevance(tender)

        record = {
            **tender,
            **result
        }

        if result["decision"] == "RELEVANT CANDIDATE":
            relevant.append(record)

        elif result["decision"] in [
            "MANUAL REVIEW",
            "MIXED SCOPE - REVIEW"
        ]:
            review.append(record)

        else:
            rejected.append(record)

    print("\nRELEVANT GUARDING CANDIDATES")

    for tender in relevant[:10]:
        print("-" * 55)
        print("Title:", tender["title"])
        print("Similarity:", tender["similarity"], "%")
        print("Decision:", tender["decision"])
        print(
            "Evidence:",
            tender["guarding_matches"]
        )
        print("OCID:", tender.get("ocid"))

    print("\nMANUAL REVIEW CANDIDATES")

    for tender in review[:5]:
        print("-" * 55)
        print("Title:", tender["title"])
        print("Decision:", tender["decision"])
        print("Similarity:", tender["similarity"], "%")
        print("OCID:", tender.get("ocid"))

    print("\n" + "=" * 55)
    print("DISCOVERY SUMMARY")
    print("=" * 55)
    print("Total analysed:", len(ranked))
    print("Relevant candidates:", len(relevant))
    print("Manual review:", len(review))
    print("Not relevant:", len(rejected))
    print("=" * 55)


if __name__ == "__main__":
    main()
