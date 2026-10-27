
# AI Tender Intelligence Engine
# Lesson 15: Commercial Eligibility Engine

from company_profile import CompanyProfile


def evaluate_eligibility(company, tender):
    reasons = []
    review_items = []

    # 1. Service compatibility
    service_text = tender["service"].lower()

    compatible = any(
        service.lower() in service_text
        for service in company.services
    )

    if compatible:
        reasons.append("Service compatibility confirmed")
    else:
        reasons.append("Service compatibility not confirmed")

    # 2. Geographic coverage
    tender_location = tender.get("location")

    if not tender_location:
        location_status = "REVIEW"
        review_items.append("Tender location missing")
    elif tender_location.lower() in [
        location.lower() for location in company.locations
    ]:
        location_status = "PASS"
    else:
        location_status = "FAIL"
        reasons.append("Outside stated operating locations")

    # 3. Contract value
    value = tender.get("value")

    if value is None:
        value_status = "REVIEW"
        review_items.append("Contract value missing")
    elif (
        company.minimum_contract_value
        <= value
        <= company.maximum_contract_value
    ):
        value_status = "PASS"
    else:
        value_status = "FAIL"
        reasons.append("Outside preferred contract value range")

    # 4. Mandatory certifications
    required = tender.get("certifications")

    if required is None:
        certification_status = "REVIEW"
        review_items.append(
            "Certification requirements not verified"
        )
    else:
        company_certs = {
            cert.lower() for cert in company.certifications
        }

        missing = [
            cert for cert in required
            if cert.lower() not in company_certs
        ]

        if missing:
            certification_status = "FAIL"
            reasons.append(
                "Missing certifications: " + ", ".join(missing)
            )
        else:
            certification_status = "PASS"

    # Overall preliminary assessment
    if (
        location_status == "FAIL"
        or value_status == "FAIL"
        or certification_status == "FAIL"
    ):
        decision = "NOT SUITABLE - REVIEW"

    elif (
        not compatible
        or location_status == "REVIEW"
        or value_status == "REVIEW"
        or certification_status == "REVIEW"
    ):
        decision = "MANUAL REVIEW REQUIRED"

    else:
        decision = "PRELIMINARY MATCH"

    return {
        "decision": decision,
        "service_match": compatible,
        "location_status": location_status,
        "value_status": value_status,
        "certification_status": certification_status,
        "reasons": reasons,
        "review_items": review_items
    }


def main():
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

    # Fictional tender for testing
    tender = {
        "title": "London Security Guarding Contract",
        "service": "Manned guarding",
        "location": "London",
        "value": 500000,
        "certifications": []
    }

    result = evaluate_eligibility(company, tender)

    print("COMMERCIAL ELIGIBILITY ASSESSMENT")
    print("--------------------------------")
    print("Company:", company.name)
    print("Tender:", tender["title"])
    print("Decision:", result["decision"])
    print("Service match:", result["service_match"])
    print("Location:", result["location_status"])
    print("Contract value:", result["value_status"])
    print("Certifications:", result["certification_status"])
    print("Reasons:", result["reasons"])
    print("Review items:", result["review_items"])


if __name__ == "__main__":
    main()
