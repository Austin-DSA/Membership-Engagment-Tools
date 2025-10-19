import argparse
import sys
import dataclasses
import datetime
import csv
import logging
import os

class Constants:
    WORKING_DIR = os.path.join(os.path.dirname(__file__), "workingDir")
    LOG_NAME = f"process_openslides_list_{datetime.datetime.strftime(datetime.datetime.now(),'%Y_%m_%d_%H_%M_%S')}.txt"
    LOG_PATH = os.path.join(WORKING_DIR,LOG_NAME)
    class OpenSlidesCols:
        TITLE = "title"
        FIRST_NAME = "first_name"
        LAST_NAME = "last_name"
        EMAIL = "email"
        PRONOUN = "pronoun"
        GENDER = "gender"
        USERNAME = "username"
        DEFAULT_PASSWORD = "default_password"
        IS_ACTIVE = "is_active"
        IS_PHYSICAL_PERSON = "is_physical_person"
        SAML_ID = "saml_id"
        IS_PRESENT = "is_present"
        STRUCTRE_LEVEL = "structure_level"
        NUMBER = "number"
        VOTE_WEIGTH = "vote_weight"
        GROUPS = "groups"
        COMMENT = "comment"
        TOP_ROW = [TITLE, FIRST_NAME,LAST_NAME,EMAIL,PRONOUN,GENDER, USERNAME, DEFAULT_PASSWORD, IS_ACTIVE, IS_PHYSICAL_PERSON,SAML_ID,IS_PRESENT,STRUCTRE_LEVEL,NUMBER,VOTE_WEIGTH,GROUPS,COMMENT]
    class ANCols:
        FIRST_NAME = "first_name"
        LAST_NAME = "last_name"
        EMAIL = "email"
        PRONOUNS = "pronouns"

class CommmandFlags:
    PREVIOUS_LIST = "-p"
    PREVIOUS_LIST_LONG = "--prev-list"
    MEMBERSHIP_LIST = "-m"
    MEMBERSHIP_LIST_LONG = "--membership-list"
    OUTPUT = "-o"
    OUTPUT_LONG = "--output"
    HELP = "-h"
    HELP_LONG = "--help"
    USAGE = "usage: python (python3 on mac) processOpenSlidesParticipants.py -p exportFromLastGBM.csv -m currentMembershipListFromActionNetwork.csv -o output-csv"

    def __init__(self, prevListPath, membershipListPath, outputPath) -> None:
        self.prevListPath = prevListPath
        self.mebershipListPath = membershipListPath
        self.outputPath = outputPath

def setup():
    if not os.path.exists(Constants.WORKING_DIR):
        os.mkdir(Constants.WORKING_DIR)
    logging.basicConfig(filename=Constants.LOG_PATH, level=logging.INFO, format="%(asctime)s : %(levelname)s : %(message)s")
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.info("Setup Complete")

def parseArgs():
    parser = argparse.ArgumentParser(description=CommmandFlags.USAGE)
    parser.add_argument(CommmandFlags.PREVIOUS_LIST, CommmandFlags.PREVIOUS_LIST_LONG, required=True)
    parser.add_argument(CommmandFlags.MEMBERSHIP_LIST, CommmandFlags.MEMBERSHIP_LIST_LONG, required=True)
    parser.add_argument(CommmandFlags.OUTPUT, CommmandFlags.OUTPUT_LONG, required=True)
    parsedArgs = parser.parse_args()
    return CommmandFlags(prevListPath=parsedArgs.prev_list, membershipListPath=parsedArgs.membership_list, outputPath=parsedArgs.output)

