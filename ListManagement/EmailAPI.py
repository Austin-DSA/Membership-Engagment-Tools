import imaplib
import email
import email.utils
import datetime
from email.message import EmailMessage
from email.utils import parseaddr
from email import policy
from email.utils import parsedate_to_datetime
import smtplib
import ssl
import mimetypes
import time
import dataclasses
import os


class Constants:
    GMAIL_HOST = "imap.gmail.com"
    GMAIL_SMTP_HOST = "smtp.gmail.com"
    GMAIL_SMTP_PORT = 465

    class Headers:
        DATE = "Date"

    class Responses:
        OK = "OK"


class EmailApiException(Exception):
    class NoUnreadRecentEnough(Exception):
        pass


@dataclasses.dataclass
class Attachement:
    path: str
    name: str


class EmailAccount:
    def __init__(
        self, username: str, password: str, host: str = Constants.GMAIL_HOST
    ) -> None:
        self.mail = imaplib.IMAP4_SSL(host)
        self.mail.login(username, password)
        self.mail.select("INBOX", readonly=False)
        self.address = username
        self.password = password
        self.lastReturnedMessage = None

    def __del__(self):
        self.mail.logout()
        # self.smtp.quit()

    def _getMostRecentUnreadEmailFrom(
        self, address: str, requiresAttachment: bool, subjectContaining: str
    ):
        """
        Returns the most recent unread email object.

        Parameters:
            address (str): search most recent email FROM this address
            subjectContaining (str): email must have this attachment
            requiresAttachment (bool): does email require hav attachment

        Returns:
            obj: custom email object type
            None if no email matches
        """
        max_email_num = 1

        status, search_data = self.mail.search(
            None, f'(FROM "{address}")', f'SUBJECT "{subjectContaining}"', "ALL"
        )
        mail_ids = search_data[0].split()
        message_id = mail_ids[-max_email_num:][::-1]
        status, message = self.mail.fetch(message_id[0], "(FLAGS RFC822)")
        self.lastReturnedMessage = message_id[0]
        flags = message[0][0].decode()
        is_unread = "UNSEEN" in flags or "\\Seen" not in flags

        if is_unread:
            raw_email = message[0][1]
            email_content = email.message_from_bytes(raw_email)
            message_subject = email_content["Subject"]

            email_attachments = email.message_from_bytes(
                raw_email, policy=policy.default
            )
            has_attachment = False

            # Now you can just do:
            for attachment in email_attachments.iter_attachments():
                filename = attachment.get_filename()
                has_attachment = True

            if email_content["Subject"] == subjectContaining and has_attachment:
                return raw_email

        else:
            return None

            # Parse the raw bytes into an Email object

            # Use email.utils to handle the "From" header cleanly
            name, addr = parseaddr(msg["From"])

            print(f"Subject: {msg['Subject']}")
            print(f"date:  {msg['Date']}")
            date_string = msg["Date"]
            dt = parsedate_to_datetime(date_string)
            formatted_date = dt.strftime("%Y-%m-%d")

            print(f"message id: {msg['Message-ID'].strip()}")
            new_id = msg["Message-ID"].strip()
            new_id = new_id.split("<")[1].split("@")[0]
            print(f"new id: {new_id}")
            print(f"From: {name} <{addr}>")
            print(f"content type: {msg.get_content_type()}")
            print(f"charset: {msg.get_content_charset()}")
            has_attachment = False
            # for part in msg.walk():
            #     # If the part has a filename, it's an attachment
            #     if part.get_filename():
            #         has_attachment = True
            #         print(f"Found attachment: {part.get_filename()}")
            msg = email.message_from_bytes(raw_email, policy=policy.default)

        # # Apparently Gmail doesn't support SORT so we will collect all our emails and sort them
        # resp, messages = self.mail.search(
        #     None, f'(FROM "{address}")', f'SUBJECT "{subjectContaining}"', "UNSEEN"
        # )
        # emails = []
        # if resp != Constants.Responses.OK:
        #     raise EmailApiException(
        #         "Got not OK response when looking for unread emails : " + str(resp)
        #     )
        # for msg in messages[0].split():
        #     try:
        #         _, data = self.mail.fetch(msg, "(RFC822)")
        #     except:
        #         # No unread emails
        #         return None
        #     emailMsg = email.message_from_bytes(data[0][1])
        #     if not requiresAttachment or emailMsg.is_multipart():
        #         emails.append((msg, emailMsg))
        # emails.sort(key=lambda msg: msg[1].get(Constants.Headers.DATE), reverse=True)
        # if len(emails) > 0:
        #     self.lastReturnedMessage = emails[0]
        #     return self.lastReturnedMessage
        # else:
        #     return None

    def get_emails(self):

        max_email_num = 10
        status, search_data = self.mail.search(None, "ALL")
        mail_ids = search_data[0].split()
        latest_100_ids = mail_ids[-max_email_num:][::-1]

        for m_id in latest_100_ids:
            # Fetch the email data by ID
            status, data = self.mail.fetch(m_id, "(FLAGS RFC822)")
            flags = data[0][0].decode()
            is_unread = "UNSEEN" in flags or "\\Seen" not in flags
            print(f"Is Unread: {is_unread}")

            # Parse the raw bytes into an Email object
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Use email.utils to handle the "From" header cleanly
            name, addr = parseaddr(msg["From"])

            print(f"Subject: {msg['Subject']}")
            print(f"date:  {msg['Date']}")
            date_string = msg["Date"]
            dt = parsedate_to_datetime(date_string)
            formatted_date = dt.strftime("%Y-%m-%d")

            print(f"message id: {msg['Message-ID'].strip()}")
            new_id = msg["Message-ID"].strip()
            new_id = new_id.split("<")[1].split("@")[0]
            print(f"new id: {new_id}")
            print(f"From: {name} <{addr}>")
            print(f"content type: {msg.get_content_type()}")
            print(f"charset: {msg.get_content_charset()}")
            has_attachment = False
            # for part in msg.walk():
            #     # If the part has a filename, it's an attachment
            #     if part.get_filename():
            #         has_attachment = True
            #         print(f"Found attachment: {part.get_filename()}")
            msg = email.message_from_bytes(raw_email, policy=policy.default)

            # Now you can just do:
            for attachment in msg.iter_attachments():
                filename = attachment.get_filename()

                if filename:
                    # 3. Get the content (policy=default handles decoding automatically)
                    content = attachment.get_content()

                    # amend filename
                    filename = f"{formatted_date}_{filename}"
                    # 4. Save the file
                    # Note: attachment.get_content() returns bytes for binary files (PDF, JPG)
                    # and strings for text files. 'wb' handles both safely.
                    with open(filename, "wb") as f:
                        if isinstance(content, str):
                            f.write(
                                content.encode(
                                    attachment.get_content_charset() or "utf-8"
                                )
                            )
                        else:
                            f.write(content)

                    print(f"Successfully downloaded: {filename}")
                    print(attachment.get_filename())

            print("-" * 30)

    def _markMessageAsRead(self):
        self.mail.store(self.lastReturnedMessage, "+FLAGS", "\\Seen")

    def _downloadAttachment(self, message, downloadPath, expectedFileName):
        msg = email.message_from_bytes(message, policy=policy.default)

        # Now you can just do:
        for attachment in msg.iter_attachments():
            filename = attachment.get_filename()

            if expectedFileName is not None:
                if filename != expectedFileName:
                    raise EmailApiException(
                        f"Unexpected filename: Got {filename} expected {expectedFileName}"
                    )

            if filename:
                # 3. Get the content (policy=default handles decoding automatically)
                content = attachment.get_content()

                # 4. Save the file
                # Note: attachment.get_content() returns bytes for binary files (PDF, JPG)
                # and strings for text files. 'wb' handles both safely.
                with open(downloadPath, "wb") as f:
                    if isinstance(content, str):
                        f.write(
                            content.encode(attachment.get_content_charset() or "utf-8")
                        )
                    else:
                        f.write(content)

                print(f"Successfully downloaded: {filename}")
                print(attachment.get_filename())

    def markDownloadedEmailAsUnread(self):
        self.mail.store(self.lastReturnedMessage, "-FLAGS", "\\Seen")

    def downloadZipAttachmentFromMostRecentUnreadEmail(
        self,
        fromAddress,
        subjectContaining,
        downloadPath,
        afterDate=None,
        expectedFileName=None,
    ):
        message = self._getMostRecentUnreadEmailFrom(
            address=fromAddress,
            requiresAttachment=True,
            subjectContaining=subjectContaining,
        )
        if message is None:
            raise EmailApiException.NoUnreadRecentEnough("No unread message was found")
        if afterDate is not None:
            email_data = email.message_from_bytes(message)
            date_string = email_data["Date"]
            email_date = parsedate_to_datetime(date_string)

            if email_date < afterDate:
                raise EmailApiException.NoUnreadRecentEnough(
                    "No unread message was found recent enough"
                )
            else:
                self._downloadAttachment(
                    message=message,
                    downloadPath=downloadPath,
                    expectedFileName=expectedFileName,
                )
                self._markMessageAsRead()

    def sendMessage(
        self, toAddress, subject, messageText, attachments: list[Attachement] = []
    ):
        message = EmailMessage()
        message.set_content(messageText)
        message["Subject"] = subject
        message["From"] = self.address
        message["To"] = toAddress
        for attachment in attachments:
            ctype, encoding = mimetypes.guess_type(attachment.path)
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded (compressed), so
                # use a generic bag-of-bits type.
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            with open(attachment.path, "rb") as fp:
                message.add_attachment(
                    fp.read(),
                    filename=attachment.name,
                    maintype=maintype,
                    subtype=subtype,
                )
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            Constants.GMAIL_SMTP_HOST, Constants.GMAIL_SMTP_PORT, context=context
        ) as server:
            server.login(self.address, self.password)
            server.send_message(message)
