
"""
AI TENDER INTELLIGENCE ENGINE

Lesson 24:
Professional Security Relevance Evaluation

Evaluates:
- Target security contract detection
- Security-related manual review
- Unrelated tender rejection
- Precision, Recall, F1 and Accuracy

IMPORTANT:
These are synthetic tests, not real-world
procurement accuracy measurements.
"""

import unittest

from hybrid_relevance import assess_relevance


TARGET = "TARGET SECURITY CONTRACT"
REVIEW = "SECURITY-RELATED - REVIEW"
UNRELATED = "NOT RELEVANT"


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
        "title": "Integrated Guarding and CCTV",
        "description": "Manned guarding and CCTV monitoring",
        "similarity": 55,
        "expected": 1
    },
    {
        "title": "Reception and Access Control",
        "description": (
            "Security reception and visitor access management"
        ),
        "similarity": 42,
        "expected": 1
    },
    {
        "title": "CCTV Monitoring Services",
        "description": (
            "24-hour CCTV operators and remote CCTV monitoring"
        ),
        "similarity": 58,
        "expected": 1
    },
    {
        "title": "Security Officer Provision",
        "description": (
            "Security officers required for commercial buildings"
        ),
        "similarity": 67,
        "expected": 1
    },
    {
        "title": "Key Holding and Alarm Response",
        "description": (
            "Key holding and alarm response services"
        ),
        "similarity": 61,
        "expected": 1
    },
    {
        "title": "Community Asset Security",
        "description": (
            "Opening and closing community sports facilities"
        ),
        "similarity": 35,
        "expected": 0,
        "expected_decision": REVIEW
    },
    {
        "title": "Walton Community Asset Security",
        "description": (
            "Opening and closing sports grounds and car parks"
        ),
        "similarity": 34.94,
        "expected": 0,
        "expected_decision": REVIEW
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
        "description": (
            "Tracking systems and tachograph installation"
        ),
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
        "description": (
            "Maintenance of fire suppression systems"
        ),
        "similarity": 31,
        "expected": 0
    }
]


# --------------------------------------------------
# PREDICTION
# --------------------------------------------------

def predict_relevance(tender):
    result = assess_relevance(tender)

    return int(
        result["decision"] == TARGET
    )


# --------------------------------------------------
# PERFORMANCE METRICS
# --------------------------------------------------

def calculate_metrics(dataset):
    tp = fp = tn = fn = 0

    for tender in dataset:
        expected = tender["expected"]
        result = assess_relevance(tender)
        predicted = int(result["decision"] == TARGET)

        if expected == 1 and predicted == 1:
            tp += 1

        elif expected == 0 and predicted == 1:
            fp += 1

        elif expected == 0 and predicted == 0:
            tn += 1

        elif expected == 1 and predicted == 0:
            fn += 1

        print("-" * 55)
        print("Tender:", tender["title"])
        print("Expected:", expected)
        print("Predicted:", predicted)
        print("Decision:", result["decision"])

    precision = (
        tp / (tp + fp)
        if tp + fp else 0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn else 0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
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


# --------------------------------------------------
# UNIT TESTS
# --------------------------------------------------

class TestProfessionalSecurityRelevance(unittest.TestCase):

    def test_target_contracts(self):
        for tender in TEST_TENDERS:
            if tender["expected"] == 1:
                with self.subTest(title=tender["title"]):
                    self.assertEqual(
                        assess_relevance(tender)["decision"],
                        TARGET
                    )

    def test_walton_style_contracts_require_review(self):
        for tender in TEST_TENDERS:
            if tender.get("expected_decision") == REVIEW:
                with self.subTest(title=tender["title"]):
                    self.assertEqual(
                        assess_relevance(tender)["decision"],
                        REVIEW
                    )

    def test_unrelated_contracts_not_shortlisted(self):
        for tender in TEST_TENDERS:
            if tender["expected"] == 0:
                with self.subTest(title=tender["title"]):
                    self.assertNotEqual(
                        assess_relevance(tender)["decision"],
                        TARGET
                    )

    def test_metric_calculation(self):
        metrics = calculate_metrics(TEST_TENDERS)

        total = (
            metrics["TP"]
            + metrics["FP"]
            + metrics["TN"]
            + metrics["FN"]
        )

        self.assertEqual(total, len(TEST_TENDERS))

        for name in [
            "precision",
            "recall",
            "f1",
            "accuracy"
        ]:
            self.assertGreaterEqual(metrics[name], 0)
            self.assertLessEqual(metrics[name], 1)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("PROFESSIONAL SECURITY RELEVANCE EVALUATION")
    print("=" * 60)

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
