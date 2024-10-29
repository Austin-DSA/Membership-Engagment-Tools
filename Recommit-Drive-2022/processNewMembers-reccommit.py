import datetime
import sys
import os
import ReccommitUtils


class Constants:
    RECOMMIT_LIST_SIZE = 500
    # Paths
    RETENTION_DATA_FILE_PATH = os.path.join(
        os.path.dirname(__file__), "adsa-retention-data.csv"
    )
    ARCHIVE_FOLDER_PATH = os.path.join(os.path.dirname(__file__), "Archive")
    OUTPUT_DIR_PATH = os.path.join(os.path.dirname(__file__), "Output")
    TODAY_STR = datetime.date.today().isoformat()
    ZIP_CODE_COL = "Zip_Code"
    RECOMMIT_DIR = os.path.join(os.path.dirname(__file__), "recommit")
    RECOMMIT_ALREADY_CALLED = os.path.join(RECOMMIT_DIR, "alreadyCalled.csv")

    # Cols from list
    MEMBERSHIP_STANDING_COL = "membership_status"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    EMAIL = "email"
    PHONE = "best_phone"

    class MEMBERSHIP_STATUS:
        LAPSED = "lapsed"
        GOOD_STANDING = "member in good standing"
        MEMBER = "member"

    COL_DO_NOT_INCLUDE = "N/A"
    COL_TO_ACTION_NETWORK = {
        "AK_ID": COL_DO_NOT_INCLUDE,
        "first_name": "first_name",
        "middle_name": COL_DO_NOT_INCLUDE,
        "last_name": "last_name",
        "suffix": COL_DO_NOT_INCLUDE,
        "Billing_Address_Line_1": COL_DO_NOT_INCLUDE,
        "Billing_Address_Line_2": COL_DO_NOT_INCLUDE,
        "Billing_City": COL_DO_NOT_INCLUDE,
        "Billing_State": COL_DO_NOT_INCLUDE,
        "Billing_Zip": COL_DO_NOT_INCLUDE,
        # TODO Combine mailing addresses
        "Mailing_Address1": "address",
        "Mailing_Address2": COL_DO_NOT_INCLUDE,
        "Mailing_City": "city",
        "Mailing_State": "state",
        "Mailing_Zip": "zip_code",
        "best_phone": "can2_phone",
        "Mobile_Phone": COL_DO_NOT_INCLUDE,
        "Home_Phone": COL_DO_NOT_INCLUDE,
        "Work_Phone": COL_DO_NOT_INCLUDE,
        "Email": "email",
        "Mail_preference": COL_DO_NOT_INCLUDE,
        "Do_Not_Call": "Do_Not_Call",
        "p2ptext_optout": "p2ptext_optout",
        "Join_Date": "Join_Date",
        "Xdate": "Xdate",
        "membership_type": COL_DO_NOT_INCLUDE,
        "monthly_dues_status": COL_DO_NOT_INCLUDE,
        "annual_recurring_dues_status": COL_DO_NOT_INCLUDE,
        "membership_status": "Membership Status",
        "memb_status_letter": "memb_status_letter",
        "union_member": "Are You a Union Member?",
        "union_name": "Union",
        "union_local": "Union Local",
        "student_yes_no": "student_yes_no",
        "student_school_name": "student_school_name",
        "YDSA Chapter": "YDSA Chapter",
        "DSA_chapter": "DSA_chapter",
        "accomodations": "accomodations",
    }
    COLS_TO_KEEP_FOR_ARCHIVE = {
        "AK_ID": False,
        "first_name": False,
        "middle_name": False,
        "last_name": False,
        "suffix": False,
        "Billing_Address_Line_1": False,
        "Billing_Address_Line_2": False,
        "Billing_City": False,
        "Billing_State": False,
        "Billing_Zip": False,
        # TODO Combine mailing addresses
        "Mailing_Address1": False,
        "Mailing_Address2": False,
        "Mailing_City": False,
        "Mailing_State": False,
        "Mailing_Zip": True,
        "best_phone": False,
        "Mobile_Phone": False,
        "Home_Phone": False,
        "Work_Phone": False,
        "Email": False,
        "Mail_preference": False,
        "Do_Not_Call": True,
        "p2ptext_optout": True,
        "Join_Date": True,
        "Xdate": True,
        "membership_type": True,
        "monthly_dues_status": True,
        "annual_recurring_dues_status": True,
        "membership_status": True,
        "memb_status_letter": True,
        "union_member": True,
        "union_name": True,
        "union_local": True,
        "student_yes_no": True,
        "student_school_name": True,
        "YDSA Chapter": True,
        "DSA_chapter": True,
        "accomodations": True,
    }


