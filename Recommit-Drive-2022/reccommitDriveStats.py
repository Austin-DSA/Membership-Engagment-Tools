import sys
import os.path
import ReccommitUtils
import datetime
class CommmandFlags:
    HELP = "-h"

    def __init__(self, membershipPath, callTrackingPath, phoneBankAttendancePath, politicalEducationAttendancePath) -> None:
        self.membershipPath = membershipPath
        self.callTrackingPath  = callTrackingPath
        self.phoneBankAttendancePath = phoneBankAttendancePath
        self.politicalEducationAttendancePath = politicalEducationAttendancePath
    
def parseArgs(args: list[str]) -> CommmandFlags:
    if CommmandFlags.HELP in args:
        print("usage: <current membership list> <call tracking list path> <phone bank attendance list> <political education attendance list>\n Will output to files(overwrite if they already exist) in reccomit/final-stats directory")
        sys.exit(0)
    if len(args) != 5:
        print("Expect exactly 4 arguments, check help -h")
    # don't exit on isFile failure as Onedrive/NetworkDrives appears to have issues with this API
    membershipPath = args[1]
    if os.path.isfile(membershipPath):
        print("Membership list path is not a file")
    callTrackingPath = args[2]
    if os.path.isfile(callTrackingPath):
        print("Call tracking path is not a file")
    phoneBankAttendancePath = args[3]
    if os.path.isfile(phoneBankAttendancePath):
        print("Phone Bank attendance path is not a file")
    politicalEducationAttendancePath = args[4]
    if os.path.isfile(politicalEducationAttendancePath):
        print("Political Education path is not a file")
    return CommmandFlags(membershipPath=membershipPath, callTrackingPath=callTrackingPath, phoneBankAttendancePath=phoneBankAttendancePath, politicalEducationAttendancePath=politicalEducationAttendancePath)

def main(args: list[str]):
    commandArgs = parseArgs(args)
    outputRows = [["Reccommit Stats Generated:", datetime.datetime.now().strftime("%Y-%m-%d")]]
    # Will use call tracking as source for email
    # We assume the called functions will lower case and strip the emails
    print("Counting Attendance")
    phoneBankAttendanceMap = ReccommitUtils.countPhoneBankAttendance(commandArgs.phoneBankAttendancePath)
    politicalEdAttendanceMap = ReccommitUtils.countPoliticalEducationAttendance(commandArgs.politicalEducationAttendancePath)
    attendeesOfBoth = set.intersection(set(phoneBankAttendanceMap.keys()), set(politicalEdAttendanceMap.keys()))
    outputRows.append([])
    outputRows.append(["Attendance Stats:"])
    outputRows.append(["Unique Political Education Attendees:",str(len(politicalEdAttendanceMap.keys()))])
    outputRows.append(["Unique Phone Bank Attendees:",str(len(phoneBankAttendanceMap.keys()))])
    outputRows.append(["Unique Attendees of Both:",str(len(attendeesOfBoth))])

    # This code could be made more generic and more concise then just using local variables and checking each case directly
    # However, we aren't expecting any other responses and this is super simple and readable and the potential genericness isn't worth the work
    print("Counting Calls")
    numCalls = 0
    numContacted = 0
    numDoNotCall = 0
    numReccommit = 0
    numNoMember = 0
    numMoved = 0
    numCallsConfirmed = 0
    numContactedConfirmed = 0
    numDoNotCallConfirmed = 0
    numReccommitConfirmed = 0
    numNoMemberConfirmed = 0
    numMovedConfirmed = 0
    trackingCols,trackingRows = ReccommitUtils.readCSV(commandArgs.callTrackingPath)
    trackingColsIndexes = ReccommitUtils.getIndexesForColumns(trackingCols)
    memberEmailsInGoodStanding = ReccommitUtils.getListOfEmailsInGoodStandingFromMembershipList(commandArgs.membershipPath)
    for row in trackingRows:
        numCalls += 1
        response = row[trackingColsIndexes[ReccommitUtils.Constants.Columns.RESPONSE]].strip().lower()
        email = row[trackingColsIndexes[ReccommitUtils.Constants.Columns.EMAIL]].strip().lower()
        if response == ReccommitUtils.Constants.Responses.CONTACTED.strip().lower():
            numContacted += 1
            if email in memberEmailsInGoodStanding:
                numCallsConfirmed += 1
                numContactedConfirmed += 1
        elif response == ReccommitUtils.Constants.Responses.DNC.strip().lower():
            numDoNotCall += 1
            if email in memberEmailsInGoodStanding:
                numCallsConfirmed += 1
                numDoNotCallConfirmed += 1
        elif response == ReccommitUtils.Constants.Responses.NO_MEMBER.strip().lower():
            numNoMember += 1
            if email in memberEmailsInGoodStanding:
                numCallsConfirmed += 1
                numNoMemberConfirmed += 1
        elif response == ReccommitUtils.Constants.Responses.MOVED.strip().lower():
            numMoved += 1
            if email in memberEmailsInGoodStanding:
                numCallsConfirmed += 1
                numMovedConfirmed += 1
        elif response == ReccommitUtils.Constants.Responses.RECOMMITTED.strip().lower():
            numReccommit += 1
            if email in memberEmailsInGoodStanding:
                numCallsConfirmed += 1
                numReccommitConfirmed += 1
    outputRows.append([])
    outputRows.append(["Response", "Number of Calls", "Number of Confirmed Reccommit", "Reccommit Percentage"])
    outputRows.append([ReccommitUtils.Constants.Responses.DNC, numDoNotCall, numDoNotCallConfirmed, numDoNotCallConfirmed/numDoNotCall])
    outputRows.append([ReccommitUtils.Constants.Responses.NO_MEMBER, numNoMember, numNoMemberConfirmed, numNoMemberConfirmed/numNoMember])
    outputRows.append([ReccommitUtils.Constants.Responses.MOVED, numMoved, numMovedConfirmed, numMovedConfirmed/numMoved])
    outputRows.append([ReccommitUtils.Constants.Responses.RECOMMITTED, numReccommit, numReccommitConfirmed, numReccommitConfirmed/numReccommit])
    outputRows.append([ReccommitUtils.Constants.Responses.CONTACTED, numContacted, numContactedConfirmed, numContactedConfirmed/numContacted])
    outputRows.append(["All Calls", numCalls, numCallsConfirmed, numCallsConfirmed/numCalls])

    ReccommitUtils.writeCSVFile(ReccommitUtils.Constants.Paths.RECOMMIT_STATS_OUTPUT, outputRows[0], outputRows[1:])


if __name__ == "__main__":
    main(sys.argv)