
import datetime
import argparse
import sys
import os
import Utils
import typing
import ActionNetworkAPI
import GoogleDriveAPI
import logging
import EmailAPI
import zipfile

class MembershipListProcessingException(Exception):
    pass

class Constants:
    # Paths
    WORKING_DIR = os.path.join(os.path.dirname(__file__), "workingDir")
    RETENTION_DATA_FILE_PATH = os.path.join(os.path.dirname(__file__),"adsa-retention-data.csv")
    ARCHIVE_FOLDER_PATH = os.path.join(os.path.dirname(__file__),"Archive")
    OUTPUT_DIR_PATH = os.path.join(os.path.dirname(__file__),"Output")
    DOWNLOAD_ZIP_PATH = os.path.join(WORKING_DIR,"downloadedList.zip")
    DOWNLOAD_ZIP_LIST_MEMBER = "austin_membership_list.csv"
    DOWNLOAD_LIST_PATH = os.path.join(WORKING_DIR,"austin_membership_list.csv")
    EMAIL_CREDS = os.path.join(os.path.dirname(__file__),"email.txt")
    EXPECTED_EMAIL_SUBJECT = "Austin Membership List"

    LEADERSHIP_EMAIL = "leadership@austindsa.org"
    MEMBERSHIP_EMAIL = "membership@austindsa.org"
    TECH_EMAIL = "tech@austindsa.org"
    
    LOG_NAME = f"membership_upload_logs_{datetime.datetime.strftime(datetime.datetime.now(),'%Y_%m_%d_%H_%M_%S')}.txt"
    LOG_PATH = os.path.join(WORKING_DIR,LOG_NAME)

    AN_API_KEY_FILE = "actionNetworkAPIKey.txt"

    EXPECTED_LIST_ATTACHMENT_NAME = "austin_membership_list.zip"
    ZIP_CODE_COL = "Zip_Code"
    
    COL_DO_NOT_INCLUDE = "N/A"
    # Only add but can map to same value 
    COLS_TO_KEEP_FOR_ARCHIVE = {
        "prefix"                       : False,
        "mailing_pref"                 : False,
        "actionkit_id"                 : False,
        "first_name"                   : False,
        "middle_name"                  : False,
        "last_name"                    : False,
        "suffix"                       : False,
        "billing_address1"             : False,
        "billing_address2"             : False,
        "billing_city"                 : False,
        "billing_state"                : False,
        "billing_zip"                  : False,
        # TODO Combine mailing addresses
        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_1 : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.ADDRESS_1 : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_2 : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.ADDRESS_2 : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_CITY : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.CITY : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_STATE : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.STATE : False,
        "country"                      : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL : True,
        "zip"                          : True,
        "best_phone"                   : False,
        "mobile_phone"                 : False,
        "home_phone"                   : False,
        "work_phone"                   : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL : False,
        "mail_preference"              : False,
        "do_not_call"                  : True,
        "p2ptext_optout"               : True,
        "join_date"                    : True,
        "xdate"                        : True,
        "membership_type"              : True,
        "monthly_dues_status"          : True,
        "annual_recurring_dues_status" : True,
        "yearly_dues_status"           : True,
        Utils.Constants.MEMBERSHIP_LIST_COLS.STANDING_COL : True,
        "memb_status_letter"           : True,
        "union_member"                 : True,
        "union_name"                   : True,
        "union_local"                  : True,
        "student_yes_no"               : True,
        "student_school_name"          : True,
        "ydsa_chapter"                 : True,
        "dsa_chapter"                  : True,
        "accomodations"                : True,
        "accommodations"               : True,
        "race"                         : True
    }

