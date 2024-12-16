"""
An interface to the Austin City Council website as an API to retrieve council district information.

*WARNING* This uses the Austin City website as a web API. This may be unreliable and could be viewed as a misuse of their 
webserver. Make sure you do not run this script on larger data sets without good reason and without checking your arguments and inputs.
"""

from dataclasses import dataclass
import json
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass(repr=True)
class Location:
    # The latitude north
    x: float
    # The longitude west
    y: float

@dataclass(repr=True)
class Extent:
    # The latitude north of the one corner of the extent
    xmin: float
    # The longitude west of the one corner of the extent
    ymin: float
    # The latitude north of the other corner of the extent
    xmax: float
    # The longitude west of the other corner of the extent
    ymax: float

@dataclass(repr=True)
class GeocodedAddress:
    # Address (generally as corrected by the geocoding service)
    address: str
    # Lat-long coordinates of the geocoded address
    location: Location
    # [not understood] An arbitrary score of the address' accuracy
    score: int
    # [not understood] The "error area" for the geocoded address
    extent: Extent

    # TODO: Combine score and extent into a combined "trust" score that gives us an idea of how much the address may overlap with others.


class AustinDataService:
    def __init__(self):
        self.session = requests.Session()
        self.session.get("https://www.austintexas.gov/government")

    def geocode_address(self, address: str) -> Optional[GeocodedAddress]:
        url = "https://maps.austintexas.gov/arcgis/rest/services/Geocode/COA_Locator/GeocodeServer/findAddressCandidates"
        params = {
            "outFields": "",
            "maxLocations": 1,
            "outSR": "",
            "searchExtent": "",
            "f": "pjson",
            "SingleLine": address,
            "callback": "callback",
            "js": 1,
        }
        response = self.session.get(url, params=params)

        # Check that the response uses the callback callback function
        if not response.text.startswith("callback("):
            logger.warning(f"Received JSONP response with callback name {response.text[:10]}.. which is not expected.")

        # Extract JSON from JSONP response
        json_str = response.text[response.text.index("(") + 1 : -2]
        data = json.loads(json_str)

        if data["candidates"]:
            candidate = data["candidates"][0]
            return GeocodedAddress(
                address=candidate["address"],
                location=Location(**candidate["location"]),
                score=candidate["score"],
                extent=Extent(**candidate["extent"])
            )
        else:
            logger.info(f"No geocoded address found for {address}")
        return None

    def get_council_district(self, location: Location) -> Optional[int]:
        url = "https://maps.austintexas.gov/gis/rest/Shared/CouncilDistrictsFill/MapServer/0/query"
        params = {
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "COUNCIL_DISTRICT",
            "returnGeometry": "false",
            "f": "pjson",
            "geometry": f"{location.x},{location.y}"
        }
        response = self.session.get(url, params=params)
        data = response.json()

        if data["features"]:
            district = data["features"][0]["attributes"]["COUNCIL_DISTRICT"]
            return int(district)
        return None



def test_api(address: str):
    logging.basicConfig(level=logging.INFO)
    service = AustinDataService()

    print(f"Testing with address: {address}")
    
    # Test geocode_address
    print("\nTesting geocode_address:")
    geocoded = service.geocode_address(address)
    if geocoded:
        print(geocoded)
    else:
        print("  No geocoded address found")

    # Test get_council_district
    if geocoded:
        print("\nTesting get_council_district:")
        district = service.get_council_district(geocoded.location)
        if district:
            print(f"  Council District: {district}")
        else:
            print("  No council district found")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test Austin City API")
    parser.add_argument("address", help="Address to test with")
    args = parser.parse_args()

    test_api(args.address)