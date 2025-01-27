
import datetime
import google.auth
import google.auth.transport
import google.auth.transport.requests
import google.oauth2.service_account
import googleapiclient.discovery
import logging
import dataclasses
import typing
import pytz
import os

class Constants:
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    CALENDAR_SEVRVICE = "calendar"
    CALENDAR_SERVICE_VERSION = "v3"

    class EventKeys:
        DESCRIPTION = "description"
        TITLE = "summary"
        LOCATION = "location"
        START = "start"
        END = "end"
        LINK = "htmlLink"

        class Date:
            TIME  = "dateTime"
            TIMEZONE = "timeZone"



@dataclasses.dataclass
class Event:
    title: str
    start: datetime.datetime
    end: datetime.datetime # Technically end is optional but we will require all events have a specific end
    description: str
    location: typing.Optional[str]
    link: typing.Optional[str] = None # Not writeable so we don't need to serialize to the API just from

    @staticmethod 
    def convertDatetimeToDict(date: datetime.datetime) -> dict:
        # Require timezone aware objects 
        if date.tzinfo is None or date.tzinfo.utcoffset(date) is None:
            logging.error("GoogleCalendarAPI: The argument for the start time must be timezone aware. Passed in unaware object.")
            raise Exception("GoogleCalendarAPI: The argument for the start time must be timezone aware. Passed in unaware object.")
        return {
            Constants.EventKeys.Date.TIME : date.isoformat(),
            Constants.EventKeys.Date.TIMEZONE : date.tzinfo.zone
        }
    
    @staticmethod
    def convertDictToDatetime(d: dict) -> datetime.datetime:
        time = datetime.datetime.fromisoformat(d[Constants.EventKeys.Date.TIME])
        if Constants.EventKeys.Date.TIMEZONE in d:
            timezone = d[Constants.EventKeys.Date.TIMEZONE]
            timezone = pytz.timezone(timezone)
            time.replace(tzinfo=timezone)
        return time

    @staticmethod
    def fromApiDict(d: str):
        title = d[Constants.EventKeys.TITLE]
        description = d[Constants.EventKeys.DESCRIPTION]
        start = Event.convertDictToDatetime(d[Constants.EventKeys.START])
        end = Event.convertDictToDatetime(d[Constants.EventKeys.END])
        location = None
        if Constants.EventKeys.LOCATION  in d:
            location = d[Constants.EventKeys.LOCATION]
        link = None
        if Constants.EventKeys.LINK in d:
            link = d[Constants.EventKeys.LINK]
        return Event(title, start, end, description, location, link)

    def toApiDict(self)->dict:
        d = {
            Constants.EventKeys.DESCRIPTION : self.description,
            Constants.EventKeys.TITLE : self.title,
            Constants.EventKeys.START : Event.convertDatetimeToDict(self.start),
            Constants.EventKeys.END : Event.convertDatetimeToDict(self.end)
        }
        if self.location is not None:
            d[Constants.EventKeys.LOCATION] = self.location
        return d

@dataclasses.dataclass
class GoogleCalendarConfig:
    serviceKeyPath: str
    calendarId: str
    delegateAccount: str

#https://github.com/googleapis/google-api-python-client/blob/main/docs/start.md
# https://googleapis.github.io/google-api-python-client/docs/dyn/calendar_v3.html
# Delegation Auth- https://developers.google.com/identity/protocols/oauth2/service-account#delegatingauthority
# For auth:
# 1. Create Project Here: https://console.cloud.google.com/apis/
# 2. Enable calendar API
# 3. Create Service Account
# 4. Enable Delegation Wide Authority to Service Account in Admin Console
# 5. Choose an account it can delegate that has access to calendar
class GoogleCalendarAPI:
    def __init__(self, config: GoogleCalendarConfig):
        logging.info("GoogleCalendarAPI: Logging in with provided credential file")
        if not os.path.exists(config.serviceKeyPath):
            logging.error("GoogleCalendarAPI: Service Key path does not exist %s", config.serviceKeyPath)
            raise Exception(f"GoogleCalendarAPI: Service Key path does not exist {config.serviceKeyPath}")
        self.config = config
        self.serviceAccountCreds = google.oauth2.service_account.Credentials.from_service_account_file(self.config.serviceKeyPath, scopes=Constants.SCOPES)
        self.delegatedCreds = self.serviceAccountCreds.with_subject(self.config.delegateAccount)
        self.delegatedCreds.refresh(google.auth.transport.requests.Request())
        # Unclear from docs if we need to refresh these
        # if not self.delegatedCreds or not self.delegatedCreds.valid:
        #     logging.error("GoogleCalendarAPI: Could not create credentials")
        #     raise Exception("GoogleCalendarAPI: Could not create credentials")

    # https://googleapis.github.io/google-api-python-client/docs/dyn/calendar_v3.events.html#list
    def findConflicts(self, start: datetime.datetime, duration: datetime.timedelta) -> list[Event]:
        # Require timezone aware objects 
        if start.tzinfo is None or start.tzinfo.utcoffset(start) is None:
            logging.error("GoogleCalendarAPI: The argument for the start time must be timezone aware. Passed in unaware object.")
            raise Exception("GoogleCalendarAPI: The argument for the start time must be timezone aware. Passed in unaware object.")
        
        end = start+duration+datetime.timedelta(minutes=15) # Give 15 min runway between events
        start = start-datetime.timedelta(minutes=15)
        logging.info("GoogleCalendarAPI: Looking for conflicts from %s to %s", str(start), str(end))
        with googleapiclient.discovery.build(Constants.CALENDAR_SEVRVICE, Constants.CALENDAR_SERVICE_VERSION, credentials=self.delegatedCreds) as service:
            result = []
            pageToken = None
            while True:
                response = service.events().list(calendarId=self.config.calendarId, timeMin=start.isoformat(), timeMax=end.isoformat(), pageToken=pageToken).execute()
                for event in response['items']:
                    result.append(Event.fromApiDict(event))
                pageToken = response.get('nextPageToken')
                if not pageToken:
                    break
            return result
    
    # https://googleapis.github.io/google-api-python-client/docs/dyn/calendar_v3.events.html#insert
    def createEvent(self, event: Event) -> str:
        logging.info("GoogleCalendarAPI: Adding Event %s starting at %s", event.title, str(event.start))
        with googleapiclient.discovery.build(Constants.CALENDAR_SEVRVICE, Constants.CALENDAR_SERVICE_VERSION, credentials=self.delegatedCreds) as service:
            body = event.toApiDict()
            response = service.events().insert(calendarId = self.config.calendarId, body = body).execute()
            return Event.fromApiDict(response).link
    
    # def getCalendars(self):
    #     with googleapiclient.discovery.build(Constants.CALENDAR_SEVRVICE, Constants.CALENDAR_SERVICE_VERSION, credentials=self.delegatedCreds) as service:
    #         result = []
    #         page_token = None
    #         while True:
    #             calendar_list = service.calendarList().list(pageToken=page_token).execute()
    #             for calendar_list_entry in calendar_list['items']:
    #                 result.append(calendar_list_entry)
    #             page_token = calendar_list.get('nextPageToken')
    #             if not page_token:
    #                 break
    #         return result

