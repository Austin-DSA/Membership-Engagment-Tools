from importlib.metadata import files
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import Utils
import logging
import os

# https://pythonhosted.org/PyDrive/
# https://medium.com/analytics-vidhya/pydrive-to-download-from-google-drive-to-a-remote-machine-14c2d086e84e


class Constants:
    class Metadata:
        TITLE = "title"
        PARENTS = "parents"
        ID = "id"
        MIME_TYPE = "mimeType"
        MIME_TYE_CSV = "text/csv"
        JSON_KEY_FILE = os.path.join(
            os.path.dirname(__file__), "googleDriveServiceAccountKey.json"
        )

    class Paths:
        GOOGLE_AUTH_YAML = "googleAuthSettings.yaml"
        RETENTION_DATA_FILE = "adsa-retention-data.csv"

    class IDs:
        RETENTION_ARCHIVE_FOLDER = "1iD0WtMeP9DvBA1HULJbWPRcLWKPddve-"
        RETENTION_DATA_FILE = "1ORnCuXxm1eFXVtWfeEn9fsjY6Nd3N3Ld"


CLIENT_SECRET = "./client_secret.json"
TOKEN_FILE = "./token.json"


class GoogleDriveAPI:
    def __init__(self) -> None:
        self.gauth = GoogleAuth()
        scope = ["https://www.googleapis.com/auth/drive"]
        self.gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            Constants.Metadata.JSON_KEY_FILE, scope
        )
        self.drive = GoogleDrive(self.gauth)

    # Will take the given rows and cols and upload it to the retention archive directory with the given name
    # This can create multiple files of the same name in the retention archive
    # However determining if we should upload based on if another file exists makes us choose which version is valid at this point
    # Is better to let anyone looking at the archive directory to figure it out themselves based on context
    def uploadArchiveRetentionData(
        self, cols, rows, name="members-" + Utils.Constants.TODAY_STR + ".csv"
    ) -> None:
        archiveFile = self.drive.CreateFile(
            {
                Constants.Metadata.TITLE: name,
                Constants.Metadata.MIME_TYPE: Constants.Metadata.MIME_TYE_CSV,
                Constants.Metadata.PARENTS: [
                    {Constants.Metadata.ID: Constants.IDs.RETENTION_ARCHIVE_FOLDER}
                ],
            }
        )
        archiveFile.SetContentString(Utils.writeCSVFileToString(cols, rows))
        archiveFile.Upload()

    # Will take the given member counts and then upload them to the retention data file
    # Can create duplicate rows in retention file
    def uploadNewRetentionData(
        self,
        membersGoodStanding: int,
        membersMember: int,
        membersLapsed: int,
        date=Utils.Constants.TODAY_STR,
    ):
        retentionFile = self.drive.CreateFile(
            {Constants.Metadata.ID: Constants.IDs.RETENTION_DATA_FILE}
        )
        if (
            retentionFile[Constants.Metadata.TITLE]
            != Constants.Paths.RETENTION_DATA_FILE
        ):
            logging.error(
                "Recieved unexpected file for retention " + str(retentionFile)
            )
            return

        newContent = Utils.appendCSVString(
            retentionFile.GetContentString(),
            (
                date,
                membersGoodStanding,
                membersMember,
                membersLapsed,
                membersGoodStanding + membersMember + membersLapsed,
            ),
        )
        retentionFile.SetContentString(newContent)
        retentionFile.Upload()
