import sys
import os
import ReccommitUtils

class CommmandFlags:
    HELP = "-h"

    def __init__(self, membershipPath, callTrackingPath, phoneBankAttendancePath, politicalEducationAttendancePath) -> None:
        self.membershipPath = membershipPath
        self.callTrackingPath  = callTrackingPath
        self.phoneBankAttendancePath = phoneBankAttendancePath
        self.politicalEducationAttendancePath = politicalEducationAttendancePath
    
def parseArgs(args: list[str]) -> CommmandFlags:
    if CommmandFlags.HELP in args:
        print("usage: <current membership list> <call tracking list path> <phone bank attendance list> <political education attendance list>\nWill output to files(overwrite if they already exist) in reccomit/final-stats directory")
        sys.exit(0)
    if len(args) != 5:
        print("Expect exactly 4 arguments, check help -h")
    membershipPath = args[1]
    # don't exit on isFile failure as Onedrive/NetworkDrives appears to have issues with this API
    if os.path.isfile(membershipPath):
        print("Membership list path is not a file")
        # exit(1)
    callTrackingPath = args[2]
    if os.path.isfile(callTrackingPath):
        print("Call tracking path is not a file")
        # exit(1)
    phoneBankAttendancePath = args[3]
    if os.path.isfile(phoneBankAttendancePath):
        print("Phone Bank attendance path is not a file")
        # exit(1)
    politicalEducationAttendancePath = args[4]
    if os.path.isfile(politicalEducationAttendancePath):
        print("Political Education path is not a file")
        # exit(1)
    return CommmandFlags(membershipPath=membershipPath, callTrackingPath=callTrackingPath, phoneBankAttendancePath=phoneBankAttendancePath, politicalEducationAttendancePath=politicalEducationAttendancePath)



# This function needs to return 0 for people who performed calls but have no confirmed recommitted 
# We use this list as the truth for everyone who counts as "trackable"
def calculateConfirmedRecommit(callTrackingPath, membershipPath) -> dict[str, tuple[int,int]]:
    # Read in data
    callTrackingCols,callTrackingRows = ReccommitUtils.readCSV(callTrackingPath)
    membershipCols,membershipRows = ReccommitUtils.readCSV(membershipPath)
    
    # It is assumed that this is run relatively close to when the drive has occurred. So we only need to checked the called person is in good standing
    membersInGoodStanding = set(ReccommitUtils.getListOfEmailsInGoodStanding(membershipCols, membershipRows))
    colIndexes = ReccommitUtils.getIndexesForColumns(callTrackingCols, [ReccommitUtils.Constants.CALL_TRACKING_COLS.CALLER, ReccommitUtils.Constants.CALL_TRACKING_COLS.EMAIL])
   
    outputMap: dict[str, tuple[int,int]] = {}
    for row in callTrackingRows:
        # Get info from row and the current output we have for this user
        caller = row[colIndexes[ReccommitUtils.Constants.CALL_TRACKING_COLS.CALLER]].strip().lower()
        member = row[colIndexes[ReccommitUtils.Constants.CALL_TRACKING_COLS.EMAIL]].strip().lower()
        numConfirmed = 0
        numCalled = 0
        if caller in outputMap:
            numConfirmed,numCalled = outputMap[caller]

        # Update counts in output
        numCalled += 1
        if member in membersInGoodStanding:
            numConfirmed += 1
        outputMap[caller] = (numConfirmed, numCalled)
    
    return outputMap

def main(args: list[str]):
    commandArgs = parseArgs(args)
    outputCols = ["Email", "Phone Bank Attendance", "Poltical Education Attendance", "Confirmed Recommitted", "Calls Made"]
    outputRows = []
    # Will use call tracking as source for email
    # We assume the called functions will lower case and strip the emails
    print("Counting Attendance")
    phoneBankAttendanceMap = ReccommitUtils.countPhoneBankAttendance(commandArgs.phoneBankAttendancePath)
    politicalEdAttendanceMap = ReccommitUtils.countPoliticalEducationAttendance(commandArgs.politicalEducationAttendancePath)
    callTrackingMap = calculateConfirmedRecommit(commandArgs.callTrackingPath, commandArgs.membershipPath)

    for caller, counts in callTrackingMap.items():
        outputRows.append([caller, 
                           phoneBankAttendanceMap[caller] if caller in phoneBankAttendanceMap else 0,
                           politicalEdAttendanceMap[caller] if caller in politicalEdAttendanceMap else 0,
                           counts[0], counts[1]])
    print("Writing Output")
    ReccommitUtils.writeCSVFile(ReccommitUtils.Constants.Paths.RECOMMIT_HAT_CHECK_OUTPUT, outputCols, outputRows)

if __name__ == "__main__":
    main(sys.argv)