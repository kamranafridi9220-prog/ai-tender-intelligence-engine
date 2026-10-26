
# AI Tender Intelligence Engine
# Lesson 7: Business Relevance Classification

import json
from urllib.request import Request, urlopen

GUARDING_TERMS = [
    "manned guarding",
    "security guarding",
    "security officer",
    "security personnel",
    "mobile patrol",
    "key holding",
    "site security"
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


def main():
    url = (
        "https://www.find-tender.service.gov.uk"
        "/api/1.0/ocdsReleasePackages"
        "?stages=tender&limit=100"
    )

    request = Request(
        url,
        headers={"Accept": "application/json"}
    )

    with urlopen(request, timeout=30) as response:
        data = json.load(response)

    releases = data.get("releases", [])

    print("AI Tender Intelligence Engine")
    print("Releases analysed:", len(releases))

    for release in releases:
        tender = release.get("tender", {})

        title = tender.get("title") or ""
        description = tender.get("description") or ""

        category = classify_tender(
            title,
            description
        )

        if category != "UNCLASSIFIED":
            print("---------------------------")
            print("Title:", title)
            print("Category:", category)
            print("OCID:", release.get("ocid"))


if __name__ == "__main__":
    main()
