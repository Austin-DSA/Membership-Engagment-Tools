import argparse
import Utils
import sys
import dataclasses
import datetime

class Constants:
    class VOTE_COLS:
        EMAIL = "email" # Will probably need updating
        VOTE = "vote"
        NAME = "name"
    class VOTE_TYPES:
        YES = "yes"
        NO = "no"
        ABSTAIN = "abstain"

class CommmandFlags:
    VOTE_LIST = "-v"
    VOTE_LIST_LONG = "--vote-list"
    MEMBERSHIP_LIST = "-m"
    MEMBERSHIP_LIST_LONG = "--membership-list"
    OUTPUT = "-o"
    OUTPUT_LONG = "--output"
    HELP = "-h"
    HELP_LONG = "--help"
    USAGE = "usage: python3 proc -v vote-list-csv -m membership-list-csv -o output-csv"

    def __init__(self, voteListPath, membershipListPath, outputPath) -> None:
        self.voteListPath = voteListPath
        self.mebershipListPath = membershipListPath
        self.outputPath = outputPath
    
def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument(CommmandFlags.VOTE_LIST, CommmandFlags.VOTE_LIST_LONG, required=True)
    parser.add_argument(CommmandFlags.MEMBERSHIP_LIST, CommmandFlags.MEMBERSHIP_LIST_LONG, required=True)
    parser.add_argument(CommmandFlags.OUTPUT, CommmandFlags.OUTPUT_LONG, required=True)
    parsedArgs = parser.parse_args()
    return CommmandFlags(voteListPath=parsedArgs.vote_list, membershipListPath=parsedArgs.membership_list, outputPath=parsedArgs.output)

@dataclasses.dataclass
class Vote:
    email: str
    vote: str
    name: str
    status: str = ""
    found: bool = False

    def toRow(self):
        return [self.name, self.email, self.vote, self.status]

