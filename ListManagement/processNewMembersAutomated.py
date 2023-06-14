
import datetime
import argparse
import sys
import os
import Utils
import typing
import ActionNetworkAPI
import GoogleDriveAPI

class Constants:
    # Paths
    RETENTION_DATA_FILE_PATH = os.path.join(os.path.dirname(__file__),"adsa-retention-data.csv")
    ARCHIVE_FOLDER_PATH = os.path.join(os.path.dirname(__file__),"Archive")
    OUTPUT_DIR_PATH = os.path.join(os.path.dirname(__file__),"Output")
    
    ZIP_CODE_COL = "Zip_Code"
    
    COL_DO_NOT_INCLUDE = "N/A"
    COL_TO_ACTION_NETWORK = {
        "prefix"                        : COL_DO_NOT_INCLUDE,
        "mailing_pref"                  : COL_DO_NOT_INCLUDE,
        "actionkit_id"                        : COL_DO_NOT_INCLUDE,
        Utils.Constants.MEMBERSHIP_LIST_COLS.FIRST_NAME : "first_name",	
        "middle_name"                  : COL_DO_NOT_INCLUDE,	
        Utils.Constants.MEMBERSHIP_LIST_COLS.LAST_NAME : "last_name",	
        "suffix"                       : COL_DO_NOT_INCLUDE,
        "billing_address1"       : COL_DO_NOT_INCLUDE,	
        "billing_address2"       : COL_DO_NOT_INCLUDE,	
        "billing_city"                 : COL_DO_NOT_INCLUDE,
        "billing_state"                : COL_DO_NOT_INCLUDE,	
        "billing_zip"                  : COL_DO_NOT_INCLUDE,
        # TODO Combine mailing addresses
        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_1  : "address",
        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_2  : COL_DO_NOT_INCLUDE,
        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_CITY       : "city",
        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_STATE      : "state",
        Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL            : "zip_code",
        Utils.Constants.MEMBERSHIP_LIST_COLS.PHONE              : "can2_phone",
        "mobile_phone"                 : COL_DO_NOT_INCLUDE,
        "home_phone"                   : COL_DO_NOT_INCLUDE,
        "work_phone"                   : COL_DO_NOT_INCLUDE,
        Utils.Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL : "email",
        "mail_preference"              : COL_DO_NOT_INCLUDE,	
        "do_not_call"                  : "Do_Not_Call",
        "p2ptext_optout"               : "p2ptext_optout",
        "join_date"                    : "Join_Date",
        "xdate"                        : "Xdate",
        "membership_type"              : COL_DO_NOT_INCLUDE,
        "monthly_dues_status"          : COL_DO_NOT_INCLUDE,	
        "annual_recurring_dues_status" : COL_DO_NOT_INCLUDE,
        Utils.Constants.MEMBERSHIP_LIST_COLS.STANDING_COL : "Membership Status",
        "memb_status_letter"           : "memb_status_letter",
        "union_member"                 : "Are You a Union Member?",
        "union_name"                   : "Union",
        "union_local"                  : "Union Local",
        "student_yes_no"               : "student_yes_no",
        "student_school_name"          : "student_school_name",	
        "ydsa_chapter"                 : "YDSA Chapter",
        "dsa_chapter"                  : "DSA_chapter",
        "accomodations"                : "accomodations"
    }
    COLS_TO_KEEP_FOR_ARCHIVE = {
        "prefix"                        : False,
        "mailing_pref"                  : False,
        "actionkit_id"                        : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.FIRST_NAME : False,
        "middle_name"                  : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.LAST_NAME : False,
        "suffix"                       : False,
        "billing_address1"       : False,
        "billing_address2"       : False,
        "billing_city"                 : False,
        "billing_state"                : False,
        "billing_zip"                  : False,
        # TODO Combine mailing addresses
        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_1 : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_2 : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_CITY : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_STATE : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL : True,
        Utils.Constants.MEMBERSHIP_LIST_COLS.PHONE                   : False,
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
        Utils.Constants.MEMBERSHIP_LIST_COLS.STANDING_COL : True,
        "memb_status_letter"           : True,
        "union_member"                 : True,
        "union_name"                   : True,
        "union_local"                  : True,
        "student_yes_no"               : True,
        "student_school_name"          : True,
        "ydsa_chapter"                 : True,
        "dsa_chapter"                  : True,
        "accomodations"                : True
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

    def __init__(self, filename : str, doNotArchive : bool, doNotRetention : bool, doNotActionNetwork : bool, automateActionNetwork : bool, automateGoogleDrive: bool, useLocalRetention : bool) -> None:
        self.filename = filename
        self.archive = not doNotArchive
        self.retention = not doNotRetention
        self.actionNetwork = not doNotActionNetwork
        self.automateActionNetwork = automateActionNetwork
        self.automateGoogleDrive = automateGoogleDrive
        self.useLocalRetention = useLocalRetention
    
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
                        help = "Automate uploading retention data to Austin DSA Google drive (will download retention data from google drive)")
    parser.add_argument(CommmandFlags.DO_NOT_ARCHIVE,        
                        dest="do_not_archive", 
                        default=False, action="store_true",  
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
                        default=False, 
                        action="store_true", 
                        help="If automating will use local retention file instead of downloading. Fails if local files DNE.")
    args = parser.parse_args()
    return CommmandFlags(args.filename, 
                         doNotArchive = args.do_not_archive, 
                         doNotRetention = args.do_not_retention, 
                         doNotActionNetwork = args.do_not_action_network,
                         automateActionNetwork = args.automate or args.automate_an,
                         automateGoogleDrive = args.automate or args.automate_gdrive,
                         useLocalRetention=args.use_local_retention)
    
