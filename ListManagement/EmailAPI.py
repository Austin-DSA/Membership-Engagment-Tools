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
    def __init__(self, username: str, password: str, host: str = Constants.GMAIL_HOST) -> None:
        self.mail = imaplib.IMAP4_SSL(host)
        self.mail.login(username, password)
        self.mail.select('INBOX', readonly=False)
        self.address = username
        self.password = password
        self.lastReturnedMessage = None
    
    def __del__(self):
        self.mail.logout()
        # self.smtp.quit()

    def _getMostRecentUnreadEmailFrom(self, address: str, requiresAttachment: bool, subjectContaining: str):
        # Apparently Gmail doesn't support SORT so we will collect all our emails and sort them
        resp, messages = self.mail.search(None, f'(FROM "{address}")', f'SUBJECT "{subjectContaining}"', 'UNSEEN')
        emails = []
        if resp != Constants.Responses.OK:
            raise EmailApiException("Got not OK response when looking for unread emails : "+str(resp))
        for msg in messages[0].split():
            try: 
                _, data = self.mail.fetch(msg, '(RFC822)')
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
        self.mail.store(message[0], '+FLAGS', '\\Seen')
    
    def _downloadAttachment(self, message, downloadPath, expectedFileName): 
        for part in message[1].walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            # Check the file name if we want to
            if expectedFileName is not None:
                filename = part.get_filename()
                if filename != expectedFileName:
                    raise EmailApiException(f"Unexpected filename: Got {filename} expected {expectedFileName}")
            with open(downloadPath, 'wb') as fp:
                fp.write(part.get_payload(decode=True))
    
    def markDownloadedEmailAsUnread(self):
        if self.lastReturnedMessage:
            self.mail.store(self.lastReturnedMessage, '-FLAGS', '\Seen')

    def downloadZipAttachmentFromMostRecentUnreadEmail(self, fromAddress, subjectContaining, downloadPath, afterDate = None, expectedFileName = None):
        message = self._getMostRecentUnreadEmailFrom(address=fromAddress, requiresAttachment=True, subjectContaining=subjectContaining)
        if message is None:
            raise EmailApiException.NoUnreadRecentEnough("No unread message was found")
        if afterDate is not None:
            messageDate = datetime.datetime.fromtimestamp(time.mktime(email.utils.parsedate(message[1].get(Constants.Headers.DATE))))
            if messageDate < afterDate:
                raise EmailApiException.NoUnreadRecentEnough("No unread message was found recent enough")
        self._downloadAttachment(message=message, downloadPath=downloadPath, expectedFileName=expectedFileName)
        self._markMessageAsRead(message=message)

    def sendMessage(self, toAddress, subject, messageText, attachments:list[Attachement] = []):
        message = EmailMessage()
        message.set_content(messageText)
        message['Subject'] = subject
        message['From'] = self.address
        message['To'] = toAddress
        for attachment in attachments:
            ctype, encoding = mimetypes.guess_type(attachment.path)
            if ctype is None or encoding is not None:
              # No guess could be made, or the file is encoded (compressed), so
                # use a generic bag-of-bits type.
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            with open(attachment.path, 'rb') as fp:
                message.add_attachment(fp.read(), filename=attachment.name, maintype=maintype, subtype=subtype)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(Constants.GMAIL_SMTP_HOST, Constants.GMAIL_SMTP_PORT, context=context) as server:
            server.login(self.address, self.password)
            server.send_message(message)


