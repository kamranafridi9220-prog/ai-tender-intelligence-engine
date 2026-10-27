
# Lesson 14: Company-Based AI Tender Matching

from sentence_transformers import SentenceTransformer, util

from company_profile import CompanyProfile
from live_ai_matcher import fetch_tenders


def create_company():
    company = CompanyProfile(
        name="Example Security Services Ltd",
        industry="Private Security",
        services=[
            "Manned guarding",
            "Security officers",
            "Mobile patrols",
            "Key holding",
            "Commercial premises security"
        ],
        locations=["London", "Greater London"],
        minimum_contract_value=100000,
        maximum_contract_value=2000000,
        certifications=[]
    )

    company.validate()
    return company


def match_company_to_tenders(company, tenders):
    if not tenders:
        return []

    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    company_text = company.service_description()

    tender_texts = [
        (tender["title"] + ". " + tender["description"])
        for tender in tenders
    ]

    embeddings = model.encode(
        [company_text] + tender_texts,
        convert_to_tensor=True
    )

    scores = util.cos_sim(
        embeddings[0],
        embeddings[1:]
    )[0].tolist()

    results = []

    for tender, score in zip(tenders, scores):
        results.append({
            **tender,
            "similarity": round(score * 100, 2)
        })

    return sorted(
        results,
        key=lambda item: item["similarity"],
        reverse=True
    )


def main():
    company = create_company()

    print("Company:", company.name)
    print("Retrieving live UK tenders...")

    tenders = fetch_tenders()
    print("Tenders retrieved:", len(tenders))

    matches = match_company_to_tenders(company, tenders)

    print("\nTOP 10 COMPANY-MATCHED TENDERS")

    for tender in matches[:10]:
        print("--------------------------")
        print("Title:", tender["title"])
        print("Similarity:", tender["similarity"], "%")
        print("OCID:", tender["ocid"])


if __name__ == "__main__":
    main()
