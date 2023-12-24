"""
Provides functions to retrieve information from membership list data.

For more information on the specific functions, please refer to their respective docstrings.
"""


import csv
import io
import datetime


class UtilsException(Exception):
    """Custom exception class used in utility functions."""
    pass


class Constants:
    """Contains constant values used throughout the module."""
    TODAY_STR = datetime.date.today().isoformat()

    # Membership Standing
    class MEMBERSHIP_LIST_COLS:
        """Contains constants of the column names used in the membership list."""
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
        """Contains constants of the valid possible membership statuses."""
        LAPSED = "lapsed"
        GOOD_STANDING = "member in good standing"
        MEMBER = "member"


def getValueWithAnyName(d: dict, names: list):
    """Get the value from a dictionary using any of the given names.

    Args:
        d (dict): The dictionary to search for values.
        names (list): List of names to search for in the dictionary.

    Returns:
        The value from the dictionary corresponding to the first name found.

    Raises:
        IndexError: If none of the names are found in the dictionary.
    """
    for n in names:
        if n in d:
            return d[n]
    raise IndexError(f"None of {names} found in {d}")


def readCSV(filename: str) -> (list, list):
    """Read a CSV file and return its contents as columns and rows.

    Args:
        filename (str): The path to the CSV file.

    Returns:
        tuple: A tuple containing the column names and the rows of data from the CSV file.
    """
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


def writeCSVFile(filename: str, cols: list[str], rows: list[list[str]]):
    """Write data to a CSV file.

    Args:
        filename (str): The path to the CSV file.
        cols (list[str]): The column names.
        rows (list[list[str]]): The rows of data.
    Returns:
        None
    """
    with open(filename, "w", newline="", encoding="utf8") as file:
        writer = csv.writer(file)
        writer.writerow(cols)
        writer.writerows(rows)


def writeCSVFileToString(cols: list[str], rows: list[list[str]]) -> str:
    """Write data to a CSV file and return it as a string.

    Args:
        cols (list[str]): The column names.
        rows (list[list[str]]): The rows of data.

    Returns:
        str: The CSV data as a string.
    """
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(cols)
    writer.writerows(rows)
    return out.getvalue()


# Think cause we are on onedrive it doesn't like appending
# So we can't do the quicker append mode, it keeps giving a "permission denied"
def appendCSVFile(filename: str, rowToAppend: list[str]):
    """Append a row of data to an existing CSV file.

    Args:
        filename (str): The path to the CSV file.
        rowToAppend (list[str]): The row of data to append.

    Returns:
        None
    """
    rows = []
    with open(filename, "r", newline="", encoding="utf8") as file:
        reader = csv.reader(file)
        for row in reader:
            rows.append(row)
    rows.append(rowToAppend)
    with open(filename, "w", newline="", encoding="utf8") as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def appendCSVString(csvStr: str, rowToAppend: list[str]) -> str:
    """Append a row of data to an existing CSV string.

    Args:
        csvStr (str): The CSV data as a string.
        rowToAppend (list[str]): The row of data to append.

    Returns:
        str: The updated CSV data as a string.
    """
    fileString = io.StringIO(initial_value=csvStr)
    fileString.seek(0, io.SEEK_END)
    writer = csv.writer(fileString)
    writer.writerow(rowToAppend)
    return fileString.getvalue()


def getIndexesForColumns(fullCols: list[str], wantedCols: list[str]) -> dict[str, int]:
    """Get the indexes of the desired columns in a list of column names.

    Args:
        fullCols (list[str]): The full list of column names.
        wantedCols (list[str]): The desired column names.

    Returns:
        dict[str, int]: A dictionary mapping the desired column names to their indexes.

    Raises:
        UtilsException: If any of the desired column names are not found in the full list of column names.
    """
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
    """
    Retrieves a list of emails for members in good standing from a membership list file.

    Args:
        membershipListPath (str): path to the membership list file.

    Returns:
        list[str]: A list of emails for members in good standing.
    """
    cols, rows = readCSV(membershipListPath)
    colToIndexMap = getIndexesForColumns(cols, [Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL, Constants.MEMBERSHIP_LIST_COLS.STANDING_COL])
    return getListOfEmailsInGoodStandingWithIndex(
        rows=rows, statusIndex=colToIndexMap[Constants.MEMBERSHIP_LIST_COLS.STANDING_COL], emailIndex=colToIndexMap[Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL]
    )


# This function will take a list of rows assumed to be from our membership list and return all emails for members that are in good standing
def getListOfEmailsInGoodStanding(cols: list[str], rows: list[list[str]]) -> list[str]:
    """
    Retrieves a list of emails for members in good standing from a given list of columns and rows.

    Args:
        cols (list[str]): column names.
        rows (list[list[str]]): row data.

    Returns:
        list[str]: list containing the emails of all members in good standing.
    """
    colToIndexMap = getIndexesForColumns(cols, [Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL, Constants.MEMBERSHIP_LIST_COLS.STANDING_COL])
    return getListOfEmailsInGoodStandingWithIndex(
        rows=rows, statusIndex=colToIndexMap[Constants.MEMBERSHIP_LIST_COLS.STANDING_COL], emailIndex=colToIndexMap[Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL]
    )


def getListOfEmailsInGoodStandingWithIndex(rows: list[list[str]], statusIndex: int, emailIndex: int) -> list[str]:
    """
    Retrieves a list of emails for members in good standing from a given list of rows using specified column indexes

    Args:
        rows (list[list[str]]): row data.
        statusIndex (int): index of column containing membership status.
        emailIndex (int): index of column containing email.

    Returns:
        list[str]: list containing the emails of all members in good standing.
    """
    emailsInGoodStanding = []
    for row in rows:
        status = row[statusIndex].strip().lower()
        if status == Constants.MEMBERSHIP_STATUS.GOOD_STANDING.lower():
            emailsInGoodStanding.append(row[emailIndex].strip().lower())
    return emailsInGoodStanding
