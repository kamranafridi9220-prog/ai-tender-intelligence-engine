
# AI Tender Intelligence Engine
# Lesson 5: Connecting to a real government API

import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def main():
    print("AI Tender Intelligence Engine")
    print("Connecting to UK Find a Tender...")

    url = (
        "https://www.find-tender.service.gov.uk"
        "/api/1.0/ocdsReleasePackages"
        "?stages=tender&limit=5"
    )

    request = Request(
        url,
        headers={"Accept": "application/json"}
    )

    try:
        with urlopen(request, timeout=30) as response:
            data = json.load(response)

        releases = data.get("releases", [])

        print("Connection successful!")
        print("Tender releases received:", len(releases))

        for release in releases:
            tender = release.get("tender", {})

            print("-------------------------")
            print("Title:", tender.get("title", "Unknown"))
            print("OCID:", release.get("ocid", "Unknown"))
            print("Status:", tender.get("status", "Unknown"))

    except (HTTPError, URLError, TimeoutError) as error:
        print("API connection failed:", error)
        raise


if __name__ == "__main__":
    main()
