import requests
import typing
import dataclasses
import time
import datetime
import logging
import base64
import pytz

# MARK: Constants

class Constants:
    NEXT_PAGE_TOKEN_KEY = "next_page_token"
    AUTH_HEADER_KEY = "Authorization"

    class AccessToken:
        OAUTH_ENDPOINT = "https://zoom.us/oauth/token"
        OAUTH_CONTENT_TYPE = "application/x-www-form-urlencoded"

        GRANT_TYPE_KEY = "grant_type"
        GRANT_TYPE = "account_credentials"
        
        ACCOUNT_ID_KEY = "account_id"

        RESPONSE_ACCESS_TOKEN = "access_token"
        RESPONSE_TOKEN_TYPE = "token_type"
        RESPONSE_EXPIRES_IN = "expires_in"
        RESPONSE_SCOPE = "scope"
        RESPONSE_API_URL = "api_url"
    
    class Users:
        LIST_USERS_ENDPOINT = "https://api.zoom.us/v2/users"

        RESPONSE_ID_KEY = "id"
        RESPONSE_EMAIL_KEY = "email"
        RESPONSE_USERS_KEY = "users"
        RESPONSE_USERS_STATUS_KEY = "status"

        RESPONSE_USER_STATUS_ACTIVE = "active"

        class Features:
            def SETTINGS_ENDPOINT(userId: str) -> str:
                return f"https://api.zoom.us/v2/users/{userId}/settings"
            
            RESPONSE_FEATURE_KEY = "feature"
            RESPONSE_MEETING_CAPACITY = "meeting_capacity"
    
    class Meetings:
        def LIST_MEETING_ENDPOINT(userId: str) -> str:
            return f"https://api.zoom.us/v2/users/{userId}/meetings"
        
        QUERY_PARAM_FROM_DATE = "from"
        QUERY_PARAM_TO_DATE = "to"
        QUERY_PARAM_TIMEZONE = "timezone"
        QUERY_PARAM_TYPE = "type"
        QUERY_PARAM_TYPE_UPCOMING = "upcoming"

        RESPONSE_MEETING_LIST_KEY = "meetings"

        RESPONSE_TOPIC_KEY = "topic"
        RESPONSE_DURATION_KEY = "duration"
        RESPONSE_JOIN_URL_KEY = "join_url"
        RESPONSE_ID_KEY = "id"
        RESPONSE_START_TIME_KEY = "start_time"
        RESPONSE_TIMEZONE_KEY = "timezone"

        

# Mark: Data Classes

@dataclasses.dataclass(init=False)
class AccessToken:
    token : str
    tokenType : str
    expireTime : datetime.datetime
    scope : str
    apiUrl : str

    def __init__(self, token: str, tokenType: str, expiresInSec: int, scope: str, apiUrl: str) -> None:
        self.token = token
        self.tokenType = tokenType
        self.scope = scope
        self.apiUrl = apiUrl
        self.expireTime = datetime.datetime.now()+ datetime.timedelta(seconds=expiresInSec)

@dataclasses.dataclass
class ZoomUser:
    @dataclasses.dataclass
    class Features:
        meetingCapacity: int

    email: str
    id: str
    status: str
    features: Features = None

#TODO: Test to see if we need to include type
@dataclasses.dataclass
class ZoomMeeting:
    id : str
    startTime: datetime.datetime # Timezone aware
    duration: datetime.timedelta
    joinUrl: str
    ownerUserId: str
    topic: str

#TODO:Accounts - Handle Bad Responses gracefully

class ZoomAPI:

    def __init__(self, accountId: str, clientId: str, clientSecret: str) -> None:
        self._accountId = accountId
        self._clientId = clientId
        self._clientSecret = clientSecret
        # Set token expire to the past, API calls will will check if we have a valid token and then refresh
        self._tokenExpireTime = datetime.datetime.now()
        self._accessToken = None

# MARK: Utilities

    def _headersForRequest(self) -> dict:
        return {Constants.AUTH_HEADER_KEY : f"Bearer {self._accessToken.token}"}

