
# ============================================================
# AI TENDER INTELLIGENCE ENGINE
# LESSON 24 - PROFESSIONAL SECURITY RELEVANCE ENGINE
# ============================================================

from company_tender_matcher import (
    create_company,
    match_company_to_tenders
)

from live_ai_matcher import fetch_tenders
from main import classify_tender


# ------------------------------------------------------------
# TARGET PROFESSIONAL SECURITY SERVICES
# ------------------------------------------------------------

TARGET_SERVICE_GROUPS = {
    "MANNED GUARDING": [
        "manned guarding",
        "security guarding",
        "security guard",
        "security guards",
        "security officer",
        "security officers",
        "security personnel",
        "static guarding",
        "guarding services",
        "security staffing",
        "site guarding"
    ],
    "MOBILE PATROLS": [
        "mobile patrol",
        "mobile security patrol",
        "security patrol services",
        "security patrols",
        "mobile guarding"
    ],
    "CCTV SECURITY": [
        "cctv monitoring",
        "cctv operator",
        "cctv operators",
        "cctv surveillance",
        "security control room",
        "remote cctv monitoring",
        "video surveillance monitoring"
    ],
    "ACCESS CONTROL": [
        "security access control",
        "access control officers",
        "security reception",
        "reception security",
        "security concierge",
        "front of house security",
        "visitor screening",
        "visitor access management"
    ],
    "KEY HOLDING AND RESPONSE": [
        "key holding",
        "keyholding",
        "alarm response",
        "alarm receiving centre",
        "security response services"
    ]
}


# ------------------------------------------------------------
# SECURITY-RELATED BUT AMBIGUOUS WORK
# ------------------------------------------------------------

RELATED_PHRASES = [
    "asset security",
    "community asset security",
    "opening and closing",
    "premises security",
    "building security",
    "site security",
    "security services",
    "security provision",
    "security arrangements"
]


# ------------------------------------------------------------
# CLEARLY UNRELATED PROCUREMENT
# ------------------------------------------------------------

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

    service_matches = {}

    for service_group, phrases in TARGET_SERVICE_GROUPS.items():
        matches = find_phrases(text, phrases)

        if matches:
            service_matches[service_group] = matches

    target_matches = list(dict.fromkeys(
        phrase
        for matches in service_matches.values()
        for phrase in matches
    ))

    related_matches = find_phrases(
        text,
        RELATED_PHRASES
    )

    unrelated_matches = find_phrases(
        text,
        UNRELATED_PHRASES
    )

    similarity = float(
        tender.get("similarity") or 0
    )

    category = classify_tender(
        title,
        description
    )

    if target_matches and not unrelated_matches:
        decision = "TARGET SECURITY CONTRACT"

    elif target_matches and unrelated_matches:
        decision = "SECURITY-RELATED - REVIEW"

    elif related_matches:
        decision = "SECURITY-RELATED - REVIEW"

    elif category in [
        "GUARDING OPPORTUNITY",
        "MIXED REQUIREMENTS - REVIEW"
    ]:
        decision = "SECURITY-RELATED - REVIEW"

    elif similarity >= 40:
        decision = "MANUAL REVIEW"

    else:
        decision = "NOT RELEVANT"

    return {
        "decision": decision,
        "similarity": similarity,
        "category": category,
        "guarding_matches": target_matches,
        "related_matches": related_matches,
        "unrelated_matches": unrelated_matches,
        "service_groups": list(service_matches.keys())
    }


def main():
    company = create_company()

    print("=" * 60)
    print("PROFESSIONAL SECURITY TENDER INTELLIGENCE")
    print("=" * 60)

    print("Company:", company.name)

    tenders = fetch_tenders()

    ranked = match_company_to_tenders(
        company,
        tenders
    )

    target = []
    review = []
    rejected = []

    for tender in ranked:
        result = assess_relevance(tender)

        record = {
            **tender,
            **result
        }

        if result["decision"] == "TARGET SECURITY CONTRACT":
            target.append(record)

        elif result["decision"] in [
            "SECURITY-RELATED - REVIEW",
            "MANUAL REVIEW"
        ]:
            review.append(record)

        else:
            rejected.append(record)

    print("Total analysed:", len(ranked))
    print("Target security contracts:", len(target))
    print("Manual review:", len(review))
    print("Not relevant:", len(rejected))

    print("\nTARGET SECURITY OPPORTUNITIES")

    for tender in target[:10]:
        print("-" * 60)
        print("Title:", tender.get("title"))
        print("Similarity:", tender.get("similarity"))
        print("Service groups:", tender["service_groups"])
        print("Evidence:", tender["guarding_matches"])
        print("OCID:", tender.get("ocid"))

    print("\nSECURITY-RELATED REVIEW")

    for tender in review[:10]:
        print("-" * 60)
        print("Title:", tender.get("title"))
        print("Decision:", tender["decision"])
        print("OCID:", tender.get("ocid"))


if __name__ == "__main__":
    main()
