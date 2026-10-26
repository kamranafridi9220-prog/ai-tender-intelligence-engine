
# Lesson 9: Evaluating tender classification

from main import classify_tender

examples = [
    {
        "title": "Security Guarding Contract",
        "description": "Security officers and mobile patrol",
        "expected": "GUARDING OPPORTUNITY"
    },
    {
        "title": "Vehicle Telematics",
        "description": "Tachograph and fleet tracking equipment",
        "expected": "TECHNOLOGY / EQUIPMENT"
    },
    {
        "title": "Integrated Security Contract",
        "description": "Manned guarding and CCTV installation",
        "expected": "MIXED REQUIREMENTS - REVIEW"
    },
    {
        "title": "Office Furniture Supply",
        "description": "Desks and office chairs",
        "expected": "UNCLASSIFIED"
    },
    {
        "title": "Community Asset Security",
        "description": "Security services for public buildings",
        "expected": "GUARDING OPPORTUNITY"
    }
]

correct = 0

for example in examples:
    predicted = classify_tender(
        example["title"],
        example["description"]
    )

    expected = example["expected"]
    is_correct = predicted == expected

    if is_correct:
        correct += 1

    print("Tender:", example["title"])
    print("Expected:", expected)
    print("Predicted:", predicted)
    print("Correct:", is_correct)
    print("-------------------------")

accuracy = correct / len(examples) * 100

print(f"Evaluation accuracy: {accuracy:.2f}%")
