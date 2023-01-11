import os
import sys

class ReccommitException(Exception):
    pass

class Constants:
    # Tracking columns
    class CALL_TRACKING_COLS:
        EMAIL = "email"
        CALLER = "Caller"

    class POLI_ED_COLS:
        EMAIL = "Email"
        PREFIX = "&PE"

    class PHONE_BANK_COLS:
        EMAIL = "Email"
        PREFIX = "&PB"

    # Cols from list
    # Matches the values from the membership list we get
    class Columns:
        FIRST_NAME = "first_name"
        LAST_NAME = "last_name"
        MEMBERSHIP_STATUS = "membership_status"
        EMAIL = "email"
        RESPONSE = "Response"
        PHONE = "best_phone"
        CALLER = "Caller"
        DATE_CALLED = "Date Called"
    KNOWN_COLUMNS = set([Columns.FIRST_NAME,
                         Columns.FIRST_NAME,  
                         Columns.LAST_NAME, 
                         Columns.MEMBERSHIP_STATUS, 
                         Columns.EMAIL, 
                         Columns.RESPONSE, 
                         Columns.PHONE, 
                         Columns.CALLER, 
                         Columns.DATE_CALLED])
    
    class Paths:
        RECOMMIT_DIR = os.path.join(os.path.dirname(__file__),"recommit")
        RECOMMIT_ALREADY_CALLED = os.path.join(RECOMMIT_DIR,"alreadyCalled.csv")
        RECOMMIT_ALREADY_CALLED_FULL = os.path.join(RECOMMIT_DIR,"alreadyCalledFull.csv")
        RECOMMIT_TO_RESOLVE = os.path.join(RECOMMIT_DIR,"contactsToResolve.csv")
        RECOMMIT_DNC = os.path.join(RECOMMIT_DIR, "dnc.csv")
        RECOMMIT_FINAL_STATS = os.path.join(RECOMMIT_DIR,"final-stats")
        RECOMMIT_HAT_CHECK_OUTPUT = os.path.join(RECOMMIT_FINAL_STATS,"hatCheck.csv")
        RECOMMIT_STATS_OUTPUT = os.path.join(RECOMMIT_FINAL_STATS,"stats.csv")

    RECOMMIT_COLS_FOR_NEW_LIST = [Columns.FIRST_NAME, 
                                  Columns.LAST_NAME, 
                                  Columns.MEMBERSHIP_STATUS, 
                                  Columns.EMAIL, 
                                  Columns.PHONE, 
                                  Columns.RESPONSE, 
                                  Columns.CALLER]
    
    class Responses:
        MOVED = "Moved"
        DNC = "Do Not Call"
        WRONG_NUMBER = "Wrong Number"
        NO_MEMBER = "Does not want to be a member"
        CONTACTED = "Contacted"
        RECOMMITTED = "Recommitted"
        FULL_LIST = "Moved,Do Not Call,Wrong Number,Does not want to be a member,Contacted,Recommitted"

def getIndexesForColumns(cols):
    colToIndexMap = {}
    for i in range(len(cols)):
        if cols[i] not in Constants.KNOWN_COLUMNS and cols[i] != "":
            print("Error: When parsing columns for indexes, found unkown column: "+str(cols[i]))
            print("Exiting")
            sys.exit(1)
        colToIndexMap[cols[i]] = i
    return colToIndexMap

# These functions take in the path to the attendance sheets, and then return a dictionary from email to number of attended events
def countAttendanceFromCondensedList(rows, listPrefix, emailCol) -> dict[str, int]:
    # The condensesd attendance list is as follows
    # First we look for a row with the first item begining with the listPrefix
    # Then we have the next row act as a column row
    # We then consider consecutive rows as part of the list until we have a row of different length
    # We assume each list has consistent columns and row lengths
    # We assume each list is separated by at least one token
    # We assume the column row occurs on the row after the token
    # We assume that each list has at least 2 columns OR there is an empty row between lists
    class STATE:
        LOOKING_FOR_TOKEN = 0
        READING_COLS = 1
        READING_ROWS = 2
    rowIndex = 0
    state = STATE.LOOKING_FOR_TOKEN
    cols = []
    colsIndexes = []
    output = {}
    currentRowLength = 0
    while rowIndex < len(rows):
        match state:
            case STATE.LOOKING_FOR_TOKEN:
                row = rows[rowIndex]
                if len(row) > 0 and row[0].startswith(listPrefix):
                    state = STATE.READING_COLS
                rowIndex += 1
            
            case STATE.READING_COLS:
                cols = rows[rowIndex]
                colsIndexes = getIndexesForColumns(cols,[emailCol])
                state = STATE.READING_ROWS
                rowIndex += 1
                currentRowLength = len(cols)

            case STATE.READING_ROWS:
                row = rows[rowIndex]
                # If this row doesn't match then we are done with the list and we should skip token state
                if len(row) != currentRowLength:
                    state = STATE.LOOKING_FOR_TOKEN
                    continue
                caller = row[colsIndexes[emailCol]].strip().lower()
                if caller not in output:
                    output[caller] = 0
                output[caller] += 1
                rowIndex += 1
            
            case _:
                raise ReccommitException("Unexpected State:"+state+" when counting attendance for "+str(rows))
    return output

