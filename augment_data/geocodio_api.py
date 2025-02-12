from abc import abstractmethod
from dataclasses import asdict, dataclass, field
import logging
import sys
import os
from typing import Any, List, Optional
import geocodio
import pprint

from augment_data.datasource import AddressAugmentationDatasource


@dataclass(repr=True)
class GeocodioResult:
    cleaned_address: str
    federal_representative_district: Optional[int] = None
    state_representative_district: Optional[int] = None
    state_senate_district: Optional[int] = None
    school_districts: Optional[str] = None


class GeocodioDatasource(AddressAugmentationDatasource):
    def __init__(self, *, key: Optional[str] = os.environ.get('GEOCODIO_KEY'), min_proportion: float = 0.5):
        self._client = geocodio.GeocodioClient(key)
        self._min_proportion = min_proportion

    # rooftop 	The exact point was found with rooftop level accuracy
    # point 	The exact point was found from address range interpolation where the range contained a single point
    # range_interpolation 	The point was found by performing address range interpolation
    # nearest_rooftop_match 	The exact house number was not found, so a close, neighboring house number was used instead
    # intersection 	The result is an intersection between two streets
    # street_center 	The result is a geocoded street centroid
    # place 	The point is a city/town/place zip code centroid
    # county 	The point is a county centroid
    # state 	The point is a state centroid
    acceptable_accuracy_types = ['rooftop', 'point', 'nearest_rooftop_match', 'range_interpolation']

    def query(self, address: str) -> Optional[GeocodioResult]:
        info = self._client.geocode_address(address, fields=["stateleg", "school", "cd"])
        res = None
        for result in info.get('results', []):
            accuracy_type=result.get('accuracy_type', '')

            if accuracy_type not in GeocodioDatasource.acceptable_accuracy_types:
                continue

            res = GeocodioResult(cleaned_address=address)

            try:
                res.cleaned_address = result['formatted_address']
            except LookupError:
                pass

            fields = result.get('fields', {})

            congressional_districts = fields.get('congressional_districts', [])
            if congressional_districts:
                district = max(congressional_districts, key=lambda x: x.get('proportion', 0))
                if district["proportion"] >= self._min_proportion:
                    legislators = district.get('current_legislators', [])
                    for legislator in legislators:
                        if legislator.get('type') == 'representative':
                            res.federal_representative_district = int(district.get('district_number'))

            state_districts = fields.get('state_legislative_districts', {})
            
            state_house = state_districts.get('house', [])
            if state_house:
                district = max(state_house, key=lambda x: x.get('proportion', 0))
                if district["proportion"] >= self._min_proportion:
                    res.state_representative_district = int(district.get('district_number'))
            
            state_senate = state_districts.get('senate', [])
            if state_senate:
                district = max(state_senate, key=lambda x: x.get('proportion', 0))
                if district["proportion"] >= self._min_proportion:
                    res.state_senate_district = int(district.get('district_number'))
            
            # Extract school district information
            school_districts = fields.get('school_districts', {})
            if school_districts:
                school_district_names = []
                for district in school_districts.values():
                    if 'name' in district:
                        school_district_names.append(district['name'])
                res.school_districts = ", ".join(school_district_names)
                
        return res