# MARK: Access Token 

    # Shouldn't call on these directly instead use _accessTokenRequired as a decorator
    def _refreshAccessToken(self) -> None:
        logging.info("ZoomAPI: Refreshing Access Token")
        authSecretsBase64 = base64.standard_b64encode(f"{self._clientId}:{self._clientSecret}")
        headers = {Constants.AUTH_HEADER_KEY : f"Basic {authSecretsBase64}"}
        body = {
            Constants.AccessToken.GRANT_TYPE_KEY : Constants.AccessToken.GRANT_TYPE,
            Constants.AccessToken.ACCOUNT_ID_KEY : self._accountId
            }
        req = requests.post(url=Constants.AccessToken.OAUTH_ENDPOINT, headers=headers, data=body)
        req.raise_for_status()
        responseDict = req.json()
        self._accessToken = AccessToken(
            token=responseDict[Constants.AccessToken.RESPONSE_ACCESS_TOKEN],
            tokenType=responseDict[Constants.AccessToken.RESPONSE_TOKEN_TYPE],
            expiresInSec=int(responseDict[Constants.AccessToken.RESPONSE_EXPIRES_IN]), # This should be an int, but in case it is a string convert, should be cheap if already an int
            scope=responseDict[Constants.AccessToken.RESPONSE_SCOPE],
            apiUrl=responseDict[Constants.AccessToken.RESPONSE_API_URL]
            )
        logging.info("ZoomAPI: Refreshed Access Token. Will expire at %s", str(self._accessToken.expireTime))


    # If the token exists and is within its lifetime it is valid
    # Count being close to the access time as invalid to reduce chance of expiring happening during a critical section
    def _isAccessTokenValid(self) -> None:
        return self._accessToken is not None and datetime.datetime.now() < (self._tokenExpireTime - datetime.timedelta(minutes=2))

    @staticmethod
    def _accessTokenRequired(func):
        def inner(self: ZoomAPI, *args, **kwargs):
            if not self._isAccessTokenValid():
                logging.info("ZoomAPI: Access token invalid")
                self._refreshAccessToken()
            return func(self,*args, **kwargs)
        return inner

# MARK: Accounts

    @_accessTokenRequired
    def _fetchAccounts(self) -> list[ZoomUser]:
        def processJsonResponseIntoUsers(responseDict: dict) -> list[ZoomUser]:
            if Constants.Users.RESPONSE_USERS_KEY not in responseDict:
                logging.error("ZoomAPI: No users list in response, returning empty account list")
                return []
            users = []
            for user in responseDict[Constants.Users.RESPONSE_USERS_KEY]:
                newUser = ZoomUser(email=user[Constants.Users.RESPONSE_EMAIL_KEY], 
                                   id=user[Constants.Users.RESPONSE_ID_KEY],
                                   status=user[Constants.Users.RESPONSE_USERS_STATUS_KEY])

                if newUser.status != Constants.Users.RESPONSE_USER_STATUS_ACTIVE:
                    logging.info("ZoomAPI: User %s is not active, instead %s. Skipping.", newUser.email, newUser.status)
                    continue
                
                logging.info("ZoomAPI: Found user %s, getting features", newUser.email)
                req = requests.get(Constants.Users.Features.SETTINGS_ENDPOINT(newUser.id), headers=self._headersForRequest())
                req.raise_for_status()
                responseDict = req.json()
                newUser.features = ZoomUser.Features(meetingCapacity=responseDict[Constants.Users.Features.RESPONSE_FEATURE_KEY][Constants.Users.Features.RESPONSE_MEETING_CAPACITY])

                users.append(newUser)
            return users

        logging.info("ZoomAPI: Fetching accounts")
        accounts = []
        req = requests.get(Constants.Users.LIST_USERS_ENDPOINT, headers=self._headersForRequest())
        req.raise_for_status()
        responseDict = req.json()
        accounts.extend(processJsonResponseIntoUsers(responseDict=responseDict))
        
        while Constants.NEXT_PAGE_TOKEN_KEY in responseDict and responseDict[Constants.NEXT_PAGE_TOKEN_KEY] != "":
            logging.info("ZoomAPI: Moving onto next page of account list")
            params = {Constants.NEXT_PAGE_TOKEN_KEY : responseDict[Constants.NEXT_PAGE_TOKEN_KEY]}
            req = requests.get(Constants.Users.LIST_USERS_ENDPOINT, headers=self._headersForRequest(), params=params)
            req.raise_for_status()
            responseDict = req.json()
            accounts.extend(processJsonResponseIntoUsers(responseDict=responseDict))
        
        logging.info("ZoomAPI: No next page, finishing fetching accounts")
        return accounts

    def _accounts(self) -> list[ZoomUser]:
        if self._cachedAccounts is None:
            logging.info("ZoomAPI: No accounts in cache")
            self._cachedAccounts = self._fetchAccounts()
        else:
            logging.info("ZoomAPI: Returning Cached ids")
        return self._cachedAccounts

