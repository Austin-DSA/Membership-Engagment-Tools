from dataclasses import asdict
import logging
import os
import pprint

import austin_city_api, geocodio_api


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test Augmentation Data Sources on a single address")
    parser.add_argument("address", help="Address to test with")
    parser.add_argument("--geocodio", "-g", action="store_true")
    parser.add_argument("--city", "-c", action="store_true", help="Austin City Website")
    parser.add_argument("--geocodio-key", type=str, default=os.environ.get('GEOCODIO_KEY'))
    parser.add_argument("--min-proportion", type=float, default=0.5)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    sources = []
    if args.city:
        sources.append(austin_city_api.AustinCityDatasource())
    if args.geocodio:
        sources.append(geocodio_api.GeocodioDatasource(key=args.geocodio_key, min_proportion=args.min_proportion))

    address = args.address

    print(f"Testing with address: {address}")
    
    full_result = {"address": address}

    for source in sources:
        res = source.query(address)
        print(f"{type(source).__name__}: {res}")
        full_result.update(asdict(res))
    print("Full result:")
    pprint.pprint(full_result)
