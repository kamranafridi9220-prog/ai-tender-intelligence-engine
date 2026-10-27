
# Lesson 11: AI Semantic Tender Matching

from sentence_transformers import SentenceTransformer, util

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main():
    print("Loading AI semantic matching model...")

    model = SentenceTransformer(MODEL_NAME)

    company_services = (
        "We provide manned guarding, security officers, "
        "mobile patrols and premises protection."
    )

    tenders = [
        "Provision of on-site security personnel for buildings",
        "Supply of office desks and furniture",
        "Installation of vehicle tracking and tachograph systems",
        "Mobile security patrol services for commercial properties"
    ]

    descriptions = [company_services] + tenders

    embeddings = model.encode(
        descriptions,
        convert_to_tensor=True
    )

    company_embedding = embeddings[0]
    tender_embeddings = embeddings[1:]

    scores = util.cos_sim(
        company_embedding,
        tender_embeddings
    )[0]

    ranked = sorted(
        zip(tenders, scores.tolist()),
        key=lambda item: item[1],
        reverse=True
    )

    print("\nAI Semantic Matching Results")

    for title, score in ranked:
        print("--------------------------")
        print("Tender:", title)
        print(f"Similarity: {score:.2%}")


if __name__ == "__main__":
    main()
