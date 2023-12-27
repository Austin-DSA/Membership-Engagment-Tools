"""
Provides classes and exceptions for downloading zip attachments from an IMAP email account.

For more information, refer to the documentation of the individual classes and methods.
"""


import imaplib
import email
import email.utils
import datetime
from email.message import EmailMessage
import smtplib
import ssl
import mimetypes
import time
import dataclasses


class Constants:
    """Contains constants used for email communication."""

    GMAIL_HOST = "imap.gmail.com"
    GMAIL_SMTP_HOST = "smtp.gmail.com"
    GMAIL_SMTP_PORT = 465

    class Headers:
        """Contains constants used in the email headers."""

        DATE = "Date"

    class Responses:
        """Contains constants used in determining email server responses."""

        OK = "OK"


class EmailApiException(Exception):
    """Exception class for custom email API exceptions."""

    class NoUnread(Exception):
        """Exception class to be raised when no unread email is found."""

        pass

    class NoUnreadRecentEnough(Exception):
        """Exception class to be raised when no unread email is found that is more recent than the requested date."""

        pass

    class NoAttachmentMatch(Exception):
        """Exception class to be raised when the email doesn't have a attachment matching the specified criteria."""

        pass


@dataclasses.dataclass
class Attachement:
    """
    A class representing an email attachment.

    Attributes:
        path (str): The path to the attachment file.
        name (str): The name of the attachment.

    """

    path: str
    name: str


class EmailAccount:
    """
    A class representing an email account.

    Attributes:
        username (str): The username of the email account.
        password (str): The password of the email account.
        host (str): The host of the email server. Default is Constants.GMAIL_HOST.
        mail (imaplib.IMAP4_SSL): The IMAP4_SSL object for interacting with the email server.
        address (str): The email address associated with the account.
        lastReturnedMessage: The last returned message from the email server.
    """

    def __init__(self, username: str, password: str, host: str = Constants.GMAIL_HOST) -> None:
        """Configures IMAP settings and logs in to the email server.

        Args:
            username (str): The username of the email account.
            password (str): The password of the email account.
            host (str, optional): The host of the email server. Default is Constants.GMAIL_HOST.

        """
        self.mail = imaplib.IMAP4_SSL(host)
        self.mail.login(username, password)
        self.mail.select("INBOX", readonly=False)
        self.address = username
        self.password = password
        self.lastReturnedMessage = None

    def __del__(self):
        """Cleanly logs out of the email server when exiting."""
        self.mail.logout()
        # self.smtp.quit()

    def _getMostRecentUnreadEmailFrom(self, address: str, requiresAttachment: bool, subjectContaining: str):
        # Apparently Gmail doesn't support SORT so we will collect all our emails and sort them
        resp, messages = self.mail.search(None, f'(FROM "{address}")', f'SUBJECT "{subjectContaining}"', "UNSEEN")
        emails = []
        if resp != Constants.Responses.OK:
            raise EmailApiException(f"Got not OK response when looking for unread emails : {str(resp)}")
        for msg in messages[0].split():
            try:
                _, data = self.mail.fetch(msg, "(RFC822)")
            except:
                # No unread emails
                return None
            emailMsg = email.message_from_bytes(data[0][1])
            if not requiresAttachment or emailMsg.is_multipart():
                emails.append((msg, emailMsg))
        emails.sort(key=lambda msg: msg[1].get(Constants.Headers.DATE), reverse=True)
        if len(emails) > 0:
            self.lastReturnedMessage = emails[0]
            return self.lastReturnedMessage
        else:
            return None

    def _markMessageAsRead(self, message):
        """Marks a specific email as unread."""
        self.mail.store(message[0], "+FLAGS", "\\Seen")

    def _downloadAttachment(self, message, downloadPath, expectedFileName):
        """
        Download an attachment from a specific email and save it to the specified path.

        Raises:
            EmailApiException.NoAttachmentMatch: If no attachment was found that matches the specified file name.

        Returns:
            None
        """
        for part in message[1].walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get("Content-Disposition") is None:
                continue
            # Check the file name if we want to
            if expectedFileName is not None:
                filename = part.get_filename()
                if filename != expectedFileName:
                    raise EmailApiException.NoAttachmentMatch(f"Unexpected filename: Got {filename} expected {expectedFileName}")
            with open(downloadPath, "wb") as fp:
                fp.write(part.get_payload(decode=True))

    def markDownloadedEmailAsUnread(self):
        """Marks the last returned email as unread. Typically called after downloading and processing an email."""
        if self.lastReturnedMessage:
            self.mail.store(self.lastReturnedMessage[0], "-FLAGS", "\\Seen")

    def downloadZipAttachmentFromMostRecentUnreadEmail(self, fromAddress: str, subjectContaining: str, downloadPath: str, afterDate=None, expectedFileName=None):
        """
        Downloads the zip attachment from the most recent unread email that matches the specified criteria.

        Args:
            fromAddress (str): The email address from which the email should be received.
            subjectContaining (str): A string that must be found in the subject of the email.
            downloadPath (str): The path where the downloaded zip file should be saved.
            afterDate (datetime.datetime, optional): Only consider emails received after this date. Defaults to None.
            expectedFileName (str, optional): The expected name of the zip file. Defaults to None.

        Raises:
            EmailApiException.NoUnread: If no unread message is found.
            EmailApiException.NoUnreadRecentEnough: If the only unread messages found are not recent enough.

        Returns:
            None
        """
        message = self._getMostRecentUnreadEmailFrom(address=fromAddress, requiresAttachment=True, subjectContaining=subjectContaining)
        if message is None:
            raise EmailApiException.NoUnread("No unread message was found")
        if afterDate is not None:
            messageDate = datetime.datetime.fromtimestamp(time.mktime(email.utils.parsedate(message[1].get(Constants.Headers.DATE))))
            if messageDate < afterDate:
                raise EmailApiException.NoUnreadRecentEnough("No unread message was found recent enough")
        self._downloadAttachment(message=message, downloadPath=downloadPath, expectedFileName=expectedFileName)
        self._markMessageAsRead(message=message)

    def sendMessage(self, toAddress: str, subject: str, messageText: str, attachments: list[Attachement] = None):
        """
        Sends an email with the specified details.

        Args:
            toAddress (str): The email address to which the email should be sent.
            subject (str): The subject line of the email.
            messageText (str): The content of the email.
            attachments (list[Attachement], optional): List of attachments to be included in the email. Defaults to None.

        Returns:
            None
        """
        message = EmailMessage()
        message.set_content(messageText)
        message["Subject"] = subject
        message["From"] = self.address
        message["To"] = toAddress
        for attachment in attachments | []:
            ctype, encoding = mimetypes.guess_type(attachment.path)
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded (compressed), so
                # use a generic bag-of-bits type.
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            with open(attachment.path, "rb") as fp:
                message.add_attachment(fp.read(), filename=attachment.name, maintype=maintype, subtype=subtype)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(Constants.GMAIL_SMTP_HOST, Constants.GMAIL_SMTP_PORT, context=context) as server:
            server.login(self.address, self.password)
            server.send_message(message)