def countPhoneBankAttendance(phoneBankAttendancePath) -> dict[str, int]:
    cols, rows = readCSV(phoneBankAttendancePath)
    rows.insert(0,cols)
    return countAttendanceFromCondensedList(rows, Constants.PHONE_BANK_COLS.PREFIX, Constants.PHONE_BANK_COLS.EMAIL)

def countPoliticalEducationAttendance(politicalEducationAttendancePath) -> dict[str, int]:
    cols, rows = readCSV(politicalEducationAttendancePath)
    rows.insert(0,cols)
    return countAttendanceFromCondensedList(rows, Constants.POLI_ED_COLS.PREFIX, Constants.POLI_ED_COLS.EMAIL)


# Utils.py
#
# This is a copy of Utils.py when these tools were originally written
# To make dependency management easier I just copied and pasted it here so that the recommit utils can be independent
# Now this modules can stand alone without the other utils
#
#
import csv
class UtilsException(Exception):
    pass

class Constants:
     # Membership Standing
    class MEMBERSHIP_LIST_COLS:   
        STANDING_COL = "membership_status"
        EMAIL_COL = "Email"

    class MEMBERSHIP_STATUS:
        LAPSED = "lapsed"
        GOOD_STANDING = "member in good standing"
        MEMBER = "member"

def readCSV(filename):
    rows = []
    cols = None
    with open(filename, "r", newline='',encoding="utf8") as file:
        reader = csv.reader(file)
        for line in reader:
            if cols is None:
                cols = line
            else:
                rows.append(line)
    return cols,rows

def writeCSVFile(filename,cols,rows):
    with open(filename,'w',newline='', encoding="utf8") as file:
        writer = csv.writer(file)
        writer.writerow(cols)
        writer.writerows(rows)

# Think cause we are on onedrive it doesn't like appending
# So we can't do the quicker append mode, it keeps giving a "permission denied"
def appendCSVFile(filename, rowToAppend):
    rows = []
    with open(filename, "r", newline='', encoding="utf8") as file:
        reader = csv.reader(file)
        for row in reader:
            rows.append(row)
    rows.append(rowToAppend)
    with open(filename, "w", newline='', encoding="utf8") as file:
        writer = csv.writer(file)
        writer.writerows(rows)

def getIndexesForColumns(fullCols, wantedCols):
    colToIndexMap = {}
    for i in range(len(fullCols)):
        if fullCols[i] in wantedCols:
            colToIndexMap[fullCols[i]] = i
    # ensure we got all the cols we wanted
    for col in wantedCols:
        if col not in colToIndexMap:
            raise UtilsException("Error: Couldn't find column "+str(col)+" in cols "+str(fullCols))
    return colToIndexMap


def getListOfEmailsInGoodStandingFromMembershipList(membershipListPath) -> list[str]:
    cols,rows = readCSV(membershipListPath)
    colToIndexMap = getIndexesForColumns(cols, [Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL, Constants.MEMBERSHIP_LIST_COLS.STANDING_COL])
    return getListOfEmailsInGoodStandingWithIndex(rows=rows, statusIndex=colToIndexMap[Constants.MEMBERSHIP_LIST_COLS.STANDING_COL], emailIndex=colToIndexMap[Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL])

# This function will take a list of rows assumed to be from our membership list and return all emails for members that are in good standing
def getListOfEmailsInGoodStanding(cols: list[str], rows: list[list[str]]) -> list[str]:
    colToIndexMap = getIndexesForColumns(cols, [Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL, Constants.MEMBERSHIP_LIST_COLS.STANDING_COL])
    return getListOfEmailsInGoodStandingWithIndex(rows=rows, statusIndex=colToIndexMap[Constants.MEMBERSHIP_LIST_COLS.STANDING_COL], emailIndex=colToIndexMap[Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL])

def getListOfEmailsInGoodStandingWithIndex(rows: list[list[str]], statusIndex: int, emailIndex: int) -> list[str]:
    emailsInGoodStanding = []
    for row in rows:
        status = row[statusIndex].strip().lower()
        if status == Constants.MEMBERSHIP_STATUS.GOOD_STANDING.lower():
            emailsInGoodStanding.append(row[emailIndex].strip().lower())
    return emailsInGoodStanding