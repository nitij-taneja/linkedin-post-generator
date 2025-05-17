#!/usr/bin/env python3
"""
Email Fetcher Module for LinkedIn Post Generator
Handles fetching emails (seen + unseen) filtered for Avi Chawla and Bhavishya Pandit's newsletters.
"""

import imaplib
import email
import json
import os
import logging
from email.header import decode_header
from datetime import datetime

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailFetcher:
    def __init__(self, config_path=None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'sources.json'
        )
        self.config = self._load_config()
        self.email_config = self.config.get('email', {})
        self.used_emails_path = os.path.join(os.path.dirname(__file__), 'used_emails.json')
        self.used_subjects = self._load_used_subjects()

    def _load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def _load_used_subjects(self):
        if os.path.exists(self.used_emails_path):
            with open(self.used_emails_path, 'r') as f:
                return set(json.load(f))
        return set()

    def _save_used_subjects(self):
        with open(self.used_emails_path, 'w') as f:
            json.dump(list(self.used_subjects), f, indent=2)

    def connect(self, username, password):
        server = self.email_config.get('server', 'imap.gmail.com')
        port = self.email_config.get('port', 993)
        use_ssl = self.email_config.get('use_ssl', True)

        try:
            mail = imaplib.IMAP4_SSL(server, port) if use_ssl else imaplib.IMAP4(server, port)
            mail.login(username, password)
            logger.info(f"Connected to {server}")
            return mail
        except Exception as e:
            logger.error(f"Email login failed: {e}")
            raise

    def fetch_emails(self, username, password):
        mail = self.connect(username, password)
        folder = self.email_config.get('folder', 'INBOX')
        max_emails = self.email_config.get('max_emails', 10)
        search_criteria = 'OR FROM "avi@dailydoseofds.com" FROM "bhavishyapandit9@substack.com"'

        try:
            mail.select(folder)
            status, data = mail.search(None, search_criteria)
            logger.info(f"Search result: status={status}, ids={data[0].split()}")
            if status != 'OK':
                logger.error(f"Search failed: {status}")
                return []

            email_ids = data[0].split()[::-1]  # Reverse for latest first
            emails = []

            for e_id in email_ids:
                if len(emails) >= max_emails:
                    break

                status, data = mail.fetch(e_id, '(RFC822)')
                if status != 'OK':
                    logger.warning(f"Failed to fetch email ID {e_id}")
                    continue

                raw_email = data[0][1]
                email_message = email.message_from_bytes(raw_email)
                email_data = self._process_email(email_message)

                if email_data and email_data['subject'] not in self.used_subjects:
                    logger.info(f"Fetched: Subject={email_data['subject']} From={email_data['from']}")
                    emails.append(email_data)
                    self.used_subjects.add(email_data['subject'])

            self._save_used_subjects()
            logger.info(f"Fetched {len(emails)} new emails")
            return emails

        except Exception as e:
            logger.error(f"Email fetching failed: {e}")
            return []
        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass

    def _process_email(self, email_message):
        subject = self._decode_header(email_message.get('Subject', ''))
        from_addr = self._decode_header(email_message.get('From', ''))
        date_str = email_message.get('Date', '')

        try:
            date = datetime.strptime(date_str[:31], '%a, %d %b %Y %H:%M:%S %z')
        except:
            date = datetime.now()

        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if "attachment" in str(part.get("Content-Disposition", "")):
                    continue
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors='ignore')
                    break
                elif part.get_content_type() == "text/html" and not body:
                    import html2text
                    h = html2text.HTML2Text()
                    h.ignore_links = False
                    body = h.handle(part.get_payload(decode=True).decode(errors='ignore'))
        else:
            body = email_message.get_payload(decode=True).decode(errors='ignore')

        return {
            'subject': subject,
            'from': from_addr,
            'date': date.isoformat(),
            'body': body
        }

    def _decode_header(self, header):
        decoded_header = decode_header(header)[0]
        if isinstance(decoded_header[0], bytes):
            return decoded_header[0].decode(decoded_header[1] or 'utf-8')
        return decoded_header[0]

if __name__ == "__main__":
    import os
    username = os.environ.get('EMAIL_USERNAME')
    password = os.environ.get('EMAIL_PASSWORD')

    if username and password:
        fetcher = EmailFetcher()
        emails = fetcher.fetch_emails(username, password)
        print(f"Fetched {len(emails)} emails")
        for i, email_data in enumerate(emails):
            print(f"\nEmail {i+1}:")
            print(f"Subject: {email_data['subject']}")
            print(f"From: {email_data['from']}")
            print(f"Date: {email_data['date']}")
            print(f"Body preview: {email_data['body'][:100]}...")
    else:
        print("EMAIL_USERNAME and EMAIL_PASSWORD environment variables required")
