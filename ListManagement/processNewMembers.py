
import datetime
import csv
from pickle import TRUE
import shutil
import sys
import os
import Utils

class Constants:
    # Paths
    RETENTION_DATA_FILE_PATH = os.path.join(os.path.dirname(__file__),"adsa-retention-data.csv")
    ARCHIVE_FOLDER_PATH = os.path.join(os.path.dirname(__file__),"Archive")
    OUTPUT_DIR_PATH = os.path.join(os.path.dirname(__file__),"Output")
    TODAY_STR = datetime.date.today().isoformat()
    ZIP_CODE_COL = "Zip_Code"
    
    COL_DO_NOT_INCLUDE = "N/A"
    COL_TO_ACTION_NETWORK = {
        "prefix"                        : COL_DO_NOT_INCLUDE,
        "mailing_pref"                  : COL_DO_NOT_INCLUDE,
        "actionkit_id"                        : COL_DO_NOT_INCLUDE,
        "first_name"                   : "first_name",	
        "middle_name"                  : COL_DO_NOT_INCLUDE,	
        "last_name"                    : "last_name",	
        "suffix"                       : COL_DO_NOT_INCLUDE,
        "billing_address1"       : COL_DO_NOT_INCLUDE,	
        "billing_address2"       : COL_DO_NOT_INCLUDE,	
        "billing_city"                 : COL_DO_NOT_INCLUDE,
        "billing_state"                : COL_DO_NOT_INCLUDE,	
        "billing_zip"                  : COL_DO_NOT_INCLUDE,
        # TODO Combine mailing addresses
        "mailing_address1"             : "address",
        "mailing_address2"             : COL_DO_NOT_INCLUDE,
        "mailing_city"                 : "city",
        "mailing_state"                : "state",
        Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL : "zip_code",
        "best_phone"                   : "can2_phone",
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
        "first_name"                   : False,
        "middle_name"                  : False,
        "last_name"                    : False,
        "suffix"                       : False,
        "billing_address1"       : False,
        "billing_address2"       : False,
        "billing_city"                 : False,
        "billing_state"                : False,
        "billing_zip"                  : False,
        # TODO Combine mailing addresses
        "mailing_address1"             : False,
        "mailing_address2"             : False,
        "mailing_city"                 : False,
        "mailing_state"                : False,
        Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL : True,
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
    DO_NOT_ARCHIVE = "-narch"
    DO_NOT_RETENTION = "-nret"
    DO_NOT_ACTION_NETWORK = "-nan"
    HELP = "-h"

    def __init__(self, filename, doNotArchive, doNotRetention, doNotActionNetwork) -> None:
        self.filename = filename
        self.archive = not doNotArchive
        self.retention = not doNotRetention
        self.actionNetwork = not doNotActionNetwork
    
def parseArgs(args):
    if CommmandFlags.HELP in args:
        print("usage: <inputCSV> [-narch] [-nret] [-nan]")
        sys.exit(0)
    if len(args) < 2:
        print("First argument is necessary and must be the file name")
    fileName = args[1]
    return CommmandFlags(fileName, CommmandFlags.DO_NOT_ARCHIVE in args, CommmandFlags.DO_NOT_RETENTION in args, CommmandFlags.DO_NOT_ACTION_NETWORK in args)
    
def main(args):
    flags = parseArgs(args)
    inputCSV = os.path.join(os.path.dirname(__file__), flags.filename)
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

    # Get zip code

    # Copy to archive
    if flags.archive:
        print("Archiving and obfuscating")
        archiveName = "members-"+Constants.TODAY_STR+".csv"
        # shutil.copyfile(inputCSV, os.path.join(Constants.ARCHIVE_FOLDER_PATH, archiveName))
        # Convert file to archive obfuscate
        colIndexs = []
        newCols = []
        for index in range(len(cols)):
            if cols[index] in Constants.COLS_TO_KEEP_FOR_ARCHIVE and Constants.COLS_TO_KEEP_FOR_ARCHIVE[cols[index]]:
                colIndexs.append(index)
                newCols.append(cols[index])
        # Filter rows
        archiveRows = [[row[i].strip() for i in colIndexs] for row in rows]
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
        Utils.appendCSVFile(Constants.RETENTION_DATA_FILE_PATH, (Constants.TODAY_STR, membersGoodStanding, membersMember, membersLapsed, membersGoodStanding+membersMember+membersLapsed))
        
    else:
        print("Skipping Retention")

    # Create csv for action network
    if flags.actionNetwork:
        print("Creating action network upload")
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
        print("Skipping Action Network")

    # TODO: Connect to google drive

if __name__ == "__main__":
    main(sys.argv)