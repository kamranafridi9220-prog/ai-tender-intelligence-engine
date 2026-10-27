
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

OCID = "ocds-h6vhtk-078ccd"

URL = (
    "https://www.find-tender.service.gov.uk"
    f"/api/1.0/ocdsRecordPackages/{OCID}"
)


def main():
    print("TENDER RECORD INSPECTOR")
    print("OCID:", OCID)

    request = Request(
        URL,
        headers={"Accept": "application/json"}
    )

    try:
        with urlopen(request, timeout=60) as response:
            data = json.load(response)

    except (HTTPError, URLError, TimeoutError) as error:
        print("API request failed:", error)
        return

    records = data.get("records") or []

    print("Records found:", len(records))

    for record in records:
        compiled = record.get("compiledRelease") or {}
        tender = compiled.get("tender") or {}

        print("\nTITLE:", tender.get("title"))
        print("VALUE:", tender.get("value"))
        print("TENDER PERIOD:", tender.get("tenderPeriod"))

        print("\nITEMS:")
        print(json.dumps(
            tender.get("items", []),
            indent=2
        )[:8000])

        print("\nLOTS:")
        print(json.dumps(
            tender.get("lots", []),
            indent=2
        )[:4000])

        print("\nBUYER:")
        print(json.dumps(
            compiled.get("buyer", {}),
            indent=2
        ))

        print("\nSOURCE RELEASES:")
        for release in record.get("releases") or []:
            print(
                release.get("id"),
                release.get("date"),
                (release.get("tender") or {}).get("title")
            )


if __name__ == "__main__":
    main()
