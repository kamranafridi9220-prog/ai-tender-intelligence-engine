

def assess_security(tender):
    """Use the existing evidence-based hybrid classifier."""
    result = as_dict(assess_relevance(tender))
    decision = str(result.get("decision") or "MANUAL REVIEW").strip().upper()
    if decision != TARGET and decision not in REVIEW:
        decision = "NOT RELEVANT"
    return result, decision


def build_eligibility_input(tender):
    return {
        "title": tender.get("title") or "",
        "service": " ".join(
            str(value)
            for value in (
                tender.get("title") or "",
                tender.get("description") or "",
            )
            if value
        ),
        # Broad UK region codes do not establish a company's local coverage.
        "location": tender.get("location"),
        "value": tender.get("value"),
        "certifications": tender.get("certifications"),
    }


def discover_opportunities(max_records=500, max_pages=5, days_back=90):
    company = create_company()
    print("AI OPPORTUNITY DISCOVERY ENGINE — LESSON 26")
    print("Company:", getattr(company, "name", "Company profile"))

    tenders = fetch_tenders(
        max_records=max_records,
        security_only=True,
        max_pages=max_pages,
        days_back=days_back,
    )
    print("Security discovery leads retrieved:", len(tenders))

    if not tenders:
        print("No discovery leads returned. Check API coverage and date window.")
        return []

    # Preserve the company matching model while letting the hybrid classifier
    # decide which notices are actually security-related.
    ranked = match_company_to_tenders(company, tenders)
    opportunities = []
    counts = Counter()

    for tender in ranked:
        evidence, decision = assess_security(tender)
        counts[decision] += 1
        if decision != TARGET and decision not in REVIEW:
            continue

        # Eligibility is preliminary and must not override scope classification.
        assessment = evaluate_eligibility(company, build_eligibility_input(tender))
        assessment = as_dict(assessment)

        opportunities.append({
            "title": tender.get("title") or "Untitled notice",
            "ocid": tender.get("ocid") or "Unknown",
            "similarity": get_similarity(tender),
            "category": evidence.get("category") or "Not specified",
            "relevance_decision": decision,
            "guarding_matches": evidence.get("guarding_matches") or [],
            "related_matches": evidence.get("related_matches") or [],
            "service_groups": evidence.get("service_groups") or [],
            "value": tender.get("value"),
            "currency": tender.get("currency"),
            "locations": tender.get("locations") or [],
            "deadline": tender.get("deadline"),
            "assessment": assessment,
        })

    opportunities.sort(
        key=lambda item: (
            item["relevance_decision"] == TARGET,
            item["similarity"],
        ),
        reverse=True,
    )

    print("\nCLASSIFICATION SUMMARY")
    print("Target security contracts:", counts[TARGET])
    print("Security-related / manual review:", sum(counts[x] for x in REVIEW))
    print("Not relevant:", counts["NOT RELEVANT"])

    print("\nSECURITY OPPORTUNITIES FOR REVIEW")
    for item in opportunities[:20]:
        print("-" * 55)
        print("Title:", item["title"])
        print("Relevance:", item["relevance_decision"])
        print("AI similarity:", f'{item["similarity"]}%')
        print("Category:", item["category"])
        print("Value:", item["value"], item["currency"] or "")
        print("Deadline:", item["deadline"] or "Not published")
        print("Preliminary eligibility:", item["assessment"].get("decision", "Not assessed"))
        print("OCID:", item["ocid"])

    print("\nTotal shortlisted:", len(opportunities))
    print("Note: AI screening is not an approved Bid / No-Bid decision.")
    return opportunities


if __name__ == "__main__":
    discover_opportunities()
