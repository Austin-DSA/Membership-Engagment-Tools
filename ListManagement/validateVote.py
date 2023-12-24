import argparse
import Utils
import sys
import dataclasses


class Constants:
    class VOTE_COLS:
        EMAIL = "email"  # Will probably need updating
        VOTE = "vote"

    class VOTE_TYPES:
        YES = "Yes"
        NO = "No"
        ABSTAIN = "Abstain"


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
    status: str = ""
    found: bool = False

    def toRow(self):
        return [self.email, self.vote, self.status]


def main(args):
    flags = parseArgs()

    # Read in all the votes
    voteListCols, voteListRows = Utils.readCSV(flags.voteListPath)
    voteColIndexes = Utils.getIndexesForColumns(voteListCols, [Constants.VOTE_COLS.EMAIL, Constants.VOTE_COLS.VOTE])
    allVotes = [Vote(voteRow[voteColIndexes[Constants.VOTE_COLS.EMAIL]].lower().strip(), voteRow[voteColIndexes[Constants.VOTE_COLS.VOTE]]) for voteRow in voteListRows]

    # Remove earlier votes from the same person
    # Assumes things are sorted in voting list by time
    alreadyVoted = set()
    votes = []
    for v in reversed(allVotes):
        if v.email in alreadyVoted:
            print(f"{v.email} voted twice")
            continue
        alreadyVoted.add(v.email)
        votes.append(v)

    membershipListCols, membershipListRows = Utils.readCSV(flags.mebershipListPath)
    membershipListColIndexes = Utils.getIndexesForColumns(membershipListCols, [Utils.Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL])

    numYes = 0
    numNo = 0
    numAbstain = 0
    outputCols = ["Email", "Vote", "Status"]
    outputRows = []
    # It is inefficient to loop through the membership list each time for each vote
    # However it is simple and easy, and our list is about 3k members and our votes are around 100 so at this point in time simplicity wins
    for vote in votes:
        for row in membershipListRows:
            if row[membershipListColIndexes[Utils.Constants.MEMBERSHIP_LIST_COLS.EMAIL_COL]].lower().strip() != vote.email:
                continue

            vote.found = True
            vote.status = "good standing"
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
    print(f"Yes: {str(numYes)}")
    print(f"No: {str(numNo)}")
    print(f"Abstain: {str(numAbstain)}")
    print(f"Total: {str(numYes + numNo + numAbstain)}")


if __name__ == "__main__":
    main(sys.argv)
