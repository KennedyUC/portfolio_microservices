import io
import email
import imaplib
import hashlib
import mimetypes
from email.header import decode_header
from datetime import datetime, timezone
from field_agent_app.core.logging import logger
from field_agent_app.core.config import settings
from field_agent_app.services.storage import storage_processor
from field_agent_app.models.main import ProcessorFolders
from field_agent_app.db.repositories import PolicyRecordRepository

class EmailService():
    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password

    async def hash_exists(self, file_hash: str, record_repo: PolicyRecordRepository) -> bool:
        hash_record = await record_repo.get_hash_record(file_hash=file_hash)

        if hash_record:
            return True
        return False

    def connect(self):
        imap_url = 'imap.gmail.com'
        try:
            logger.info("Logging into Email ...")
            mail = imaplib.IMAP4_SSL(imap_url)
            mail.login(self.user, self.password)
            logger.info("Email Login Successful!")
            mail.select('inbox')
            self.email = mail
        except Exception as e:
            logger.error("Connection failed: {}".format(e))
            raise

    def fetch_emails(self, subject_keyword="Conversation History"):
        today = datetime.today().strftime("%d-%b-%Y")
        logger.info(f"Searching for unread emails since {today}...")

        typ, data = self.email.search(None, f'(UNSEEN SINCE {today})')
        if typ != 'OK':
            logger.error("Failed to search mailbox.")
            return []

        email_ids = data[0].split()
        matching_emails = []

        for eid in reversed(email_ids):
            typ, msg_data = self.email.fetch(eid, '(RFC822)')
            if typ != 'OK':
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or 'utf-8')

            if subject_keyword.lower() in subject.lower():
                matching_emails.append(msg)

        logger.info(f"Found {len(matching_emails)} matching unread emails.")

        return matching_emails
    
    def extract_attachments(self, msg):
        attachments = []

        for part in msg.walk():
            content_disposition = part.get("Content-Disposition", "")
            if part.get_content_maintype() == 'multipart' or 'attachment' not in content_disposition:
                continue

            filename = part.get_filename()
            if filename:
                decoded_filename, encoding = decode_header(filename)[0]
                if isinstance(decoded_filename, bytes):
                    decoded_filename = decoded_filename.decode(encoding or 'utf-8')

                file_data = part.get_payload(decode=True)
                if file_data:
                    mime_type = part.get_content_type() or mimetypes.guess_type(decoded_filename)[0] or 'application/octet-stream'
                    attachments.append((decoded_filename, file_data, mime_type))

        return attachments

    async def process_files(self, record_repo: PolicyRecordRepository):
        """Extracts and uploads attachments from multiple emails."""
        self.connect()
        emails = self.fetch_emails()
        files_metadata = []
        for msg in emails:
            attachments = self.extract_attachments(msg)
            for filename, file_data, mime_type in attachments:
                logger.info("Upload File Info:")
                logger.info(f"===> File Name: {filename}")
                logger.info(f"===> File Type: {mime_type}")

                file_hash = hashlib.sha256(file_data).hexdigest()

                if await self.hash_exists(file_hash=file_hash, record_repo=record_repo):
                    logger.info(f"Duplicate skipped: File '{filename}' with hash {file_hash} already uploaded.")
                    continue

                file_content = io.BytesIO(file_data)

                storage_path = await storage_processor.upload_document(
                    storage_folder=ProcessorFolders.audio.value, 
                    file_name=filename, 
                    file_content=file_content, 
                    mime_type=mime_type
                )
                
                file_metadata = {
                    "File_Name": filename,
                    "Storage_Path": storage_path,
                    "Upload_Time": datetime.now(timezone.utc),
                    "File_Hash": file_hash
                }

                files_metadata.append(file_metadata)
        
        logger.info("Uploaded File Metadata:")
        logger.info(files_metadata)
        return files_metadata

email_service = EmailService(user=settings.email_username, password=settings.email_password)