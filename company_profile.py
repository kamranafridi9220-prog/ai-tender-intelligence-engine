
# AI Tender Intelligence Engine
# Lesson 13: Company Profile Engine

from dataclasses import dataclass, field


@dataclass
class CompanyProfile:
    name: str
    industry: str
    services: list[str]
    locations: list[str]
    minimum_contract_value: int
    maximum_contract_value: int
    certifications: list[str] = field(default_factory=list)

    def validate(self):
        if not self.name.strip():
            raise ValueError("Company name is required")

        if not self.services:
            raise ValueError("At least one service is required")

        if self.minimum_contract_value < 0:
            raise ValueError("Minimum value cannot be negative")

        if self.maximum_contract_value < self.minimum_contract_value:
            raise ValueError("Maximum value must be >= minimum value")

    def service_description(self):
        return (
            f"{self.name} operates in {self.industry}. "
            f"Services: {', '.join(self.services)}. "
            f"Operating locations: {', '.join(self.locations)}."
        )


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
        locations=[
            "London",
            "Greater London"
        ],
        minimum_contract_value=100000,
        maximum_contract_value=2000000,
        certifications=[]
    )

    company.validate()

    print("COMPANY PROFILE")
    print("-------------------------")
    print("Company:", company.name)
    print("Industry:", company.industry)
    print("Services:", ", ".join(company.services))
    print("Locations:", ", ".join(company.locations))
    print(
        "Contract value range:",
        f"£{company.minimum_contract_value:,}",
        "to",
        f"£{company.maximum_contract_value:,}"
    )
    print("Certifications:", company.certifications)
    print("-------------------------")
    print("AI matching description:")
    print(company.service_description())


if __name__ == "__main__":
    main()
