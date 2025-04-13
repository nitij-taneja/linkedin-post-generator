#!/usr/bin/env python3
"""
Email Fetcher Module for LinkedIn Post Generator

This module handles fetching and parsing emails from a specified email account
to extract content for LinkedIn post generation.
"""

import imaplib
import email
import json
import os
import logging
from email.header import decode_header
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailFetcher:
    """Class to fetch and process emails from a specified account."""
    
    def __init__(self, config_path=None):
        """
        Initialize the EmailFetcher with configuration.
        
        Args:
            config_path (str, optional): Path to the configuration file.
                If None, uses default config path.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config',
            'sources.json'
        )
        self.config = self._load_config()
        self.email_config = self.config.get('email', {})
        
    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
            
    def connect(self, username, password):
        """
        Connect to the email server.
        
        Args:
            username (str): Email account username
            password (str): Email account password
            
        Returns:
            imaplib.IMAP4_SSL: Connected IMAP client
        """
        server = self.email_config.get('server', 'imap.gmail.com')
        port = self.email_config.get('port', 993)
        use_ssl = self.email_config.get('use_ssl', True)
        
        try:
            if use_ssl:
                mail = imaplib.IMAP4_SSL(server, port)
            else:
                mail = imaplib.IMAP4(server, port)
                
            mail.login(username, password)
            logger.info(f"Successfully connected to {server}")
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            raise
            
    def fetch_emails(self, username, password):
        """
        Fetch emails based on search criteria in config.
        
        Args:
            username (str): Email account username
            password (str): Email account password
            
        Returns:
            list: List of dictionaries containing email data
        """
        mail = self.connect(username, password)
        folder = self.email_config.get('folder', 'INBOX')
        search_criteria = self.email_config.get('search_criteria', 'UNSEEN')
        max_emails = self.email_config.get('max_emails', 5)
        
        try:
            mail.select(folder)
            status, data = mail.search(None, search_criteria)
            
            if status != 'OK':
                logger.error(f"Search failed with status: {status}")
                return []
                
            email_ids = data[0].split()
            if not email_ids:
                logger.info("No emails found matching criteria")
                return []
                
            # Limit to max_emails
            email_ids = email_ids[-min(max_emails, len(email_ids)):]
            
            emails = []
            for e_id in email_ids:
                status, data = mail.fetch(e_id, '(RFC822)')
                if status != 'OK':
                    logger.warning(f"Failed to fetch email ID {e_id}")
                    continue
                    
                raw_email = data[0][1]
                email_message = email.message_from_bytes(raw_email)
                
                # Process email
                email_data = self._process_email(email_message)
                if email_data:
                    emails.append(email_data)
                    
            logger.info(f"Successfully fetched {len(emails)} emails")
            return emails
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass
                
    def _process_email(self, email_message):
        """
        Process an email message to extract relevant content.
        
        Args:
            email_message: Email message object
            
        Returns:
            dict: Dictionary containing email data
        """
        subject = self._decode_header(email_message.get('Subject', ''))
        from_addr = self._decode_header(email_message.get('From', ''))
        date_str = email_message.get('Date', '')
        
        try:
            date = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        except:
            date = datetime.now()
            
        # Get email body
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                    
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
                elif content_type == "text/html" and not body:
                    # Use HTML if plain text not found
                    import html2text
                    h = html2text.HTML2Text()
                    h.ignore_links = False
                    body = h.handle(part.get_payload(decode=True).decode())
        else:
            body = email_message.get_payload(decode=True).decode()
            
        return {
            'subject': subject,
            'from': from_addr,
            'date': date.isoformat(),
            'body': body
        }
        
    def _decode_header(self, header):
        """Decode email header."""
        decoded_header = decode_header(header)[0]
        if isinstance(decoded_header[0], bytes):
            return decoded_header[0].decode(decoded_header[1] or 'utf-8')
        return decoded_header[0]
        
if __name__ == "__main__":
    # Example usage
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