class CommmandFlags:
    DO_NOT_ARCHIVE = "-narch"
    DO_NOT_RETENTION = "-nret"
    DO_NOT_ACTION_NETWORK = "-nan"
    HELP = "-h"

    def __init__(
        self, filename, doNotArchive, doNotRetention, doNotActionNetwork
    ) -> None:
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
    return CommmandFlags(
        fileName,
        CommmandFlags.DO_NOT_ARCHIVE in args,
        CommmandFlags.DO_NOT_RETENTION in args,
        CommmandFlags.DO_NOT_ACTION_NETWORK in args,
    )


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
    cols, rows = ReccommitUtils.readCSV(inputCSV)

    # Check for new columns
    print("Checking for new columns")
    foundNewCol = False
    for c in cols:
        if c not in Constants.COL_TO_ACTION_NETWORK:
            print(c + "- Is not in the Action Network mapping")
            foundNewCol = True
        if c not in Constants.COLS_TO_KEEP_FOR_ARCHIVE:
            print(c + "- Is not in the Keep in Archive mapping")
            foundNewCol = True
    if foundNewCol:
        print("Found new column not perfoming any operations")
        return

    # Copy to archive
    if flags.archive:
        print("Archiving and obfuscating")
        archiveName = "members-" + Constants.TODAY_STR + ".csv"
        # shutil.copyfile(inputCSV, os.path.join(Constants.ARCHIVE_FOLDER_PATH, archiveName))
        # Convert file to archive obfuscate
        colIndexs = []
        newCols = []
        for index in range(len(cols)):
            if (
                cols[index] in Constants.COLS_TO_KEEP_FOR_ARCHIVE
                and Constants.COLS_TO_KEEP_FOR_ARCHIVE[cols[index]]
            ):
                colIndexs.append(index)
                newCols.append(cols[index])
        # Filter rows
        archiveRows = [[row[i].strip() for i in colIndexs] for row in rows]
        ReccommitUtils.writeCSVFile(
            os.path.join(Constants.ARCHIVE_FOLDER_PATH, archiveName),
            newCols,
            archiveRows,
        )
    # Retention
    if flags.retention:
        print("Retention")
        membersGoodStanding = 0
        membersMember = 0
        membersLapsed = 0
        standingIndex = -1
        for index in range(len(cols)):
            if cols[index].strip().lower() == Constants.MEMBERSHIP_STANDING_COL:
                standingIndex = index
                break
        if standingIndex == -1:
            print("Couldn't find membership standing column")
            return
        for row in rows:
            if len(row) != len(cols):
                print(
                    "Column Row Mismatch. Most likely a comma problem. Inspect the row in the input file and rearchive if wanted."
                )
                print([x for x in zip(cols, row)])
                return
            status = row[standingIndex].strip().lower()
            if status == Constants.MEMBERSHIP_STATUS.GOOD_STANDING:
                membersGoodStanding += 1
            elif status == Constants.MEMBERSHIP_STATUS.MEMBER:
                membersMember += 1
            elif status == Constants.MEMBERSHIP_STATUS.LAPSED:
                membersLapsed += 1
            else:
                print("Found unexpected value")
                print(status)
                return
        ReccommitUtils.appendCSVFile(
            Constants.RETENTION_DATA_FILE_PATH,
            (
                Constants.TODAY_STR,
                membersGoodStanding,
                membersMember,
                membersLapsed,
                membersGoodStanding + membersMember + membersLapsed,
            ),
        )

    else:
        print("Skipping Retention")

    # Create csv for action network
    if flags.actionNetwork:
        print("Creating action network upload")
        # Convert cols to Action network
        colIndexs = []
        newCols = []
        for index in range(len(cols)):
            if (
                cols[index] in Constants.COL_TO_ACTION_NETWORK
                and Constants.COL_TO_ACTION_NETWORK[cols[index]]
                != Constants.COL_DO_NOT_INCLUDE
            ):
                colIndexs.append(index)
                newCols.append(Constants.COL_TO_ACTION_NETWORK[cols[index]])
        # Filter rows
        actionNetworkRows = [[row[i].strip() for i in colIndexs] for row in rows]
        ReccommitUtils.writeCSVFile(
            os.path.join(
                Constants.OUTPUT_DIR_PATH,
                "action-network-" + Constants.TODAY_STR + ".csv",
            ),
            newCols,
            actionNetworkRows,
        )
    else:
        print("Skipping Action Network")

    #
    # Create the next phone bank list
    #
    # The code below is overly verbose and could be condesed/optimized. However in this case simplicity and readability are key
    print("Creating recommit list of limit " + str(Constants.RECOMMIT_LIST_SIZE))
    firstNameColIndex = -1
    lastNameColIndex = -1
    emailIndex = -1
    phoneNumberIndex = -1
    standingIndex = -1
    # Get all the columns we will need
    for index in range(len(cols)):
        if cols[index].strip().lower() == Constants.MEMBERSHIP_STANDING_COL:
            standingIndex = index
        elif cols[index].strip().lower() == Constants.FIRST_NAME:
            firstNameColIndex = index
        elif cols[index].strip().lower() == Constants.LAST_NAME:
            lastNameColIndex = index
        elif cols[index].strip().lower() == Constants.EMAIL:
            emailIndex = index
        elif cols[index].strip().lower() == Constants.PHONE:
            phoneNumberIndex = index
    if firstNameColIndex == -1:
        print("Couldn't find first name column")
        return
    if lastNameColIndex == -1:
        print("Couldn't find last name column")
        return
    if emailIndex == -1:
        print("Couldn't find email column")
        return
    if phoneNumberIndex == -1:
        print("Couldn't find phone column")
        return
    if standingIndex == -1:
        print("Couldn't find standing column")
        return

    # Read in the alreadyCaleld list and the do not call list
    alreadyCalledListCols, alreadCalledListRows = ReccommitUtils.readCSV(
        ReccommitUtils.Constants.Paths.RECOMMIT_ALREADY_CALLED_FULL
    )
    alreadyCalledListColsIndexes = ReccommitUtils.getIndexesForColumns(
        alreadyCalledListCols
    )

    doNotCallCols, doNotCallRows = ReccommitUtils.readCSV(
        ReccommitUtils.Constants.Paths.RECOMMIT_DNC
    )
    doNotCallColsIndexes = ReccommitUtils.getIndexesForColumns(doNotCallCols)

    alreadyCalledAndDNCEmailSet = set(
        [
            x[alreadyCalledListColsIndexes[ReccommitUtils.Constants.Columns.EMAIL]]
            .strip()
            .lower()
            for x in alreadCalledListRows + doNotCallCols
        ]
    )

    recommitRows = []
    recommitCols = ReccommitUtils.Constants.RECOMMIT_COLS_FOR_NEW_LIST
    colIndexes = [
        firstNameColIndex,
        lastNameColIndex,
        standingIndex,
        emailIndex,
        phoneNumberIndex,
    ]
    for row in rows:
        if len(recommitRows) >= Constants.RECOMMIT_LIST_SIZE:
            break
        if (
            row[standingIndex] == Constants.MEMBERSHIP_STATUS.MEMBER
            and row[emailIndex].strip().lower() not in alreadyCalledAndDNCEmailSet
            and row[phoneNumberIndex].strip() != ""
        ):
            recommitRows.append([row[i] for i in colIndexes])
    if len(recommitRows) < Constants.RECOMMIT_LIST_SIZE:
        for row in rows:
            if len(recommitRows) >= Constants.RECOMMIT_LIST_SIZE:
                break
            if (
                row[standingIndex] == Constants.MEMBERSHIP_STATUS.LAPSED
                and row[emailIndex].strip().lower() not in alreadyCalledAndDNCEmailSet
                and row[phoneNumberIndex].strip() != ""
            ):
                recommitRows.append([row[i] for i in colIndexes])
    ReccommitUtils.writeCSVFile(
        os.path.join(Constants.RECOMMIT_DIR, "nextBankList.csv"),
        recommitCols,
        recommitRows,
    )


if __name__ == "__main__":
    main(sys.argv)
