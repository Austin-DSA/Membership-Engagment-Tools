from importlib.metadata import files
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import Utils
import logging

# https://pythonhosted.org/PyDrive/

class Constants:
    class Metadata:
        TITLE = "title"
        PARENTS = "parents"
        ID = "id"
        MIME_TYPE = "mimeType"
        MIME_TYE_CSV = "text/csv"
    
    class Paths:
        GOOGLE_AUTH_YAML = "googleAuthSettings.yaml"
        RETENTION_DATA_FILE = "adsa-retention-data.csv"
    
    class IDs:
        RETENTION_ARCHIVE_FOLDER = "1iD0WtMeP9DvBA1HULJbWPRcLWKPddve-"
        RETENTION_DATA_FILE = "1ORnCuXxm1eFXVtWfeEn9fsjY6Nd3N3Ld"

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

CLIENT_SECRET = "./client_secret.json"
TOKEN_FILE = "./token.json"

def create_authenticated_drive():
    gauth = GoogleAuth("googleAuthSettings.yaml")
    #gauth.settings['save_credentials'] = True
    gauth.LocalWebserverAuth() # client_secrets.json need to be in the same directory as the script
    drive = GoogleDrive(gauth)
    drive
    return drive

class GoogleDriveAPI:
    def __init__(self) -> None:
        self.gauth = GoogleAuth("googleAuthSettings.yaml")
        self.gauth.LocalWebserverAuth() # client_secrets.json need to be in the same directory as the script
        self.drive = GoogleDrive(self.gauth)
    
    # Will take the given rows and cols and upload it to the retention archive directory with the given name
    # This can create multiple files of the same name in the retention archive
    # However determining if we should upload based on if another file exists makes us choose which version is valid at this point
    # Is better to let anyone looking at the archive directory to figure it out themselves based on context 
    def uploadArchiveRetentionData(self, cols, rows, name="members-"+Utils.Constants.TODAY_STR+".csv") -> None:
        archiveFile = self.drive.CreateFile({Constants.Metadata.TITLE : name,
                                             Constants.Metadata.MIME_TYPE : Constants.Metadata.MIME_TYE_CSV, 
                                             Constants.Metadata.PARENTS : [{Constants.Metadata.ID: Constants.IDs.RETENTION_ARCHIVE_FOLDER}]})
        archiveFile.SetContentString(Utils.writeCSVFileToString(cols,rows))
        archiveFile.Upload()
    
    # Will take the given member counts and then upload them to the retention data file
    # Can create duplicate rows in retention file
    def uploadNewRetentionData(self, membersGoodStanding: int, membersMember: int, membersLapsed:int , date=Utils.Constants.TODAY_STR):
        retentionFile = self.drive.CreateFile({Constants.Metadata.ID : Constants.IDs.RETENTION_DATA_FILE})
        if retentionFile[Constants.Metadata.TITLE] != Constants.Paths.RETENTION_DATA_FILE:
            logging.error("Recieved unexpected file for retention "+str(retentionFile))
            return
        
        newContent = Utils.appendCSVString(retentionFile.GetContentString(), (date, membersGoodStanding, membersMember, membersLapsed, membersGoodStanding+membersMember+membersLapsed))
        retentionFile.SetContentString(newContent)
        retentionFile.Upload()