class CommmandFlags:
    FILENAME = "filename"
    AUTOMATE = "--automate"
    AUTOMATE_AN = "--auto_an"
    AUTOMATE_GDRIVE ="--auto_gd"
    DO_NOT_ARCHIVE = "--narch"
    DO_NOT_RETENTION = "--nret"
    DO_NOT_ACTION_NETWORK = "--nan"
    USE_LOCAL_RETENTION = "--local_retention"
    BACKGROUND = "--background"

    def __init__(self, filename : str, doNotArchive : bool, doNotRetention : bool, doNotActionNetwork : bool, automateActionNetwork : bool, automateGoogleDrive: bool, useLocalRetention : bool, useANBackground: bool) -> None:
        self.filename = filename
        self.archive = not doNotArchive
        self.retention = not doNotRetention
        self.actionNetwork = not doNotActionNetwork
        self.automateActionNetwork = automateActionNetwork
        self.automateGoogleDrive = automateGoogleDrive
        self.useLocalRetention = useLocalRetention
        self.useANBackground = useANBackground
    
def parseArgs():
    # I am using hardcoded strings here since you can't subscript the parsed args by the argument name
    # NOW WHY YOU CAN"T IS BEYONd ME and if you want to yell at python for me I would kiss you
    # Since the scope of the strings is literally just this function I figured making constants would be a bit much
    # Especially since the error from an incorrect string should stop the program before starting
    parser = argparse.ArgumentParser(description="Process the member list from National DSA")
    parser.add_argument(CommmandFlags.FILENAME,
                        help="File name of the membership list")    
    parser.add_argument(CommmandFlags.AUTOMATE, 
                        dest="automate", 
                        default=False, 
                        action="store_true", 
                        help = "Automate both Action network and Google Drive. If false will use local file for retention data.")
    parser.add_argument(CommmandFlags.AUTOMATE_AN, 
                        dest="automate_an", 
                        default=False, 
                        action="store_true", 
                        help = "Automate uploading to Action network")
    parser.add_argument(CommmandFlags.AUTOMATE_GDRIVE,       
                        dest="automate_gdrive", 
                        default=False, 
                        action="store_true",  
                        help = "Automate uploading retention data to Austin DSA Google drive (will download retention data from google drive). Overrides --local-retention")
    parser.add_argument(CommmandFlags.DO_NOT_ARCHIVE,        
                        dest="do_not_archive", 
                        default=False, 
                        action="store_true",  
                        help = "Skip archiving step, will skip uploading archive to google drive but not retention")
    parser.add_argument(CommmandFlags.DO_NOT_RETENTION,      
                        dest="do_not_retention", 
                        default=False, 
                        action="store_true", 
                        help = "Skip retention step, will skip any automated google drive steps")
    parser.add_argument(CommmandFlags.DO_NOT_ACTION_NETWORK, 
                        dest="do_not_action_network", 
                        default=False, 
                        action="store_true", 
                        help="Skip Action Network steps. Will skip upload if automated.")
    parser.add_argument(CommmandFlags.USE_LOCAL_RETENTION,   
                        dest="use_local_retention", 
                        default=True, 
                        action="store_true", 
                        help="If automating will use local retention file instead of downloading. Fails if local files DNE.")
    parser.add_argument(CommmandFlags.BACKGROUND,
                        dest="background",
                        default=False,
                        action="store_true",
                        help="If supplied then when uploading to AN will include the background tag. Theoretically should be faster however testing hasn't been clear."
                        )
    args = parser.parse_args()
    return CommmandFlags(args.filename, 
                         doNotArchive = args.do_not_archive, 
                         doNotRetention = args.do_not_retention, 
                         doNotActionNetwork = args.do_not_action_network,
                         automateActionNetwork = args.automate or args.automate_an,
                         automateGoogleDrive = args.automate or args.automate_gdrive,
                         useLocalRetention=args.use_local_retention,
                         useANBackground=args.background)

def setup():
    if not os.path.exists(Constants.WORKING_DIR):
        os.mkdir(Constants.WORKING_DIR)
    logging.basicConfig(filename=Constants.LOG_PATH, level=logging.INFO, format="%(asctime)s : %(levelname)s : %(message)s")
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.info("Starting membership list processing")

def setupEmail() -> EmailAPI.EmailAccount:
    logging.info("Setting up email account")
    logging.info("Reading from email")
    mailUsername = None
    mailPassword = None
    with open(Constants.EMAIL_CREDS, "r") as creds:
        lines = creds.readlines()
        mailUsername = lines[0].strip()
        mailPassword = lines[1].strip()
    if mailUsername is None or mailPassword is None:
        logging.error("Couldn't read email credentials")
        raise MembershipListProcessingException("Couldn't read email credentials")
    emailAccount = EmailAPI.EmailAccount(mailUsername, mailPassword)
    return emailAccount

