
import datetime
import google.oauth2.service_account
import googleapiclient.discovery
import logging

class Constants:
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    CALENDAR_SEVRVICE = "calendar"
    CALENDAR_SERVICE_VERSION = "v3"


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
    def __init__(self, serviceKeyPath: str, calendarId: str, delegateAccount: str):
        logging.info("GoogleCalendarAPI: Logging in with provided credential file")
        self.serviceKeyPath = serviceKeyPath
        self.serviceAccountCreds = google.oauth2.service_account.Credentials.from_service_account_file(self.serviceKeyPath, scopes=Constants.SCOPES)
        self.delegateAccount = delegateAccount
        self.delegatedCreds = self.serviceAccountCreds.with_subject(self.delegateAccount)
        self.calendarId = calendarId
        # Unclear from docs if we need to refresh these
        if not self.delegatedCreds or not self.delegatedCreds.valid:
            logging.error("GoogleCalendarAPI: Could not create credentials")
            raise Exception("GoogleCalendarAPI: Could not create credentials")

    def listCalendarEventsForUTCDate(self, start: datetime.datetime, duration: datetime.timedelta):
        with googleapiclient.discovery.build(Constants.CALENDAR_SEVRVICE, Constants.CALENDAR_SERVICE_VERSION, credentials=self.delegatedCreds) as service:
            response = service.events().list(calendarId=self.calendarId).execute()
            return response
    
    def createEvent(self):
        with googleapiclient.discovery.build(Constants.CALENDAR_SEVRVICE, Constants.CALENDAR_SERVICE_VERSION, credentials=self.delegatedCreds) as service:
            response = service.events().insert(calendarId = self.calendarId, body = {
                "summary" : "Test Event From Script",
                'start': {
                            'dateTime': '2025-01-28T09:00:00-07:00',
                            'timeZone': 'America/Los_Angeles',
                         },
                'end': {
                            'dateTime': '2025-01-28T17:00:00-07:00',
                            'timeZone': 'America/Los_Angeles',
                        },
            }).execute()
            return response
    
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

