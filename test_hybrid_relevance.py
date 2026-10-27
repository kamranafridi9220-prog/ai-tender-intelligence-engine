
"""
AI TENDER INTELLIGENCE ENGINE

Lesson 19:
Hybrid Relevance Classification Evaluation

Measures:
- Precision
- Recall
- F1 Score
- Accuracy

Evaluation uses synthetic labelled examples.
"""

import unittest

from hybrid_relevance import assess_relevance


# --------------------------------------------------
# SYNTHETIC EVALUATION DATASET
# --------------------------------------------------

TEST_TENDERS = [
    {
        "title": "Manned Guarding Services",
        "description": "Security officers required for buildings",
        "similarity": 65,
        "expected": 1
    },
    {
        "title": "Mobile Patrol Contract",
        "description": "Mobile patrol and key holding services",
        "similarity": 62,
        "expected": 1
    },
    {
        "title": "Commercial Premises Security",
        "description": "Security guarding for commercial premises",
        "similarity": 60,
        "expected": 1
    },
    {
        "title": "Community Asset Security",
        "description": "Protection of community buildings",
        "similarity": 35,
        "expected": 1
    },
    {
        "title": "Integrated Guarding and CCTV",
        "description": "Manned guarding and CCTV installation",
        "similarity": 55,
        "expected": 1
    },
    {
        "title": "Reception and Access Control",
        "description": "Reception staff and visitor access management",
        "similarity": 42,
        "expected": 1
    },
    {
        "title": "Banking and Merchant Services",
        "description": "Payment processing services",
        "similarity": 33,
        "expected": 0
    },
    {
        "title": "Teleradiology Service",
        "description": "Remote medical imaging reporting",
        "similarity": 32,
        "expected": 0
    },
    {
        "title": "Office Furniture Supply",
        "description": "Supply of desks and chairs",
        "similarity": 22,
        "expected": 0
    },
    {
        "title": "Vehicle Telematics",
        "description": "Tracking systems and tachograph installation",
        "similarity": 30,
        "expected": 0
    },
    {
        "title": "Internal Audit Services",
        "description": "Financial audit and assurance",
        "similarity": 32,
        "expected": 0
    },
    {
        "title": "Fire Suppression Maintenance",
        "description": "Maintenance of fire suppression systems",
        "similarity": 31,
        "expected": 0
    }
]


def predict_relevance(tender):
    result = assess_relevance(tender)

    # Only clearly relevant candidates count as
    # positive automatic shortlist decisions.
    # Manual review is not a confirmed positive.
    return int(
        result["decision"] == "RELEVANT CANDIDATE"
    )


def calculate_metrics(dataset):
    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for tender in dataset:
        expected = tender["expected"]
        predicted = predict_relevance(tender)

        if expected == 1 and predicted == 1:
            tp += 1

        elif expected == 0 and predicted == 1:
            fp += 1

        elif expected == 0 and predicted == 0:
            tn += 1

        elif expected == 1 and predicted == 0:
            fn += 1

        result = assess_relevance(tender)

        print("-" * 50)
        print("Tender:", tender["title"])
        print("Expected:", expected)
        print("Predicted:", predicted)
        print("Decision:", result["decision"])

    precision = (
        tp / (tp + fp)
        if (tp + fp) else 0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) else 0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) else 0
    )

    accuracy = (
        (tp + tn) / len(dataset)
        if dataset else 0
    )

    return {
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy
    }


class TestHybridRelevance(unittest.TestCase):

    def test_metric_calculation(self):
        metrics = calculate_metrics(TEST_TENDERS)

        self.assertEqual(
            metrics["TP"] + metrics["FP"]
            + metrics["TN"] + metrics["FN"],
            len(TEST_TENDERS)
        )

        for metric in [
            "precision",
            "recall",
            "f1",
            "accuracy"
        ]:
            self.assertGreaterEqual(metrics[metric], 0)
            self.assertLessEqual(metrics[metric], 1)

    def test_known_guarding_contract(self):
        tender = TEST_TENDERS[0]
        self.assertEqual(predict_relevance(tender), 1)

    def test_known_unrelated_contract(self):
        tender = TEST_TENDERS[6]
        self.assertEqual(predict_relevance(tender), 0)


if __name__ == "__main__":
    print("=" * 55)
    print("HYBRID TENDER CLASSIFICATION EVALUATION")
    print("=" * 55)

    metrics = calculate_metrics(TEST_TENDERS)

    print("\nCONFUSION MATRIX")
    print("True positives:", metrics["TP"])
    print("False positives:", metrics["FP"])
    print("True negatives:", metrics["TN"])
    print("False negatives:", metrics["FN"])

    print("\nPERFORMANCE METRICS")
    print(
        f"Precision: {metrics['precision'] * 100:.2f}%"
    )
    print(
        f"Recall: {metrics['recall'] * 100:.2f}%"
    )
    print(
        f"F1 Score: {metrics['f1'] * 100:.2f}%"
    )
    print(
        f"Accuracy: {metrics['accuracy'] * 100:.2f}%"
    )

    print("\nRUNNING UNIT TESTS")
    unittest.main()