# MARK: Meetings
    @_accessTokenRequired
    def _fetchMeetingsForAccountAndTime(self, account: ZoomUser, fromDate: datetime.datetime, toDate: datetime.datetime) -> list[ZoomMeeting]:
        def processJsonResponIntoMeetings(responseDict: dict) -> list[ZoomMeeting]:
            if Constants.Meetings.RESPONSE_MEETING_LIST_KEY not in responseDict:
                logging.error("ZoomAPI: No meeting list in response, returning empty meeting list")
                return []
            meetings = []
            for meeting in responseDict[Constants.Meetings.RESPONSE_MEETING_LIST_KEY]:
                startTime = datetime.datetime.fromisoformat(meeting[Constants.Meetings.RESPONSE_START_TIME_KEY])
                startTime.replace(tzinfo=pytz.timezone(meeting[Constants.Meetings.RESPONSE_TIMEZONE_KEY]))

                newMeeting = ZoomMeeting(id=meeting[Constants.Meetings.RESPONSE_ID_KEY],
                                         startTime=startTime,
                                         duration=datetime.timedelta(minutes=meeting[Constants.Meetings.RESPONSE_DURATION_KEY]),
                                         joinUrl=Constants.Meetings.RESPONSE_JOIN_URL_KEY,
                                         ownerUserId=account.id,
                                         topic=meeting[Constants.Meetings.RESPONSE_TOPIC_KEY])
                
                logging.info("ZoomAPI: Found meeting %s at %s, getting features", newMeeting.topic, startTime)
                meetings.append(newMeeting)
            return meetings
        
        logging.info("ZoomAPI: Fetching meetings for %s from %s to %s", account.email, fromDate, toDate)
        meetings = []
        params = { Constants.Meetings.QUERY_PARAM_FROM_DATE : fromDate.isoformat(),
                   Constants.Meetings.QUERY_PARAM_TO_DATE : toDate.isoformat(),
                   Constants.Meetings.QUERY_PARAM_TIMEZONE : fromDate.tzinfo.tzname(),
                   Constants.Meetings.QUERY_PARAM_TYPE : Constants.Meetings.QUERY_PARAM_TYPE_UPCOMING}
        req = requests.get(Constants.Meetings.LIST_MEETING_ENDPOINT(account.id), headers=self._headersForRequest(), params=params)
        req.raise_for_status()
        responseDict = req.json()
        meetings.extend(processJsonResponIntoMeetings(responseDict=responseDict))
        
        while Constants.NEXT_PAGE_TOKEN_KEY in responseDict and responseDict[Constants.NEXT_PAGE_TOKEN_KEY] != "":
            logging.info("ZoomAPI: Moving onto next page of meeting list")
            params[Constants.NEXT_PAGE_TOKEN_KEY] = responseDict[Constants.NEXT_PAGE_TOKEN_KEY]
            req = requests.get(Constants.Meetings.LIST_MEETING_ENDPOINT(account.id), headers=self._headersForRequest(), params=params)
            req.raise_for_status()
            responseDict = req.json()
            meetings.extend(processJsonResponIntoMeetings(responseDict=responseDict))
        
        logging.info("ZoomAPI: No next page, finishing fetching meetings")
        return meetings


# MARK: Public APIs

    # Returns the list of tuples
    # 0 - The account this record is for
    # 1 - List of conflicting meetings, if empty then account is available
    def getAccountsAndAvailablilityForTime(self, time: datetime.datetime, duration: datetime.timedelta) -> list[tuple[ZoomUser,list[ZoomMeeting]]]:
        # Can't check for conflicts in the past nor schedule meetings
        # Return false as if there is a conflict
        if time < datetime.datetime.now():
            logging.error("ZoomAPI: Passed in time %s that is in the past", str(time))
            raise Exception(f"ZoomAPI: Passed in time {time} that is in the past") # ??
        # Require timezone specific 
        if time.tzinfo is None or time.tzinfo.utcoffset() is None:
            logging.error("ZoomAPI: The argument for the start time must be timezone aware. Passed in unaware object.")
            raise Exception("ZoomAPI: The argument for the start time must be timezone aware. Passed in unaware object.")
        
        # Look for potential conflicts within 3 hours on each side
        logging.info("ZoomAPI: Check availability for meeting starting at %s for duration %s", time, duration)
        fromDate = time - datetime.timedelta(hours=3)
        toDate = time + datetime.timedelta(hours=3)+duration
        results = []
        for account in self._accounts():
            # Get potential conflicts
            potentialConflicts = self._fetchMeetingsForAccountAndTime(account=account, fromDate=fromDate, toDate=toDate)
            confirmedConflicts = []
            # Check for conflicts
            logging.info("ZoomAPI: Checking conflicts for account %s", account.email)
            for potentialConflict in potentialConflicts:
                # If the potential conflict ends before the meeting starts then there is no conflict
                if potentialConflict.startTime+potentialConflict.duration < time:
                    continue
                # If the potential conflict starts after the meeting ends then there is no conflict
                if time+duration < potentialConflict.startTime:
                    continue
                # Otherwise there must be overlap and so we have a conflict
                logging.info("ZoomAPI: Found conflict by meeting %s at %s for %s duration", potentialConflict.topic, potentialConflict.startTime, potentialConflict.duration)
                confirmedConflicts.append(potentialConflict)
            results.append((account,confirmedConflicts))
        logging.info("ZoomAPI: Done checking availability")
        return results



        

    

