import requests
import typing
import dataclasses
import time
import datetime
import logging


class Constants:
    # URLS
    API_ENTRY = "https://actionnetwork.org/api/v2/"
    BACKGROUN_PROCESSING_QUERY_PARAM = "background_request"

    # Person Keys
    EMAIL = "address"
    EMAIL_ADDRESSES = "email_addresses"
    PHONE_NUMBERS = "phone_numbers"
    POSTAL_ADDRESSES = "postal_addresses"
    LAST_NAME = "family_name"
    FIRST_NAME = "given_name"
    CUSTOM_FIELDS = "custom_fields"

    # Phone Number Keys
    PHONE = "number"

    # Person Address Keys
    ADDRESS_LINES = "address_lines"
    REGION = "region"
    ZIP_CODE = "postal_code"
    COUNTRY = "country"
    CITY = "locality"

    # POST headers
    HEADER_CONTENT_TYPE = "Content-Type"
    HEADER_CONTENT_JSON = "application/json"
    HEADER_API_KEY = "OSDI-API-Token"

    # API Endpoint Keys
    API_PERSON_SIGNUP_HELPER_KEY = "osdi:person_signup_helper"
    API_ENDPOINT = "href"
    API_ENDPOINTS_LIST = "_links"

    # Signup helper keys
    SIGNUP_HELPER_PERSON = "person"
    SIGNUP_HELPER_ADD_TAGS = "add_tags"
    SIGNUP_HELPER_REMOVE_TAGS = "remove_tags"


@dataclasses.dataclass
class PersonAddress:
    # Assuming TX becuase chapter is in Austin,TX
    zip_code: str
    address_lines: typing.List[str]
    country: str = "US"
    region: str = "TX"
    city: str = "Austin"

    def toDict(self) -> dict:
        return {
            Constants.ADDRESS_LINES: self.address_lines,
            Constants.REGION: self.region,
            Constants.ZIP_CODE: self.zip_code,
            Constants.COUNTRY: self.country,
            Constants.CITY: self.city,
        }


# Forces customFields to lower case
@dataclasses.dataclass
class Person:
    firstName: str
    lastName: str
    email: str
    phone: str
    address: type[PersonAddress]
    customFields: dict[str, str]

    # The structre here is different from the full spec, in the sign up helper it is flattened
    # https://actionnetwork.org/docs/v2/person_signup_helper
    def toSignupHelperDict(self):
        personDict = {
            Constants.FIRST_NAME: self.firstName,
            Constants.LAST_NAME: self.lastName,
            Constants.EMAIL_ADDRESSES: [{Constants.EMAIL: self.email}],
            Constants.PHONE_NUMBERS: [{Constants.PHONE: self.phone}],
            Constants.POSTAL_ADDRESSES: [self.address.toDict()],
            Constants.CUSTOM_FIELDS: {},
        }
        restrictedCols = set(
            [
                Constants.FIRST_NAME,
                Constants.LAST_NAME,
                Constants.EMAIL_ADDRESSES,
                Constants.PHONE_NUMBERS,
                Constants.POSTAL_ADDRESSES,
            ]
        )
        for k, v in self.customFields.items():
            outKey = k.lower()
            if outKey in restrictedCols:
                raise InvalidPerson(
                    "Custom field " + k + " conflicts with restricted API keys"
                )
            if type(v) != str:
                raise InvalidPerson(
                    "Custom field " + k + " of value " + str(v) + " is not of string"
                )
            personDict[Constants.CUSTOM_FIELDS][k] = v
        return personDict


class InvalidPerson(Exception):
    pass


class InvalidAPIResponse(Exception):
    pass


