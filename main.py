
# AI Tender Intelligence Engine
# Lesson 4: Working with tender data

def main():

    tenders = [
        {
            "title": "Security Services Contract",
            "buyer": "London City Council",
            "value": 500000,
            "location": "London"
        },
        {
            "title": "Office Cleaning Contract",
            "buyer": "UK Facilities Group",
            "value": 250000,
            "location": "Manchester"
        },
        {
            "title": "Warehouse Security Contract",
            "buyer": "National Logistics Ltd",
            "value": 750000,
            "location": "Birmingham"
        }
    ]

    print("AI Tender Intelligence Engine")
    print("-----------------------------")

    for tender in tenders:
        print("Tender:", tender["title"])
        print("Buyer:", tender["buyer"])
        print("Value: £", tender["value"])
        print("Location:", tender["location"])
        print("-----------------------------")


if __name__ == "__main__":
    main()
