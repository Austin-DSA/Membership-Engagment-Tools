"""
Validates votes by comparing them with a membership list. Takes in a vote list CSV file and a membership list CSV file as input, and outputs a CSV file with the validated votes.

Usage:
    python3 validateVote.py -v <vote-list-csv> -m <membership-list-csv> -o <output-csv>

Arguments:
    -v, --vote-list: The path to the vote list CSV file.
    -m, --membership-list: The path to the membership list CSV file.
    -o, --output: The path to the output CSV file.

The script follows the following steps:

1. Read in the vote list CSV file and extract the necessary columns.
2. Create Vote objects for each vote entry in the vote list.
3. Read in the membership list CSV file.
4. Compare the votes with the membership list to validate them.
5. Remove any earlier votes from the same person.
6. Mark the status of each vote as found or not found in the membership list.
7. Write the validated votes to the output CSV file.

Note: This docstring provides an overview of the script's functionality and usage. Please refer to the code comments for more detailed explanations of each step and component.
"""


import argparse
import dataclasses
import Utils


class Constants:
    """Contains constant values used in the script."""

    class VOTE_COLS:
        """Contains constant values for the vote columns."""

        EMAIL = "email"  # Will probably need updating
        VOTE = "vote"

    class VOTE_TYPES:
        """Contains constant values for the vote types."""

        YES = "Yes"
        NO = "No"
        ABSTAIN = "Abstain"


class CommmandFlags:
    """Defines the command line flags and their corresponding long forms."""

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
        """Initializes the CommmandFlags object.
        Args:
            voteListPath (str): The path to the vote list CSV file.
            membershipListPath (str): The path to the membership list CSV file.
            outputPath (str): The path to the output CSV file.
        """
        self.voteListPath = voteListPath
        self.mebershipListPath = membershipListPath
        self.outputPath = outputPath


def parseArgs():
    """Parses command line arguments.

    Returns:
        CommmandFlags: An object containing the parsed command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(CommmandFlags.VOTE_LIST, CommmandFlags.VOTE_LIST_LONG, required=True)
    parser.add_argument(CommmandFlags.MEMBERSHIP_LIST, CommmandFlags.MEMBERSHIP_LIST_LONG, required=True)
    parser.add_argument(CommmandFlags.OUTPUT, CommmandFlags.OUTPUT_LONG, required=True)
    parsedArgs = parser.parse_args()
    return CommmandFlags(voteListPath=parsedArgs.vote_list, membershipListPath=parsedArgs.membership_list, outputPath=parsedArgs.output)


@dataclasses.dataclass
class Vote:
    """Represents a single vote entry."""

    email: str
    vote: str
    status: str = ""
    found: bool = False

    def toRow(self):
        """Converts the Vote object into a list representing a single row for a CSV file.

        Returns:
            list: A list representing a single row of a CSV file.
        """
        return [self.email, self.vote, self.status]


def main():
    """Hey, I just met you, and this is crazy, but I'm the main function, so call me maybe."""
    flags = parseArgs()

    # Read in all the votes
    voteListCols, voteListRows = Utils.readCSV(flags.voteListPath)
    voteColIndexes = Utils.getIndexesForColumns(voteListCols, [Constants.VOTE_COLS.EMAIL, Constants.VOTE_COLS.VOTE])
    allVotes = [
        Vote(voteRow[voteColIndexes[Constants.VOTE_COLS.EMAIL]].lower().strip(), voteRow[voteColIndexes[Constants.VOTE_COLS.VOTE]]) for voteRow in voteListRows
    ]

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
    main()