class ActionNetworkAPI:
    def __init__(self, apiKey) -> None:
        self.apiKey = apiKey
        self._initializeEndpoints()

    @staticmethod
    def _extractEndpoint(endpointDict: dict, api: str) -> str:
        if api not in endpointDict:
            raise InvalidAPIResponse(
                "Api ("
                + api
                + ") was not in endpoint list which is "
                + str(endpointDict)
            )
        endpointObj = endpointDict[api]
        if Constants.API_ENDPOINT not in endpointObj:
            raise InvalidAPIResponse(
                "Endpoint("
                + Constants.API_ENDPOINT
                + ") not found for API("
                + api
                + ") in endpoint object "
                + str(endpointObj)
            )
        return endpointObj[Constants.API_ENDPOINT]

    def _initializeEndpoints(self) -> None:
        # Get available APIs
        response = requests.get(Constants.API_ENTRY, headers=self._headersForRequest())
        response.raise_for_status()
        # Action Network API shoul return a JSON response for endpoints
        # https://actionnetwork.org/docs/v2/post-people/
        responseDict = response.json()
        endpoints = responseDict[Constants.API_ENDPOINTS_LIST]
        if type(endpoints) != dict:
            raise InvalidAPIResponse(
                "Endpoints list in response ("
                + Constants.API_ENDPOINTS_LIST
                + ") was not a dictionary. Instead it was "
                + str(endpoints)
            )

        # Extract APIs we want
        self.personSignupHelper = ActionNetworkAPI._extractEndpoint(
            endpoints, Constants.API_PERSON_SIGNUP_HELPER_KEY
        )

    def _headersForRequest(self) -> dict:
        # Requests should add in json content header https://requests.readthedocs.io/en/latest/user/quickstart/?highlight=raise_for_status#more-complicated-post-requests
        return {Constants.HEADER_API_KEY: self.apiKey}

    # Send a list of people to Action Network synchronously and sequentially
    # If any of the post request fails no later request will be attempted and an exception will be raised
    # CURRENTLY DO NOT RETRY PROGRAMATICALLY UPON EXCEPTION
    # Action Network asks for exopential backoff on failures and this function does not account for that
    # Returns a list of people that failed
    def postPeople(
        self, people: list[type[Person]], useBackgroundProcessing: bool = True
    ) -> list[tuple[str, str]]:
        # Currently (2023-04-15) Action Network rate limits at 4 per second https://actionnetwork.org/docs/#considerations
        # To avoid any possible conflicts we will wait 0.35 seconds per request
        # Upon failure a exception will be raised and assumed to kill the program
        failedUploads = []
        numPeople = len(people)
        currentPerson = 0
        for person in people:
            logging.info(
                "Uploading "
                + person.firstName
                + " "
                + person.lastName
                + " "
                + str(currentPerson)
                + "/"
                + str(numPeople)
            )
            startTime = datetime.datetime.now()
            try:
                self._postPerson(person, useBackgroundProcessing)
            except Exception as err:
                personText = f"({person.firstName}, {person.lastName}, {person.email})"
                errorText = f"{err}"
                logging.error(
                    "Failed to upload: %s because of %s", personText, errorText
                )
                failedUploads.append((personText, errorText))
                # Sleep an extra few seconds to back off of server
                time.sleep(2)

            # Sleep to avoid rate limit if we aren't background processing
            timeInRequest = datetime.datetime.now() - startTime
            if not useBackgroundProcessing and timeInRequest < datetime.timedelta(
                seconds=0.35
            ):
                timeToSleep = 0.5 - timeInRequest.seconds
                if timeToSleep > 0:
                    time.sleep(timeToSleep)
            currentPerson += 1
        return failedUploads

    # Do not use this directly
    # The API is rate limited so using this in a tight for loop could cause issues
    # To post a single person use postPeople() with a list of a single person
    def _postPerson(
        self, person: type[Person], useBackgroundProcessing: bool = True
    ) -> None:
        # Currently we do not support adding or removing tags
        params = {}
        if useBackgroundProcessing:
            params[Constants.BACKGROUN_PROCESSING_QUERY_PARAM] = True
        req = requests.post(
            self.personSignupHelper,
            json=person.toSignupHelperDict(),
            headers=self._headersForRequest(),
            params=params,
        )
        # We currently don't care about the response as long as it is not failure
        req.raise_for_status()

    # Assumes the API key is on the first line of the file
    @staticmethod
    def readAPIKeyFromFile(path: str) -> str:
        with open(path) as f:
            for line in f:
                return line.strip()
