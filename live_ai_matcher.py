
# Lesson 12: Live AI Tender Matching

import json
from urllib.request import Request, urlopen

from sentence_transformers import SentenceTransformer, util


API_URL = (
    "https://www.find-tender.service.gov.uk"
    "/api/1.0/ocdsReleasePackages"
    "?stages=tender&limit=100"
)

COMPANY_PROFILE = (
    "Professional security services including "
    "manned guarding, security officers, "
    "mobile patrols, key holding and "
    "commercial premises protection."
)


def fetch_tenders():
    request = Request(
        API_URL,
        headers={"Accept": "application/json"}
    )

    with urlopen(request, timeout=30) as response:
        data = json.load(response)

    tenders = []

    for release in data.get("releases", []):
        tender = release.get("tender") or {}

        title = tender.get("title") or ""
        description = tender.get("description") or ""

        if not title.strip():
            continue

        tenders.append({
            "title": title,
            "description": description,
            "ocid": release.get("ocid", "Unknown")
        })

    return tenders


def rank_tenders(tenders):
    if not tenders:
        return []

    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    texts = [
        COMPANY_PROFILE
    ] + [
        tender["title"] + ". " + tender["description"]
        for tender in tenders
    ]

    embeddings = model.encode(
        texts,
        convert_to_tensor=True
    )

    scores = util.cos_sim(
        embeddings[0],
        embeddings[1:]
    )[0].tolist()

    for tender, score in zip(tenders, scores):
        tender["similarity"] = round(score * 100, 2)

    return sorted(
        tenders,
        key=lambda tender: tender["similarity"],
        reverse=True
    )


def main():
    print("Fetching live UK government tenders...")

    tenders = fetch_tenders()
    print("Tenders retrieved:", len(tenders))

    ranked = rank_tenders(tenders)

    print("\nTOP 10 AI-MATCHED TENDERS")

    for tender in ranked[:10]:
        print("---------------------------")
        print("Title:", tender["title"])
        print("Similarity:", tender["similarity"], "%")
        print("OCID:", tender["ocid"])


if __name__ == "__main__":
    main()
