
# Lesson 8: Testing our tender classifier

import unittest

from main import classify_tender


class TestTenderClassifier(unittest.TestCase):

    def test_guarding_contract(self):
        result = classify_tender(
            "Security Guarding Services",
            "Provision of security officers and mobile patrols"
        )
        self.assertEqual(
            result,
            "GUARDING OPPORTUNITY"
        )

    def test_technology_contract(self):
        result = classify_tender(
            "Vehicle Telematics Contract",
            "Supply of tachograph equipment"
        )
        self.assertEqual(
            result,
            "TECHNOLOGY / EQUIPMENT"
        )

    def test_mixed_contract(self):
        result = classify_tender(
            "Integrated Security Services",
            "Security guarding and CCTV installation"
        )
        self.assertEqual(
            result,
            "MIXED REQUIREMENTS - REVIEW"
        )

    def test_unclassified_contract(self):
        result = classify_tender(
            "Office Furniture Supply",
            "Supply of desks and chairs"
        )
        self.assertEqual(
            result,
            "UNCLASSIFIED"
        )


if __name__ == "__main__":
    unittest.main()
