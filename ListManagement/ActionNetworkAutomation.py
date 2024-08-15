import selenium
import selenium.webdriver
import selenium.webdriver.common
from selenium.webdriver.common.by import By
import time
import dataclasses
import datetime
import typing
import abc
import logging
@dataclasses.dataclass
class EventInfo:
    title : str
    # isVirual : bool # Don't need right now since we put zoom in instructions
    startTime : datetime.datetime
    locationName : str
    address : str
    city : str
    state : str = "TX"
    zip : str
    country : str = "US"
    description: str
    insturctions: str
    endTime : typing.Optional[datetime.datetime] = None


# TODO: Logging
# TODO: Errors

class Utils:

    @staticmethod
    def typeTextIntoElement(elem, text: str):
        elem.clear()
        elem.send_keys(text)

class Screen(abc.ABC):

    @classmethod
    def tryToCreate(self, driver, *args, **kwargs) -> typing.Optional[typing.Self]:
        screen = self(driver, *args, **kwargs)
        if not screen.exists():
            return None
        return screen

    def exists(self) -> bool:
        self.__class__.exists(driver=self.driver)

    def __init__(self, driver):
        super().__init__()
        self.driver = driver

    @abc.abstractmethod
    def exists(self) -> bool:
        pass

class LoginScreen(Screen):
    class Constants:
        AN_SIGN_IN_URL = "https://actionnetwork.org/users/sign_in"
    
    class IDs:
        EMAIL_ID = "ipt-login"
        PASSWORD_ID = "iptpassword"
        SUBMIT_ID = "commit"

    def exists(self) -> bool:
        try:
            _ = self._emailBox()
            _ = self._passwordBox()
            _ = self._submitButton()
            return True
        except Exception as e:
            logging.info("LoginScreen: Does not exist %s", str(e))
            return False
    
    def _emailBox(self):
        return self.driver.find_element(By.ID, LoginScreen.IDs.EMAIL_ID)
    def _passwordBox(self):
        return self.driver.find_element(By.ID, LoginScreen.IDs.PASSWORD_ID)
    def _submitButton(self):
        return self.driver.find_element(By.NAME, LoginScreen.IDs.SUBMIT_ID)
    
    def login(self, email, password):
        emailBox = self._emailBox()
        passwordBox = self._passwordBox()
        submitButton = self._submitButton()

        logging.info("LoginScreen: Logging in with user %s", email)
        emailBox.clear()
        emailBox.send_keys(email)

        passwordBox.clear()
        passwordBox.send_keys(password)

        submitButton.click()

class DashboardScreen(Screen):
    
    class Constants:
        AUSTIN_DSA_DASHBOARD = "https://actionnetwork.org/groups/austin-dsa/manage"
    
    class IDs:
        CREATE_ACTION_MENU_ID = "group_create_action"
        TABS = "tabs"
    
    class Classes:
        MANAGING_TITLE = "managing_title"

    class Texts:
        CURRENTLY_MANAGING = "Currently Managing Group:" 

    class ActionsInCreateActionMenu:
        EVENT = "Event"
    
    def __init__(self, driver, groupText = "Austin DSA"):
        super().__init__(driver)
        self.groupText = groupText
    
    def _createActionMenu(self):
        return self.driver.find_element(By.ID, DashboardScreen.IDs.CREATE_ACTION_MENU_ID)
    
    def exists(self) -> bool:
        try:
            containgDiv = self.driver.find_element(By.CLASS_NAME, DashboardScreen.Classes.MANAGING_TITLE)
            h6s = containgDiv.find_elements(By.TAG_NAME, "h6")
            found = False
            for h6 in h6s:
                if h6.text.lower() == DashboardScreen.Texts.CURRENTLY_MANAGING.lower():
                    found = True
                    break
            if not found: 
                logging.error("DashboardScreen: Couldn't find currently managing text")
                return False
            
            h2s = containgDiv.find_elements(By.TAG_NAME, "h2")
            found = False
            for h2 in h2s:
                if h2.text.lower() == self.groupText.lower():
                    found = True
                    break
            if not found: 
                logging.error("DashboardScreen: Couldn't find group text %s", self.groupText)
                return False
            
            logging.info("DashboardScreen: Exists")
            return True
        except Exception as e:
            logging.info("DashboardScreen: Does not exist %s", str(e))
            return False
    
    def selectFromCreateActionMenu(self, action):
        createActionMenu = self._createActionMenu()
        selectedAction = createActionMenu.find_element(By.LINK_TEXT, action)
        selectedAction.click()