def dowloadMembershipListFromEmail(emailAccount: EmailAPI.EmailAccount) -> str:
    if os.path.exists(Constants.DOWNLOAD_ZIP_PATH):
            logging.info("Found old downloaded zip file, deleting")
            os.remove(Constants.DOWNLOAD_ZIP_PATH)
            
    emailAccount.downloadZipAttachmentFromMostRecentUnreadEmail(Constants.MEMBERSHIP_EMAIL,
                                                                Constants.EXPECTED_EMAIL_SUBJECT,  
                                                                Constants.DOWNLOAD_ZIP_PATH,
                                                                datetime.datetime.now() - datetime.timedelta(days=10), 
                                                                expectedFileName=Constants.EXPECTED_LIST_ATTACHMENT_NAME)

    
    if os.path.exists(Constants.DOWNLOAD_LIST_PATH):
        logging.info("Found old downloaded list, deleting")
        os.remove(Constants.DOWNLOAD_LIST_PATH)

    logging.info(f"Unzipping downloaded list to {Constants.DOWNLOAD_LIST_PATH}")
    with zipfile.ZipFile(Constants.DOWNLOAD_ZIP_PATH) as downloadedZip:
        downloadedZip.extract(Constants.DOWNLOAD_ZIP_LIST_MEMBER, path=Constants.WORKING_DIR)
    return Constants.DOWNLOAD_LIST_PATH

def readMembershipList(path: str) -> (list,list):
    logging.info(f"Reading membership list from {path}")
    if not os.path.exists(path):
        logging.error(f"Input file DNE {path}")
        raise MembershipListProcessingException(f"Input file DNE {path}")
    if not path.endswith("csv"):
        logging.error(f"File is not csv {path}")
        raise MembershipListProcessingException(f"File is not csv {path}")
    
    # Save member counts to aggregate tracker
    logging.info("Reading input")
    cols,rows = Utils.readCSV(path)
    return cols,rows

def checkForNewCols(cols: list[str]):
    logging.info("Checking for new columns")
    newCols = []
    for c in cols:
        if c not in Constants.COLS_TO_KEEP_FOR_ARCHIVE:
            logging.error(c+"- Is not in the Keep in Archive mapping")
            newCols.append(c)
    if len(newCols) > 0:
        logging.error("Found new column not perfoming any operations")
        raise MembershipListProcessingException(f"Found new columns in list {newCols}")

def archiveAndObfuscate(cols: list[str], rows: list[str], googleDriveApi: typing.Optional[GoogleDriveAPI.GoogleDriveAPI]):
    logging.info("Archiving and obfuscating")
    # Convert file to archive obfuscate
    colIndexs = []
    newCols = []
    for index in range(len(cols)):
        if cols[index] in Constants.COLS_TO_KEEP_FOR_ARCHIVE and Constants.COLS_TO_KEEP_FOR_ARCHIVE[cols[index]]:
            colIndexs.append(index)
            newCols.append(cols[index])
    # Filter rows
    archiveRows = [[row[i].strip() for i in colIndexs] for row in rows]

    if googleDriveApi is not None:
        googleDriveApi.uploadArchiveRetentionData(cols=newCols, rows=archiveRows)
    else:
        archiveName = "members-"+Utils.Constants.TODAY_STR+".csv"
        Utils.writeCSVFile(os.path.join(Constants.ARCHIVE_FOLDER_PATH, archiveName), newCols, archiveRows)

