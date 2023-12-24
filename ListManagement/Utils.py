import csv
import io
import datetime


class UtilsException(Exception):
    pass


class Constants:
    TODAY_STR = datetime.date.today().isoformat()

    # Membership Standing
    class MEMBERSHIP_LIST_COLS:
        FIRST_NAME = "first_name"
        LAST_NAME = "last_name"
        STANDING_COL = "membership_status"
        EMAIL_COL = "email"

        # One of the following two will exist
        MAILING_ADDRESS_1 = "mailing_address1"
        ADDRESS_1 = "address1"

        # One of the following two will exist
        MAILING_ADDRESS_2 = "mailing_address2"
        ADDRESS_2 = "address2"

        # One of the following two will exist
        MAILING_CITY = "mailing_city"
        CITY = "city"

        # One of the following two will exist
        MAILING_STATE = "mailing_state"
        STATE = "state"

        # One of the following two will exist
        ZIP_COL = "mailing_zip"
        ZIP_COL2 = "zip"

        BILLING_ZIP_COL = "billing_zip"
        PHONE = "best_phone"

    class MEMBERSHIP_STATUS:
        LAPSED = "lapsed"
        GOOD_STANDING = "member in good standing"
        MEMBER = "member"


def getValueWithAnyName(d, names):
    for n in names:
        if n in d:
            return d[n]
    raise IndexError(f"None of {names} found in {d}")


def readCSV(filename):
    rows = []
    cols = None
    with open(filename, "r", newline="", encoding="utf8") as file:
        reader = csv.reader(file)
        for line in reader:
            if cols is None:
                cols = line
            else:
                rows.append(line)
    return cols, rows


def writeCSVFile(filename, cols, rows):
    with open(filename, "w", newline="", encoding="utf8") as file:
        writer = csv.writer(file)
        writer.writerow(cols)
        writer.writerows(rows)


def writeCSVFileToString(cols: list[str], rows: list[list[str]]) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(cols)
    writer.writerows(rows)
    return out.getvalue()


# Think cause we are on onedrive it doesn't like appending
# So we can't do the quicker append mode, it keeps giving a "permission denied"
def appendCSVFile(filename, rowToAppend):
    rows = []
    with open(filename, "r", newline="", encoding="utf8") as file:
        reader = csv.reader(file)
        for row in reader:
            rows.append(row)
    rows.append(rowToAppend)
    with open(filename, "w", newline="", encoding="utf8") as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def appendCSVString(csvStr, rowToAppend) -> str:
    fileString = io.StringIO(initial_value=csvStr)
    fileString.seek(0, io.SEEK_END)
    writer = csv.writer(fileString)
    writer.writerow(rowToAppend)
    return fileString.getvalue()


def getIndexesForColumns(fullCols, wantedCols):
    colToIndexMap = {}
    for i in range(len(fullCols)):
        if fullCols[i] in wantedCols:
            colToIndexMap[fullCols[i]] = i
    # ensure we got all the cols we wanted
    for col in wantedCols:
        if col not in colToIndexMap:
            raise UtilsException(f"Error: Couldn't find column {str(col)} in cols {str(fullCols)}")
    return colToIndexMap


def getListOfEmailsInGoodStandingFromMembershipList(membershipListPath) -> list[str]:
    cols, rows = readCSV(membershipListPath)
    colToIndexMap = getIndexesForColumns(cols, [Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL, Constants.MEMBERSHIP_LIST_COLS.STANDING_COL])
    return getListOfEmailsInGoodStandingWithIndex(
        rows=rows, statusIndex=colToIndexMap[Constants.MEMBERSHIP_LIST_COLS.STANDING_COL], emailIndex=colToIndexMap[Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL]
    )


# This function will take a list of rows assumed to be from our membership list and return all emails for members that are in good standing
def getListOfEmailsInGoodStanding(cols: list[str], rows: list[list[str]]) -> list[str]:
    colToIndexMap = getIndexesForColumns(cols, [Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL, Constants.MEMBERSHIP_LIST_COLS.STANDING_COL])
    return getListOfEmailsInGoodStandingWithIndex(
        rows=rows, statusIndex=colToIndexMap[Constants.MEMBERSHIP_LIST_COLS.STANDING_COL], emailIndex=colToIndexMap[Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL]
    )


def getListOfEmailsInGoodStandingWithIndex(rows: list[list[str]], statusIndex: int, emailIndex: int) -> list[str]:
    emailsInGoodStanding = []
    for row in rows:
        status = row[statusIndex].strip().lower()
        if status == Constants.MEMBERSHIP_STATUS.GOOD_STANDING.lower():
            emailsInGoodStanding.append(row[emailIndex].strip().lower())
    return emailsInGoodStanding
