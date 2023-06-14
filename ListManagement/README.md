# List Upload and Management Tools

## processNewMembers.py
To use this file to upload a membership list check these notes [https://docs.google.com/document/d/199ej3o_1ERxRm7n_4jLEKQnEFTlonfQmmzI2mdin7Wg/edit?usp=sharing]

Steps of the script can be skipped. Check the flags in `processNewMembers.CommmandFlags`.

## processNewMembersAutomated.py
This will do everything `processNewMembers.py` does and also perform the uploads to Action Network and Google Drive.

A few additional steps are needed for initial setup.
1. You will need to add an Action Network API key into `actionNetworkAPIKey.txt`. A key can be found in Action Network, Details -> API & Sync.
3. You will need to make a `client_secrets.json` in the same folder as the scripts. Details for that can be found here [https://pythonhosted.org/PyDrive/quickstart.html#authentication].
2. Upon running you will need to OAuth into google. The script should automatically prompt for your credentials. This allows the script to upload to Google Drive. The account you sign in with will need to have access to the Membership Engagement folder.

### ActionNetworkAPI.py
An encapsulation of the AN API as `ActionNetworkAPI.ActionNetworkAPI()`. It requires the API key file upon construction and then you can post people to Action network.

### GoogleDriveAPI.py
An encapsulation of the Google Drive API as `GoogleDriveAPI.GoogleDriveAPI()`. Requires the client secrets file to exist in the same directory.

### validateVote.py
Can validate a vote table based off a given membership list. May require changes for each individual vote list as there is not currently a standard format.

### Utils.py
Various utils used by all other files.