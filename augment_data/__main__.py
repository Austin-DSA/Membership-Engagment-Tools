from dataclasses import asdict
import logging
import os
import time
from typing import List
from . import geocodio_api, austin_city_api, datasource
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
    parser = argparse.ArgumentParser(
        description="""                                     
This script goes through the input CSV file which should be formatted as an Action Network membership list and adds 
some useful information to it.

*WARNING* This script uses the Austin City website as a web API. This may be unreliable and could be viewed as a misuse of their 
webserver. Make sure you do not run this script on larger data sets without good reason and without checking your arguments and inputs.
"""
    )
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
    parser.add_argument(
        "--geocodio",
        action="store_true",
        help="Use Geocodio to get state and federal districts.",
    )
    parser.add_argument(
        "--city",
        action="store_true",
        help="Use the Austin City website to get city council districts",
    )
    parser.add_argument(
        "--geocodio-key",
        type=str,
        default=os.environ.get("GEOCODIO_KEY"),
        help="A Geocodio API key. You can also put the key in the environment variable GEOCODIO_KEY.",
    )
    parser.add_argument("--min-proportion", type=float, default=0.5)

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    logger.info(f"Data loaded from {args.input}")
    data = read_csv(args.input)

    sources: List[datasource.AddressAugmentationDatasource] = []
    if args.city:
        sources.append(austin_city_api.AustinCityDatasource())
    if args.geocodio:
        sources.append(geocodio_api.GeocodioDatasource(key=args.geocodio_key, min_proportion=args.min_proportion))
    
    for row in data:
        address = assemble_address(row)
        logger.info(
            f"Processing row: name: {row.get('first_name')} {row.get('last_name')} address: {address}"
        )
        for source in sources:
            res = source.query(address)
            logger.info(f"{type(source).__name__}: {res}")
            row.update(asdict(res))
        time.sleep(args.interval)

    with open(args.output, "w", newline="", encoding="utf8") as file:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"Augmented data written to {args.output}")



if __name__ == "__main__":
    main()
