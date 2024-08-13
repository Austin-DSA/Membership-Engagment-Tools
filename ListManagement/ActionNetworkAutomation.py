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
    hasEndtime : bool
    startTime : datetime.datetime
    locationName : str
    address : str
    city : str
    state : str
    zip : str
    description: str
    insturctions: str
    endTime : typing.Optional[datetime.datetime] = None


# TODO: Logging
# TODO: Errors

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

        LOCATION_INPUT = "event-location"
        ADDRESS_INPUT = "event-address"
        CITY_INPUT = "event-city"
        STATE_INPUT = "event-state"
        ZIP_INPUT = "event-zip"
        COUNTRY_INPUT = "form-country"

        DESCRIPTION_INPUT = "event-description"

        NEXT_STEP_BUTTON = "event-publish_link_button"

    def exists(self) -> bool:
        pass

    def fillOutEventInfo(self, eventInfo: EventInfo):
        pass

class ANAutomator:

    @classmethod
    def createEvent(self, title, name):
        logging.info("ANAutomator: Starting Driver")
        driver = selenium.webdriver.Edge()
        driver.implicitly_wait(2)
        driver.get(DashboardScreen.Constants.AUSTIN_DSA_DASHBOARD)

        logging.info("ANAutomator: Checking if we need to login")
        loginScreen = LoginScreen.tryToCreate(driver)
        if loginScreen is not None:
            logging.info("ANAutomator: LoginScreen detected, logging in")
            loginScreen.login(email="", password="")

        dashboardScreen = DashboardScreen.tryToCreate(driver)
        if dashboardScreen is None:
            logging.error("ANAutomator: Can't find dashboard screen")
            raise Exception("Not in Dashboard")
        
        logging.info("ANAutomator: Selecting Create Event Item")
        dashboardScreen.selectFromCreateActionMenu(DashboardScreen.ActionsInCreateActionMenu.EVENT)

        time.sleep(5)
        


        
        


        