class EditEventScreen(Screen):

    class IDs:
        TITLE_INPUT = "event-title"
        
        IS_VIRTUAL_INPUT = "event_physical_location_toggle"
        HAS_END_TIME_INPUT = "event_endtime_toggle"
        
        START_DATE_INPUT = "event-start-date"
        END_DATE_INPUT = "event-end-date"

        LOCATION_INPUT = "event-location"
        ADDRESS_INPUT = "event-address"
        CITY_INPUT = "event-city"
        STATE_INPUT = "event-state"
        ZIP_INPUT = "event-zip"
        COUNTRY_INPUT = "form-country"

        DESCRIPTION_INPUT = "event-description"

        NEXT_STEP_BUTTON = "event-publish_link_button"

    class Classes:
        DATETIME_PICKER = "datetimepicker-days"
        DATETIME_PICKER_SWITCH = "switch"
        DATETIME_PICKER_FORWARD = "next"
        DATETIME_PICKER_PREV = "prev"

        DATETIME_PICKER_DAY = "day"
    

    def _titleInputBox(self):
        return self.driver.find_element(EditEventScreen.IDs.TITLE_INPUT)
    def _isVirtualICheckBox(self):
        return self.driver.find_element(EditEventScreen.IDs.IS_VIRTUAL_INPUT)
    def _hasEndTimeICheckBox(self):
        return self.driver.find_element(EditEventScreen.IDs.HAS_END_TIME_INPUT)
    def _startDateInputBox(self):
        return self.driver.find_element(EditEventScreen.IDs.START_DATE_INPUT)
    def _endDateInputBox(self):
        return self.driver.find_element(EditEventScreen.IDs.END_DATE_INPUT)
    def _locationInputBox(self):
        return self.driver.find_element(EditEventScreen.IDs.LOCATION_INPUT)
    def _addressInputBox(self):
        return self.driver.find_element(EditEventScreen.IDs.ADDRESS_INPUT)
    def _cityInputBox(self):
        return self.driver.find_element(EditEventScreen.IDs.CITY_INPUT)
    def _stateInputDropdown(self):
        return self.driver.find_element(EditEventScreen.IDs.STATE_INPUT)
    def _zipInputBox(self):
        return self.driver.find_element(EditEventScreen.IDs.ZIP_INPUT)
    def _countryInputDropdown(self):
        return self.driver.find_element(EditEventScreen.IDs.COUNTRY_INPUT)
    def _descriptionInputBox(self):
        return self.driver.find_element(EditEventScreen.IDs.DESCRIPTION_INPUT)
    def _nextStepButton(self):
        return self.driver.find_element(EditEventScreen.IDs.NEXT_STEP_BUTTON)
    
    def exists(self) -> bool:
        try:
            _ = self._titleInputBox()
            _ = self._isVirtualICheckBox()
            _ = self._hasEndTimeICheckBox()
            _ = self._startDateInputBox()
            _ = self._locationInputBox()
            _ = self._addressInputBox()
            _ = self._cityInputBox()
            _ = self._stateInputDropdown()
            _ = self._zipInputBox()
            _ = self._countryInputDropdown()
            _ = self._descriptionInputBox()
            _ = self._nextStepButton()
            return True
        except Exception as e:
            logging.info("EditEventScreen: Does not exist %s", str(e))
            return False
        
    def _fillOutDatePicker(self, time: datetime.datetime):
        dateTimePicker = self.driver.find_element(By.CLASS_NAME, EditEventScreen.Classes.DATETIME_PICKER)
        inCorrectMonthYear = False
        wantedMonthYearText = time.strftime("%B %Y")
        while not inCorrectMonthYear:
            currentMonthYearElem = dateTimePicker.find_element(By.CLASS_NAME, EditEventScreen.Classes.DATETIME_PICKER_SWITCH)
            currentMonthYear = datetime.datetime.strptime(currentMonthYearElem.text, "%B %Y")
            if currentMonthYear.month == time.month and currentMonthYear.year == time.year:
                logging.info("EditEventScreen: Date Picker is in correct month-year %s", currentMonthYearElem.text)
                inCorrectMonthYear = True
            elif currentMonthYear < time:
                logging.info("EditEventScreen: Date Picker is in %s which is BEFORE %s, going forwards", currentMonthYearElem.text, wantedMonthYearText)
                dateTimePicker.find_element(By.CLASS_NAME, EditEventScreen.Classes.DATETIME_PICKER_FORWARD).click()
            else:
                logging.info("EditEventScreen: Date Picker is in %s which is AFTER %s, going backwards", currentMonthYearElem.text, wantedMonthYearText)
                dateTimePicker.find_element(By.CLASS_NAME, EditEventScreen.Classes.DATETIME_PICKER_FORWARD).click()
        
        logging.info("EditEventScren: Picking day %d from year month", time.day)
        tdElements = dateTimePicker.find_elements(By.TAG_NAME, "td")
        foundDay = False
        dayString = str(time.day)
        for tdElem in tdElements:
            if tdElem.text == dayString:
                foundDay = True
                tdElem.click()
                break
        if not foundDay:
            logging.error("EditEventScreen: Could not find day %s", dayString)
            raise Exception("Couldn't set date %s", str(time))
        
        logging.info("EditEventScreen: Setting hour to %s", str(time.hour))
        isAM = time.hour < 12
        hourStr = time.strftime("%I")
        # Get rid of leading 0
        if hourStr[0] == '0':
            hourStr = hourStr[1:]
        className = f"hour hour_{"am" if isAM else "pm"}"
        spanElems = dateTimePicker.find_elements(By.CLASS_NAME, className)
        foundHour = False
        for spanElem in spanElems:
            if spanElem.text == hourStr:
                foundHour = True
                spanElem.click()


        
        
    def fillOutEventInfo(self, eventInfo: EventInfo):
        logging.info("EditEventScreen: Setting title to %s", eventInfo.title)
        Utils.typeTextIntoElement(self._titleInputBox(), eventInfo.title)

        logging.info("EditEventScreen: Setting Location to %s", eventInfo.locationName)
        Utils.typeTextIntoElement(self._locationInputBox(), eventInfo.locationName)

        logging.info("EditEventScreen: Setting Address to %s", eventInfo.address)
        Utils.typeTextIntoElement(self._addressInputBox(), eventInfo.address)

        logging.info("EditEventScreen: Setting City to %s", eventInfo.city)
        Utils.typeTextIntoElement(self._cityInputBox(), eventInfo.city)

        logging.info("EditEventScreen: Setting Zip to %s", eventInfo.zip)
        Utils.typeTextIntoElement(self._zipInputBox(), eventInfo.zip)

        logging.info("EditEventScreen: Setting Description to %s", eventInfo.description)
        Utils.typeTextIntoElement(self._descriptionInputBox(), eventInfo.description)

        logging.info("EditEventScreen: Setting State to %s", eventInfo.state)
        stateSelectDropdown = self._stateInputDropdown()
        stateSelectDropdown.selectByValue(eventInfo.state)

        logging.info("EditEventScreen: Setting Country to %s", eventInfo.country)
        countrySelectDropdown = self._countryInputDropdown()
        countrySelectDropdown.selectByValue(eventInfo.country)

        logging.info("EditEventScreen: Setting start date to %s", str(eventInfo.startTime))
        self._startDateInputBox().click()
        self._fillOutDatePicker(eventInfo.startTime)

        if eventInfo.endTime is not None:
            logging.info("EditEventScreen: Setting end date to %s", str(eventInfo.endTime))
            self._hasEndTimeICheckBox().click()
            self._endDateInputBox().click()
            self._fillOutDatePicker(eventInfo.endTime)

    def goToNextStep(self):
        self._nextStepButton().click()

