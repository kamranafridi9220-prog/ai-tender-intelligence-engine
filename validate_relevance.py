
"""
AI Tender Intelligence Engine
Lesson 21: Independent Synthetic Validation

Tests previously unused examples.
No model training or rule modification occurs.
"""

from hybrid_relevance import assess_relevance


VALIDATION_TENDERS = [
    {
        "title": "Static Guarding at Public Buildings",
        "description": "Provide static guarding at council offices.",
        "expected": 1,
    },
    {
        "title": "Night Watchmen for Industrial Estate",
        "description": "Provide overnight watchmen and site protection.",
        "expected": 1,
    },
    {
        "title": "Retail Loss Prevention Officers",
        "description": "Uniformed loss prevention officers at retail stores.",
        "expected": 1,
    },
    {
        "title": "Event Stewarding and Crowd Safety",
        "description": "Licensed stewards for venue entry and crowd management.",
        "expected": 1,
    },
    {
        "title": "Building Security Patrols",
        "description": "Regular security patrol of commercial buildings.",
        "expected": 1,
    },
    {
        "title": "Security Systems Installation",
        "description": "Supply and installation of CCTV cameras only.",
        "expected": 0,
    },
    {
        "title": "Cyber Security Monitoring",
        "description": "Remote monitoring of digital infrastructure.",
        "expected": 0,
    },
    {
        "title": "Financial Security Audit",
        "description": "Internal audit and financial assurance services.",
        "expected": 0,
    },
    {
        "title": "Hospital Medical Equipment",
        "description": "Supply diagnostic imaging equipment.",
        "expected": 0,
    },
    {
        "title": "Car Park Barrier Maintenance",
        "description": "Repair automated parking barriers.",
        "expected": 0,
    },
    {
        "title": "Office Reception Administration",
        "description": "Administrative reception and telephone duties only.",
        "expected": 0,
    },
    {
        "title": "Key Holding and Alarm Response",
        "description": "Key holding and mobile response to alarm activations.",
        "expected": 1,
    },
]


def main():
    tp = fp = tn = fn = 0

    print("=" * 55)
    print("INDEPENDENT SYNTHETIC VALIDATION")
    print("=" * 55)

    for tender in VALIDATION_TENDERS:

        record = {
            **tender,
            "similarity": 0
        }

        result = assess_relevance(record)

        predicted = int(
            result["decision"] == "RELEVANT CANDIDATE"
        )

        expected = tender["expected"]

        if expected == 1 and predicted == 1:
            tp += 1
        elif expected == 0 and predicted == 1:
            fp += 1
        elif expected == 0 and predicted == 0:
            tn += 1
        else:
            fn += 1

        print("-" * 55)
        print("Tender:", tender["title"])
        print("Expected:", expected)
        print("Predicted:", predicted)
        print("Decision:", result["decision"])

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
    )

    accuracy = (
        (tp + tn) / len(VALIDATION_TENDERS)
    )

    print("\nCONFUSION MATRIX")
    print("True positives:", tp)
    print("False positives:", fp)
    print("True negatives:", tn)
    print("False negatives:", fn)

    print("\nVALIDATION METRICS")
    print(f"Precision: {precision * 100:.2f}%")
    print(f"Recall: {recall * 100:.2f}%")
    print(f"F1 Score: {f1 * 100:.2f}%")
    print(f"Accuracy: {accuracy * 100:.2f}%")

    print("\nValidation completed")


if __name__ == "__main__":
    main()
