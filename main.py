
# AI Tender Intelligence Engine
# Lesson 6: Security Tender Matching

import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


SECURITY_KEYWORDS = [
    "security",
    "manned guarding",
    "guarding",
    "mobile patrol",
    "cctv",
    "access control",
    "key holding"
]


def calculate_match_score(title, description):
    text = (title + " " + description).lower()

    matched_keywords = []

    for keyword in SECURITY_KEYWORDS:
        if keyword in text:
            matched_keywords.append(keyword)

    score = (
        len(matched_keywords) / len(SECURITY_KEYWORDS)
    ) * 100

    return round(score, 2), matched_keywords


def main():
    print("AI Tender Intelligence Engine")
    print("Searching for security opportunities...")

    url = (
        "https://www.find-tender.service.gov.uk"
        "/api/1.0/ocdsReleasePackages"
        "?stages=tender&limit=100"
    )

    request = Request(
        url,
        headers={"Accept": "application/json"}
    )

    try:
        with urlopen(request, timeout=30) as response:
            data = json.load(response)

        releases = data.get("releases", [])

        print("Tender releases retrieved:", len(releases))

        matches = []

        for release in releases:
            tender = release.get("tender", {})

            title = tender.get("title") or ""
            description = tender.get("description") or ""

            score, keywords = calculate_match_score(
                title,
                description
            )

            if score > 0:
                matches.append({
                    "title": title,
                    "score": score,
                    "keywords": keywords,
                    "ocid": release.get("ocid")
                })

        matches.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        print("Matching tenders:", len(matches))

        for tender in matches:
            print("-------------------------")
            print("Title:", tender["title"])
            print("Match score:", tender["score"], "%")
            print("Keywords:", tender["keywords"])
            print("OCID:", tender["ocid"])

    except (HTTPError, URLError, TimeoutError) as error:
        print("API connection failed:", error)
        raise


if __name__ == "__main__":
    main()