class ANAutomator:

    @classmethod
    def createEvent(self, eventInfo: EventInfo, email: str, password: str):
        logging.info("ANAutomator: Starting Driver")
        driver = selenium.webdriver.Edge()
        driver.implicitly_wait(2)
        driver.get(DashboardScreen.Constants.AUSTIN_DSA_DASHBOARD)

        logging.info("ANAutomator: Checking if we need to login")
        loginScreen = LoginScreen.tryToCreate(driver)
        if loginScreen is not None:
            logging.info("ANAutomator: LoginScreen detected, logging in")
            loginScreen.login(email=email, password=password)

        dashboardScreen = DashboardScreen.tryToCreate(driver)
        if dashboardScreen is None:
            logging.error("ANAutomator: Can't find dashboard screen")
            raise Exception("Not in Dashboard")
        
        logging.info("ANAutomator: Selecting Create Event Item")
        dashboardScreen.selectFromCreateActionMenu(DashboardScreen.ActionsInCreateActionMenu.EVENT)

        editEventScreen = EditEventScreen.tryToCreate(driver)
        if editEventScreen is None:
            logging.error("ANAutomator: Can't find edit event screen")
            raise Exception("Not in edit event screen")
        logging.info("ANAutomator: Filling out event info")
        editEventScreen.fillOutEventInfo(eventInfo)

        logging.info("ANAutomator: Moving to action confirmation screen")
        editEventScreen.goToNextStep()

        time.sleep(5)
        


        
        


        