def main(args):
    flags = parseArgs()
    inputCSV = os.path.join(os.path.dirname(__file__), flags.filename)
    print(inputCSV)
    if not os.path.exists(inputCSV):
        print("Input file DNE")
        return
    if not inputCSV.endswith("csv"):
        print("File is not csv")
        return
    
    # Save member counts to aggregate tracker
    print("Reading input")
    cols,rows = Utils.readCSV(inputCSV)

    # Check for new columns
    print("Checking for new columns")
    foundNewCol = False
    for c in cols:
        if c not in Constants.COL_TO_ACTION_NETWORK:
            print(c+"- Is not in the Action Network mapping")
            foundNewCol = True
        if c not in Constants.COLS_TO_KEEP_FOR_ARCHIVE:
            print(c+"- Is not in the Keep in Archive mapping")
            foundNewCol = True
    if foundNewCol:
        print("Found new column not perfoming any operations")
        return

    googleDriveApi = None
    if flags.automateGoogleDrive:
        googleDriveApi = GoogleDriveAPI.GoogleDriveAPI()

    # Copy to archive
    if flags.archive:
        print("Archiving and obfuscating")
        # Convert file to archive obfuscate
        colIndexs = []
        newCols = []
        for index in range(len(cols)):
            if cols[index] in Constants.COLS_TO_KEEP_FOR_ARCHIVE and Constants.COLS_TO_KEEP_FOR_ARCHIVE[cols[index]]:
                colIndexs.append(index)
                newCols.append(cols[index])
        # Filter rows
        archiveRows = [[row[i].strip() for i in colIndexs] for row in rows]

        if flags.automateGoogleDrive:
            googleDriveApi.uploadArchiveRetentionData(cols=newCols, rows=archiveRows)
        else:
            archiveName = "members-"+Utils.Constants.TODAY_STR+".csv"
            Utils.writeCSVFile(os.path.join(Constants.ARCHIVE_FOLDER_PATH, archiveName), newCols, archiveRows)

    if flags.retention:
        print("Retention")
        membersGoodStanding = 0
        membersMember = 0
        membersLapsed = 0
        standingIndex = -1
        for index in range(len(cols)):
            if cols[index].strip().lower() == Utils.Constants.MEMBERSHIP_LIST_COLS.STANDING_COL:
                standingIndex = index
                break
        if standingIndex == -1:
            print("Couldn't find membership standing column")
            return
        for row in rows:
            if len(row) != len(cols):
                print("Column Row Mismatch. Most likely a comma problem. Inspect the row in the input file and rearchive if wanted.")
                print([x for x in zip(cols, row)])
                return
            status = row[standingIndex].strip().lower()
            if status == Utils.Constants.MEMBERSHIP_STATUS.GOOD_STANDING:
                membersGoodStanding += 1
            elif status == Utils.Constants.MEMBERSHIP_STATUS.MEMBER:
                membersMember += 1
            elif status == Utils.Constants.MEMBERSHIP_STATUS.LAPSED:
                membersLapsed += 1
            else:
                print("Found unexpected value")
                print(status)
                return
        if flags.useLocalRetention:
            Utils.appendCSVFile(Constants.RETENTION_DATA_FILE_PATH, (Constants.TODAY_STR, membersGoodStanding, membersMember, membersLapsed, membersGoodStanding+membersMember+membersLapsed))
        elif flags.automateGoogleDrive:
            googleDriveApi.uploadNewRetentionData(membersGoodStanding=membersGoodStanding, membersMember=membersMember, membersLapsed=membersLapsed)
        else:
            print("Neither local retention nor automated google drive was specified. Not saving retention.")
    else:
        print("Skipping Retention")

    # Create csv for action network
    if flags.actionNetwork:
        if not flags.automateActionNetwork:
            print("Creating action network upload file")
            # Convert cols to Action network
            colIndexs = []
            newCols = []
            for index in range(len(cols)):
                if cols[index] in Constants.COL_TO_ACTION_NETWORK and Constants.COL_TO_ACTION_NETWORK[cols[index]] != Constants.COL_DO_NOT_INCLUDE:
                    colIndexs.append(index)
                    newCols.append(Constants.COL_TO_ACTION_NETWORK[cols[index]])
            # Filter rows
            actionNetworkRows = [[row[i].strip() for i in colIndexs] for row in rows]
            Utils.writeCSVFile(os.path.join(Constants.OUTPUT_DIR_PATH, "action-network-"+Constants.TODAY_STR+".csv"), newCols, actionNetworkRows)
        else:
            # For uploads we will not convert to our old columns but instead use what national sends down
            # For non-automated will keep the conversion, but our columns include spaces and capital letters
            # The API connector will auto-lowercase
            # We shouldn't lose any columns but we may have duplicates
            print("Uploading members to action network")
            # A bit redundant to build this map but it will make building the person more convient later
            # Also redundant to look up the col in the colToIndex map later when building people, but our col list length is small enough the simplicity and convience is worthwhile
            colToIndex = {}
            for index in range(len(cols)):
                colToIndex[cols[index]] = index
            nonCustomFields = set([Utils.Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL,
                                   Utils.Constants.MEMBERSHIP_LIST_COLS.PHONE,
                                   Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_1,
                                   Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_2,
                                   Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_CITY,
                                   Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_STATE,
                                   Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL,
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
                                                                region=row[colToIndex[Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_STATE]],
                                                                zip_code=row[colToIndex[Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL]],
                                                                city=row[colToIndex[Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_CITY]],
                                                                address_lines=[row[colToIndex[Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_1]], 
                                                                               row[colToIndex[Utils.Constants.MEMBERSHIP_LIST_COLS.MAILING_ADDRESS_2]]]
                                                            )))
            api = ActionNetworkAPI.ActionNetworkAPI(apiKey=ActionNetworkAPI.ActionNetworkAPI.readAPIKeyFromFile("actionNetworkAPIKey.txt"))
            api.postPeople(people=peopleToPost)
    else:
        print("Skipping Action Network")

if __name__ == "__main__":
    main(sys.argv)