@dataclasses.dataclass
class OpenSlidesRow:
    firstName: str
    lastName: str
    email: str
    title: str = ""
    pronoun: str = ""
    gender: str = ""
    username: str = ""
    defaultPassword: str = ""
    isActive: int = 1
    isPhysicalPerson: int = 1
    saml_id: str = ""
    isPresent: str  = ""
    structreLevel : str = ""
    number : str = ""
    voteWeight : int = 1
    groups: str = "Delegates"
    comment: str = ""

    def toRow(self):
        return [self.title, 
                self.firstName, 
                self.lastName, 
                self.email, 
                self.pronoun, 
                self.gender, 
                self.username, 
                self.defaultPassword, 
                self.isActive, 
                self.isPhysicalPerson, 
                self.isPresent, 
                self.saml_id, 
                self.isPresent, 
                self.structreLevel, 
                self.number,
                self.voteWeight,
                self.groups,
                self.comment]

@dataclasses.dataclass
class ANReportRow:
    firstName: str
    lastName: str
    email: str
    pronoun: str = ""

    def toOpenSlidesRow(self):
        return OpenSlidesRow(firstName=self.firstName, lastName=self.lastName, email=self.email, pronoun=self.pronoun)

def readInANList(path:str ) -> list[ANReportRow]:
    result = []
    with open(file=path, newline='') as csvFile:
        reader = csv.DictReader(csvFile)
        for row in reader:
            result.append(ANReportRow(firstName=row[Constants.ANCols.FIRST_NAME], 
                                      lastName=row[Constants.ANCols.LAST_NAME], 
                                      email=row[Constants.ANCols.EMAIL],
                                      pronoun=row[Constants.ANCols.PRONOUNS]))
    return result

def readInOpenSlidesList(path:str ) -> list[OpenSlidesRow]:
    result = []
    with open(file=path, newline='') as csvFile:
        reader = csv.DictReader(csvFile)
        for row in reader:
            # We want to ignore the isActive, isPresent, isPhysicalPerson, voteWeight, number, comment, and groups columns
            result.append(OpenSlidesRow(title=row[Constants.OpenSlidesCols.TITLE],
                                        firstName=row[Constants.OpenSlidesCols.FIRST_NAME], 
                                        lastName=row[Constants.OpenSlidesCols.LAST_NAME], 
                                        email=row[Constants.OpenSlidesCols.EMAIL],
                                        pronoun=row[Constants.OpenSlidesCols.PRONOUN],
                                        gender=row[Constants.OpenSlidesCols.GENDER],
                                        username=row[Constants.OpenSlidesCols.USERNAME],
                                        defaultPassword=row[Constants.OpenSlidesCols.DEFAULT_PASSWORD],
                                        saml_id=row[Constants.OpenSlidesCols.SAML_ID],
                                        structreLevel=row[Constants.OpenSlidesCols.STRUCTRE_LEVEL]))
    return result

def main(args):
    setup()
    flags = parseArgs()
    logging.info("Reading Open Slides Previous list, %s", flags.prevListPath)
    previousList = readInOpenSlidesList(flags.prevListPath)
    logging.info("Reading in AN list, %s", flags.mebershipListPath)
    anList = readInANList(flags.mebershipListPath)

    outputList: list[OpenSlidesRow] = []

    # Loop through AN list
    # If a user with the same email exists in the previous list, add that row to the output
    # Otherwise create a new row for that user
    for anRow in anList:
        logging.info("Looking for %s", anRow.email)
        rowToAdd = None
        for oldRow in previousList:
            if anRow.email.casefold() == oldRow.email.casefold():
                rowToAdd = oldRow
                logging.info("Found info for %s", anRow.email)
                break
        if rowToAdd is None:
            logging.info("Nothing found for %s, making new row", anRow.email)
            rowToAdd = anRow.toOpenSlidesRow()
        outputList.append(rowToAdd)

    # Output the list
    logging.info("Writing Output, %s", flags.outputPath)
    with open(file=flags.outputPath, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(Constants.OpenSlidesCols.TOP_ROW)
        for row in outputList:
            writer.writerow(row.toRow())
    logging.info("Done")

if __name__ == "__main__":
    main(sys.argv)