def main(args):
    flags = parseArgs()

    # Read in all the votes
    voteListCols, voteListRows = Utils.readCSV(flags.voteListPath)
    voteColIndexes = Utils.getIndexesForColumns(voteListCols, [Constants.VOTE_COLS.EMAIL, Constants.VOTE_COLS.VOTE, Constants.VOTE_COLS.NAME])
    allVotes = [Vote(email=voteRow[voteColIndexes[Constants.VOTE_COLS.EMAIL]].lower().strip(), 
                     vote=voteRow[voteColIndexes[Constants.VOTE_COLS.VOTE]].lower().strip(), 
                     name=voteRow[voteColIndexes[Constants.VOTE_COLS.NAME]].lower().strip()) for voteRow in voteListRows]

    # Remove earlier votes from the same person
    # Assumes things are sorted in voting list by time
    print("Grabbing most recent votes")
    alreadyVoted = set()
    votes = []
    for v in reversed(allVotes):
        if v.email in alreadyVoted:
            print(f"{v.email} voted twice")
            continue
        alreadyVoted.add(v.email)
        votes.append(v)
    
    membershipListCols, membershipListRows = Utils.readCSV(flags.mebershipListPath)
    membershipListColIndexes = Utils.getIndexesForColumns(membershipListCols, [Utils.Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL, 
                                                                               Utils.Constants.MEMBERSHIP_LIST_COLS.FIRST_NAME,
                                                                               Utils.Constants.MEMBERSHIP_LIST_COLS.MIDDLE_NAME,
                                                                               Utils.Constants.MEMBERSHIP_LIST_COLS.LAST_NAME,
                                                                               Utils.Constants.MEMBERSHIP_LIST_COLS.ADDRESS_1,
                                                                               Utils.Constants.MEMBERSHIP_LIST_COLS.ADDRESS_2,
                                                                               Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL2,
                                                                               Utils.Constants.MEMBERSHIP_LIST_COLS.JOIN_DATE,
                                                                               Utils.Constants.MEMBERSHIP_LIST_COLS.STANDING_COL])

    # Check for membership collisions
    print("Checking for collisions in membership ")
    for v1 in votes:
        for v2 in votes:
            if v1.email == v2.email:
                continue
            v1Member = None
            v2Member = None
            for row in membershipListRows:
                if row[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL]].lower().strip() == v1.email:
                    v1Member = row
                if row[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL]].lower().strip() == v2.email:
                    v2Member = row
                if v1Member is not None and v2Member is not None:
                    break
            if v1Member is None or v2Member is None:
                continue
            # Check First-Middle-Last Name
            # Check address1-address2-zip
            # Check if join_date is on the same day
            v1MemberName = f"{v1Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.FIRST_NAME]].lower().strip()}-{v1Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.MIDDLE_NAME]].lower().strip()}-{v1Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.LAST_NAME]].lower().strip()}"
            v2MemberName = f"{v2Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.FIRST_NAME]].lower().strip()}-{v2Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.MIDDLE_NAME]].lower().strip()}-{v2Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.LAST_NAME]].lower().strip()}"
            v1MemberAddress = f"{v1Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.ADDRESS_1]].lower().strip()}-{v1Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.ADDRESS_2]].lower().strip()}-{v1Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL2]].lower().strip()}"
            v2MemberAddress = f"{v2Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.ADDRESS_1]].lower().strip()}-{v2Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.ADDRESS_2]].lower().strip()}-{v2Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.ZIP_COL2]].lower().strip()}"
            # v1MemberJoinDate = datetime.datetime.strptime(v1Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.JOIN_DATE]].lower().strip(), "%Y-%m-%d")
            # v2MemberJoinDate = datetime.datetime.strptime(v2Member[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.JOIN_DATE]].lower().strip(), "%Y-%m-%d")
            # if v1MemberName == v2MemberName:
            #     print(f"Collision: Votes for {v1.email} and {v2.email} have same name {v1MemberName}")
            # if v1MemberAddress == v2MemberAddress:
            #     print(f"Collision: Votes for {v1.email} and {v2.email} have same address {v1MemberAddress}")
            # if (v1MemberJoinDate < v2MemberJoinDate and v2MemberJoinDate < v1MemberJoinDate+datetime.timedelta(weeks=1)) or ((v2MemberJoinDate < v1MemberJoinDate and v1MemberJoinDate < v2MemberJoinDate+datetime.timedelta(weeks=1))):
            #     v1DateStr = v1MemberJoinDate.strftime("%Y-%m-%d")
            #     v2DateStr = v2MemberJoinDate.strftime("%Y-%m-%d")
            #     print(f"Collision: Votes for {v1.email} and {v2.email} joined within the same week {v1DateStr} {v2DateStr}")

    numYes = 0
    numNo = 0
    numAbstain = 0
    outputCols = ["Name", "Email", "Vote", "Status"]
    outputRows = []
    # It is inefficient to loop through the membership list each time for each vote
    # However it is simple and easy, and our list is about 3k members and our votes are around 100 so at this point in time simplicity wins
    for vote in votes:
        for row in membershipListRows:
            if row[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL]].lower().strip() != vote.email:
                continue

            
            vote.found = True
            vote.status = row[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.STANDING_COL]]
            print(f"Found member for email {vote.email} - {vote.vote} - {vote.status}")
            if vote.status == Utils.Constants.MEMBERSHIP_STATUS.LAPSED:
                break
            if vote.vote == Constants.VOTE_TYPES.YES:
                numYes += 1
            if vote.vote == Constants.VOTE_TYPES.NO:
                numNo += 1
            if vote.vote == Constants.VOTE_TYPES.ABSTAIN:
                numAbstain += 1
        if not vote.found:
            vote.status = "Not in list"
        outputRows.append(vote.toRow())
    
    Utils.writeCSVFile(flags.outputPath, outputCols, outputRows)
    print("Yes: "+str(numYes))
    print("No: "+str(numNo))
    print("Abstain: "+str(numAbstain))
    print("Total: "+str(numYes+numNo+numAbstain))

    



if __name__ == "__main__":
    main(sys.argv)