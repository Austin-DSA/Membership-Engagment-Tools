# List Upload and Management Tools

## Description

This script is designed to automate the processing of membership lists from the Democratic Socialists of America (DSA) for the Austin DSA chapter.
Features include:
- Downloading membership lists from emails,
- Archiving lists for retention tracking with obfuscation of sensitive data,
- Processing retention data,
- Uploading data to Google Drive and/or Action Network,
- Logging activities and notifying users by email upon completion or failure.

## Prerequisites

- Python 3.x installed
- Additional Python packages: `argparse`, `datetime`, `logging`, `os`, `sys`, `typing`, `zipfile`
- Custom Python modules: `Utils`, `ActionNetworkAPI`, `GoogleDriveAPI`, `EmailAPI`
- Credentials and API keys configured as required by the script (refer to `Constants` class within the script for configuration files and paths)
  1. You will need to add an Action Network API key into `actionNetworkAPIKey.txt`. A key can be found in Action Network, Details -> API & Sync.
  3. You will need to make a `client_secrets.json` in the same folder as the scripts. Details for that can be found here [https://pythonhosted.org/PyDrive/quickstart.html#authentication].
  2. Upon running you will need to OAuth into google. The script should automatically prompt for your credentials. This allows the script to upload to Google Drive. The account you sign in with will need to have access to the Membership Engagement folder.

## Usage

Run the script with Python, optionally providing arguments to customize behavior:

```bash
python3 -m membership_list_processor [arguments]
```

### Available Arguments
- `filename`: Specify the file name of the membership list. Use "EMAIL" to download the list from an email account.
- `--automate`: Automate both Action Network and Google Drive upload processes. If false, it will use a local file for retention data.
- `--auto_an`: Automate uploading to Action Network.
- `--auto_gd`: Automate uploading retention data to Austin DSA Google Drive (and will download retention data from Google Drive). Overrides --local-retention.
- `--narch`: Skip the archiving step.
- `--nret`: Skip the retention step.
- `--nan`: Skip the Action Network steps.
- `--local_retention`: Use local retention file instead of downloading (if automating).
- `--background`: Use background processing when uploading to Action Network.

### Example

```bash
python3 -m membership_list_processor filename=path/to/membership_list.csv --automate
```

This will run the processor using the specified membership list CSV file, upload the membership data to Action Network, and handle Google Drive uploads for retention data.

## Logging and Exceptions

The script logs all its activities to a file that is named with the current timestamp and stored in the `workingDir` directory specified in the `Constants` class. Ensure this directory exists or is created by the script.

The script contains a custom exception (`MembershipListProcessingException`) which will be raised in case of processing errors without halting the code.

Upon finishing the tasks or encountering errors, the script attempts to send email notifications. Verify that the SMTP credentials and endpoints are correctly configured within the `Constants` and that the script is permitted to access your email server.To use this file to upload a membership list check these notes [https://docs.google.com/document/d/199ej3o_1ERxRm7n_4jLEKQnEFTlonfQmmzI2mdin7Wg/edit?usp=sharing]

### ActionNetworkAPI.py
An encapsulation of the AN API as `ActionNetworkAPI.ActionNetworkAPI()`. It requires the API key file upon construction and then you can post people to Action network.

### GoogleDriveAPI.py
An encapsulation of the Google Drive API as `GoogleDriveAPI.GoogleDriveAPI()`. Requires the client secrets file to exist in the same directory.

### validateVote.py
Can validate a vote table based off a given membership list. May require changes for each individual vote list as there is not currently a standard format.

### Utils.py
Various utils used by all other files.