def processRetentionData(cols: list[str], rows: list[str], flags: CommmandFlags, googleDriveApi: typing.Optional[GoogleDriveAPI.GoogleDriveAPI]):
    logging.info("Starting Retention processing")
    membersGoodStanding = 0
    membersMember = 0
    membersLapsed = 0
    standingIndex = -1
    for index in range(len(cols)):
        if cols[index].strip().lower() == Utils.Constants.MEMBERSHIP_LIST_COLS.STANDING_COL:
            standingIndex = index
            break
    if standingIndex == -1:
        logging.error("Couldn't find membership standing column")
        raise MembershipListProcessingException("Couldn't find membership standing column")
    for row in rows:
        if len(row) != len(cols):
            logging.error(f"Column Row Mismatch. Most likely a comma problem. Inspect the row in the input file and rearchive if wanted.{[x for x in zip(cols, row)]}")
            raise MembershipListProcessingException(f"Column Row Mismatch. Most likely a comma problem. Inspect the row in the input file and rearchive if wanted.{[x for x in zip(cols, row)]}")
            
        status = row[standingIndex].strip().lower()
        if status == Utils.Constants.MEMBERSHIP_STATUS.GOOD_STANDING:
            membersGoodStanding += 1
        elif status == Utils.Constants.MEMBERSHIP_STATUS.MEMBER:
            membersMember += 1
        elif status == Utils.Constants.MEMBERSHIP_STATUS.LAPSED:
            membersLapsed += 1
        else:
            logging.error(f"Found unexpected membership status: {status}")
            raise MembershipListProcessingException(f"Found unexpected membership status: {status}")
    if flags.useLocalRetention and not flags.automateGoogleDrive:
        Utils.appendCSVFile(Constants.RETENTION_DATA_FILE_PATH, (Utils.Constants.TODAY_STR, membersGoodStanding, membersMember, membersLapsed, membersGoodStanding+membersMember+membersLapsed))
    elif flags.automateGoogleDrive:
        googleDriveApi.uploadNewRetentionData(membersGoodStanding=membersGoodStanding, membersMember=membersMember, membersLapsed=membersLapsed)
    else:
        logging.error("Neither local retention nor automated google drive was specified. Not saving retention.")

def uploadToActionNetwork(cols: list[str], rows:list[str], useBackgroundProcessing:bool):
    # For uploads we will not convert to our old columns but instead use what national sends down
    # For non-automated will keep the conversion, but our columns include spaces and capital letters
    # The API connector will auto-lowercase
    # We shouldn't lose any columns but we may have duplicates
    logging.info("Uploading members to action network")
    # A bit redundant to build this map but it will make building the person more convient later
    # Also redundant to look up the col in the colToIndex map later when building people, but our col list length is small enough the simplicity and convience is worthwhile
    colToIndex = {}
    for index in range(len(cols)):
        colToIndex[cols[index]] = index
    nonCustomFields = set([Utils.Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL,
                        Utils.Constants.MEMBERSHIP_LIST_COLS.PHONE,
                        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_1,
                        Utils.Constants.MEMBERSHIP_LIST_COLS.ADDRESS_1,
                        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_2,
                        Utils.Constants.MEMBERSHIP_LIST_COLS.ADDRESS_2,
                        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_CITY,
                        Utils.Constants.MEMBERSHIP_LIST_COLS.CITY,
                        Utils.Constants.MEMBERSHIP_LIST_COLS.STATE,
                        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_STATE,
                        Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL,
                        Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL2,
                        Utils.Constants.MEMBERSHIP_LIST_COLS.FIRST_NAME,
                        Utils.Constants.MEMBERSHIP_LIST_COLS.LAST_NAME])
    peopleToPost = []
    for row in rows:
        customFields = {}
        for col in cols:
            if col in nonCustomFields:
                continue
            customFields[col] = row[colToIndex[col]]

        peopleToPost.append(ActionNetworkAPI.Person(firstName=row[colToIndex[Utils.Constants.MEMBERSHIP_LIST_COLS.FIRST_NAME]],
                                                    lastName=row[colToIndex[Utils.Constants.MEMBERSHIP_LIST_COLS.LAST_NAME]],
                                                    email=row[colToIndex[Utils.Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL]],
                                                    phone=row[colToIndex[Utils.Constants.MEMBERSHIP_LIST_COLS.PHONE]],
                                                    customFields=customFields,
                                                    address=ActionNetworkAPI.PersonAddress(
                                                        region=row[Utils.getValueWithAnyName(colToIndex, [Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_STATE, Utils.Constants.MEMBERSHIP_LIST_COLS.STATE])],
                                                        zip_code=row[Utils.getValueWithAnyName(colToIndex, [Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL, Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL2])],
                                                        city=row[Utils.getValueWithAnyName(colToIndex, [Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_CITY, Utils.Constants.MEMBERSHIP_LIST_COLS.CITY])],
                                                        address_lines=[row[Utils.getValueWithAnyName(colToIndex, [Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_1, Utils.Constants.MEMBERSHIP_LIST_COLS.ADDRESS_1])], 
                                                                    row[Utils.getValueWithAnyName(colToIndex, [Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_2, Utils.Constants.MEMBERSHIP_LIST_COLS.ADDRESS_2])]]
                                                    )))
    api = ActionNetworkAPI.ActionNetworkAPI(apiKey=ActionNetworkAPI.ActionNetworkAPI.readAPIKeyFromFile("actionNetworkAPIKey.txt"))
    api.postPeople(people=peopleToPost, useBackgroundProcessing=useBackgroundProcessing)

