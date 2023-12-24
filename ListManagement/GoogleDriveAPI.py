"""
Provides a class GoogleDriveAPI for interacting with the Google Drive API to upload and manage files.

Note: This module requires the Google Drive API credentials to be set up correctly and saved in googleDriveServiceAccountKey.json.

For more information, refer to the Google Drive API documentation: [Google Drive API Documentation](https://developers.google.com/drive)
"""


from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import Utils
import logging
import os


# https://pythonhosted.org/PyDrive/
# https://medium.com/analytics-vidhya/pydrive-to-download-from-google-drive-to-a-remote-machine-14c2d086e84e


class Constants:
    """Contains constants used in the GoogleDriveAPI module."""
    class Metadata:
        """Contains constant metadata keys."""
        TITLE = "title"
        PARENTS = "parents"
        ID = "id"
        MIME_TYPE = "mimeType"
        MIME_TYE_CSV = "text/csv"
        JSON_KEY_FILE = os.path.join(os.path.dirname(__file__), "googleDriveServiceAccountKey.json")

    class Paths:
        """Contains constant file paths."""
        GOOGLE_AUTH_YAML = "googleAuthSettings.yaml"
        RETENTION_DATA_FILE = "adsa-retention-data.csv"

    class IDs:
        """Contains constant IDs."""
        RETENTION_ARCHIVE_FOLDER = "1iD0WtMeP9DvBA1HULJbWPRcLWKPddve-"
        RETENTION_DATA_FILE = "1ORnCuXxm1eFXVtWfeEn9fsjY6Nd3N3Ld"


CLIENT_SECRET = "./client_secret.json"
TOKEN_FILE = "./token.json"


class GoogleDriveAPI:
    """Provides methods to interact with the Google Drive API."""
    def __init__(self) -> None:
        """Initializes a new instance of the GoogleDriveAPI class."""
        self.gauth = GoogleAuth()
        scope = ["https://www.googleapis.com/auth/drive"]
        self.gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(Constants.Metadata.JSON_KEY_FILE, scope)
        self.drive = GoogleDrive(self.gauth)

    # Will take the given rows and cols and upload it to the retention archive directory with the given name
    # This can create multiple files of the same name in the retention archive
    # However determining if we should upload based on if another file exists makes us choose which version is valid at this point
    # Is better to let anyone looking at the archive directory to figure it out themselves based on context
    def uploadArchiveRetentionData(self, cols: list[str], rows: list[list[str]], name=f"members-{Utils.Constants.TODAY_STR}.csv") -> None:
        """
        Uploads the given rows and cols as a CSV file to the retention archive directory.

        Args:
            cols (list[str]): A list of column names.
            rows (list[list[str]]): A list of rows, where each row is a list of values.
            name (str, optional): The name of the file to be uploaded. Defaults to "members-{Utils.Constants.TODAY_STR}.csv".

        Returns:
            None
        """
        archiveFile = self.drive.CreateFile({
            Constants.Metadata.TITLE: name,
            Constants.Metadata.MIME_TYPE: Constants.Metadata.MIME_TYE_CSV,
            Constants.Metadata.PARENTS: [{Constants.Metadata.ID: Constants.IDs.RETENTION_ARCHIVE_FOLDER}],
        })
        archiveFile.SetContentString(Utils.writeCSVFileToString(cols, rows))
        archiveFile.Upload()

    # Will take the given member counts and then upload them to the retention data file
    # Can create duplicate rows in retention file
    def uploadNewRetentionData(self, membersGoodStanding: int, membersMember: int, membersLapsed: int, date=Utils.Constants.TODAY_STR):
        """
        Uploads the given member counts to the retention data file.

        Args:
            membersGoodStanding (int): The number of members in good standing.
            membersMember (int): The number of members.
            membersLapsed (int): The number of lapsed members.
            date (str, optional): The date of the retention data. Defaults to Utils.Constants.TODAY_STR.

        Returns:
            None
        """
        retentionFile = self.drive.CreateFile({Constants.Metadata.ID: Constants.IDs.RETENTION_DATA_FILE})
        if retentionFile[Constants.Metadata.TITLE] != Constants.Paths.RETENTION_DATA_FILE:
            logging.error(f"Recieved unexpected file for retention {str(retentionFile)}")
            return

        newContent = Utils.appendCSVString(
            retentionFile.GetContentString(), (date, membersGoodStanding, membersMember, membersLapsed, membersGoodStanding + membersMember + membersLapsed)
        )
        retentionFile.SetContentString(newContent)
        retentionFile.Upload()
