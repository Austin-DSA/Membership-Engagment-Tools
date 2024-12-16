import logging
import time
from austin_city_api import AustinDataService
from pathlib import Path
import argparse
import csv

logger = logging.getLogger(__name__)


def read_csv(filename: Path):
    with open(filename, "r", newline="", encoding="utf8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def assemble_address(row: dict) -> str:
    """Take a row dict and assemble an address from the fields address1, address2, city, state, zip, country."""
    return (
        f"{row.get('address1', '')} {row.get('address2', '')}, {row.get('city', '')},"
        f" {row.get('state', '')}, {row.get('zip', '')}, {row.get('country', '')}"
    )


def main():
    parser = argparse.ArgumentParser(description="""
*WARNING* This script uses the Austin City website as a web API. This may be unreliable and could be viewed as a misuse of their 
webserver. Make sure you do not run this script on larger data sets without good reason and without checking your arguments and inputs.
                                     
This script goes through the input CSV file (which should be an Action Network membership list) and adds some useful information to it.
""")
    parser.add_argument("-v", "--verbose", action="store_true", help="Be more verbose.")
    parser.add_argument(
        "-i", "--input", required=True, type=Path, help="Input CSV file path"
    )
    parser.add_argument(
        "-o", "--output", required=True, type=Path, help="Output CSV file path"
    )
    parser.add_argument(
        "-n",
        "--interval",
        type=float,
        default=30,
        help="The interval in seconds between rows being processed. The default is very large to avoid triggering "
            "throttling by accident. You will want to decrease this probably. (default: 30 seconds)",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    logger.info(f"Data loaded from {args.input}")
    data = read_csv(args.input)

    austin_service = AustinDataService()

    for row in data:
        logger.info(
            f"Processing row: name: {row.get('first_name')} {row.get('last_name')} address: {assemble_address(row)}"
        )
        add_city_council_district(austin_service, row)
        time.sleep(args.interval)

    with open(args.output, "w", newline="", encoding="utf8") as file:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"Augmented data written to {args.output}")


def add_city_council_district(austin_service: AustinDataService, row: dict) -> None:
    """Augment the row with the city council district, if available."""
    if "city_council_district" in row:
        return
    
    address = assemble_address(row)
    geocoded_address = austin_service.geocode_address(address)
    if geocoded_address:
        row["geocoded_address"] = geocoded_address.address
        logger.info(f"Requesting council district for {geocoded_address.address}")
        district = austin_service.get_council_district(geocoded_address.location)
        row["city_council_district"] = district if district is not None else "Unknown"
    else:
        row["geocoded_address"] = ""
        row["city_council_district"] = ""
    logger.info(f"  City Council District: {row.get('city_council_district')}")


if __name__ == "__main__":
    main()