def main(args):
    setup()
    emailAccount = None
    try:
        flags = parseArgs()
        inputFileName = flags.filename
        if flags.filename == "EMAIL":
            emailAccount = setupEmail()
            inputFileName = dowloadMembershipListFromEmail(emailAccount)

        cols,rows = readMembershipList(inputFileName)

        checkForNewCols(cols)        

        googleDriveApi = None
        if flags.automateGoogleDrive:
            logging.info("Setting up Google Drive API")
            googleDriveApi = GoogleDriveAPI.GoogleDriveAPI()
 
        # Copy to archive
        if flags.archive:
            archiveAndObfuscate(cols,rows,googleDriveApi)
        else:
            logging.info("Skipping Archiving")

        if flags.retention:
            processRetentionData(cols,rows,flags,googleDriveApi)
        else:
            logging.info("Skipping Retention")

        # Create csv for action network
        if flags.actionNetwork:
            if not flags.automateActionNetwork:
                # Just directly copy over, we no longer convert to special custom fields since it could create stale custom fields
                logging.info("Creating action network upload file")
                Utils.writeCSVFile(os.path.join(Constants.OUTPUT_DIR_PATH, "action-network-"+Utils.Constants.TODAY_STR+".csv"), cols, rows)
            else:
                uploadToActionNetwork(cols,rows,flags.useANBackground)
        else:
            logging.info("Skipping Action Network")
    
        if emailAccount is not None:
            emailAccount.sendMessage(Constants.LEADERSHIP_EMAIL, "Successful Membership Upload", f"Uploaded Membership List",[EmailAPI.Attachement(Constants.LOG_PATH,Constants.LOG_NAME)])
            emailAccount.sendMessage(Constants.MEMBERSHIP_EMAIL, "Successful Membership Upload", f"Uploaded Membership List",[EmailAPI.Attachement(Constants.LOG_PATH,Constants.LOG_NAME)])
            emailAccount.sendMessage(Constants.TECH_EMAIL, "Successful Membership Upload", f"Uploaded Membership List",[EmailAPI.Attachement(Constants.LOG_PATH,Constants.LOG_NAME)])

    except Exception as err:
        logging.error("Failed to process membership list due to error")
        logging.exception(err)
        if emailAccount is not None:
            emailAccount.markDownloadedEmailAsUnread()
            emailAccount.sendMessage(Constants.LEADERSHIP_EMAIL, "Failed Membership Upload", f"Failed to upload membership script due to:\n {err}",[EmailAPI.Attachement(Constants.LOG_PATH,Constants.LOG_NAME)])
            emailAccount.sendMessage(Constants.MEMBERSHIP_EMAIL, "Failed Membership Upload", f"Failed to upload membership script due to:\n {err}",[EmailAPI.Attachement(Constants.LOG_PATH,Constants.LOG_NAME)])
            emailAccount.sendMessage(Constants.TECH_EMAIL, "Failed Membership Upload", f"Failed to upload membership script due to:\n {err}",[EmailAPI.Attachement(Constants.LOG_PATH,Constants.LOG_NAME)])

if __name__ == "__main__":
    main(sys.argv)
        