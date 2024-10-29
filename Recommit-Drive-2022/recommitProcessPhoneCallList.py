import sys
import ReccommitUtils
import datetime


class Constants:
    pass


class CommmandFlags:
    HELP = "-h"

    def __init__(self, filename, date) -> None:
        self.filename = filename
        self.date = date


def parseArgs(args):
    if CommmandFlags.HELP in args:
        print("usage: <inputCSV> <dateOfPhoneBank>>")
        sys.exit(0)
    if len(args) < 2:
        print("First argument is necessary and must be the file name")
    if len(args) != 3:
        print("Expect exactly two arguments, second is the date of the phone banks")
    fileName = args[1]
    try:
        date = datetime.datetime.strptime(args[2], "%m/%d/%Y").strftime("%m/%d/%Y")
    except ValueError:
        print("Error supplied date argument does not conform to MM/DD/YYYY format")
        exit(1)
    return CommmandFlags(fileName, date)


def main(args):
    commandArgs = parseArgs(args)
    # Read in list
    print(
        "This tool is meant to generate the copy paste into the shared tracking list, it will not accumulate from previous runs."
    )
    print(
        "It is expected that in the same directory as this script there is a 'recommit' directory, all output will be written there."
    )
    print(
        "Any Existing Files in the recommit files may be overwritten. Press any button to confirm. Ctrl-C or exit terminal to exit."
    )
    input("Continue?")
    callListCols, callListRows = ReccommitUtils.readCSV(commandArgs.filename)
    callListColsIndexes = ReccommitUtils.getIndexesForColumns(callListCols)

    # Prepare various outputs
    alreadyCalledCols = [
        ReccommitUtils.Constants.Columns.FIRST_NAME,
        ReccommitUtils.Constants.Columns.LAST_NAME,
        ReccommitUtils.Constants.Columns.EMAIL,
        ReccommitUtils.Constants.Columns.RESPONSE,
        ReccommitUtils.Constants.Columns.CALLER,
        ReccommitUtils.Constants.Columns.DATE_CALLED,
    ]
    alreadyCalledRows = []

    def transformRowToAlreadyCalledRow(colIndexes, row):
        newRow = [
            row[colIndexes[c]]
            for c in alreadyCalledCols
            if c != ReccommitUtils.Constants.Columns.DATE_CALLED
        ]
        newRow.append(commandArgs.date)
        return newRow

    movedCols = [
        ReccommitUtils.Constants.Columns.FIRST_NAME,
        ReccommitUtils.Constants.Columns.LAST_NAME,
        ReccommitUtils.Constants.Columns.EMAIL,
    ]
    movedRows = []

    def transformRowToMovedRow(colIndexes, row):
        return [row[colIndexes[c]] for c in movedCols]

    dncCols = [
        ReccommitUtils.Constants.Columns.FIRST_NAME,
        ReccommitUtils.Constants.Columns.LAST_NAME,
        ReccommitUtils.Constants.Columns.EMAIL,
    ]
    dncRows = []

    def transformRowToDNCRow(colIndexes, row):
        return [row[colIndexes[c]] for c in dncCols]

    wrongNumberCols = [
        ReccommitUtils.Constants.Columns.FIRST_NAME,
        ReccommitUtils.Constants.Columns.LAST_NAME,
        ReccommitUtils.Constants.Columns.EMAIL,
    ]
    wrongNumberRows = []

    def transformRowToWrongNumberRow(colIndexes, row):
        return [row[colIndexes[c]] for c in wrongNumberCols]

    needsFollowupCols = [
        ReccommitUtils.Constants.Columns.FIRST_NAME,
        ReccommitUtils.Constants.Columns.LAST_NAME,
        ReccommitUtils.Constants.Columns.EMAIL,
        ReccommitUtils.Constants.Columns.CALLER,
        ReccommitUtils.Constants.Columns.DATE_CALLED,
    ]
    needsFollowupRows = []

    def transformRowToNeedsFollowupRow(colIndexes, row):
        newRow = [
            row[colIndexes[c]]
            for c in needsFollowupCols
            if c != ReccommitUtils.Constants.Columns.DATE_CALLED
        ]
        newRow.append(commandArgs.date)
        return newRow

    doesNotWantToBeAMemberCols = [
        ReccommitUtils.Constants.Columns.FIRST_NAME,
        ReccommitUtils.Constants.Columns.LAST_NAME,
        ReccommitUtils.Constants.Columns.EMAIL,
    ]
    doesNotWantToBeAMemberRows = []

    def transformRowToDoesNotWantToBeAMemberRow(colIndexes, row):
        return [row[colIndexes[c]] for c in doesNotWantToBeAMemberCols]

    # Iteratre through rows and map responses according
    print("Categorizing List")
    for callRow in callListRows:
        response = (
            callRow[callListColsIndexes[ReccommitUtils.Constants.Columns.RESPONSE]]
            .strip()
            .lower()
        )
        if response == ReccommitUtils.Constants.Responses.MOVED.lower():
            movedRows.append(transformRowToMovedRow(callListColsIndexes, callRow))
            alreadyCalledRows.append(
                transformRowToAlreadyCalledRow(callListColsIndexes, callRow)
            )

        elif response == ReccommitUtils.Constants.Responses.DNC.lower():
            dncRows.append(transformRowToDNCRow(callListColsIndexes, callRow))
            alreadyCalledRows.append(
                transformRowToAlreadyCalledRow(callListColsIndexes, callRow)
            )

        elif response == ReccommitUtils.Constants.Responses.WRONG_NUMBER.lower():
            wrongNumberRows.append(
                transformRowToWrongNumberRow(callListColsIndexes, callRow)
            )
            alreadyCalledRows.append(
                transformRowToAlreadyCalledRow(callListColsIndexes, callRow)
            )

        elif response == ReccommitUtils.Constants.Responses.NO_MEMBER.lower():
            doesNotWantToBeAMemberRows.append(
                transformRowToDoesNotWantToBeAMemberRow(callListColsIndexes, callRow)
            )
            alreadyCalledRows.append(
                transformRowToAlreadyCalledRow(callListColsIndexes, callRow)
            )

        elif response == ReccommitUtils.Constants.Responses.CONTACTED.lower():
            alreadyCalledRows.append(
                transformRowToAlreadyCalledRow(callListColsIndexes, callRow)
            )

        elif response == ReccommitUtils.Constants.Responses.RECOMMITTED.lower():
            needsFollowupRows.append(
                transformRowToNeedsFollowupRow(callListColsIndexes, callRow)
            )
            alreadyCalledRows.append(
                transformRowToAlreadyCalledRow(callListColsIndexes, callRow)
            )

        # If we don't match any of the responses then we most likely just didn't call so we can ignore
        else:
            print("Error: Found unexpected response " + str(response))

    print("Writing Outputs")
    # Write outputs
    ReccommitUtils.writeCSVFile(
        ReccommitUtils.Constants.Paths.RECOMMIT_ALREADY_CALLED,
        alreadyCalledCols,
        alreadyCalledRows,
    )

    # For the other numbers we will consolidate into one file to make copying and pasting easier
    consolidatedCols = ["Consliated Contacts to Resolve"]
    consolidatedRows = []
    consolidatedRows.append([])
    consolidatedRows.append([])

    consolidatedRows.append(["Moved"])
    consolidatedRows.append(movedCols)
    consolidatedRows.extend(movedRows)
    consolidatedRows.append([])
    consolidatedRows.append([])

    consolidatedRows.append(["Do Not Call"])
    consolidatedRows.append(dncCols)
    consolidatedRows.extend(dncRows)
    consolidatedRows.append([])
    consolidatedRows.append([])

    consolidatedRows.append(["Wrong Number"])
    consolidatedRows.append(wrongNumberCols)
    consolidatedRows.extend(wrongNumberRows)
    consolidatedRows.append([])
    consolidatedRows.append([])

    consolidatedRows.append(["Needs Followup"])
    consolidatedRows.append(needsFollowupCols)
    consolidatedRows.extend(needsFollowupRows)
    consolidatedRows.append([])
    consolidatedRows.append([])

    consolidatedRows.append(["Does not want to be a member"])
    consolidatedRows.append(doesNotWantToBeAMemberCols)
    consolidatedRows.extend(doesNotWantToBeAMemberRows)
    consolidatedRows.append([])
    consolidatedRows.append([])

    ReccommitUtils.writeCSVFile(
        ReccommitUtils.Constants.Paths.RECOMMIT_TO_RESOLVE,
        consolidatedCols,
        consolidatedRows,
    )
    print("Done")


if __name__ == "__main__":
    main(sys.argv)
