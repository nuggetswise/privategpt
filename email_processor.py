#!/usr/bin/env python3
"""
Email Processing Pipeline for Private-GPT
Processes .eml, .mbox, and .elmx files and ingests them into Private-GPT
"""

import os
import json
import hashlib
import email
import email.policy
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from email_validator import validate_email, EmailNotValidError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmailProcessor:
    """Main email processing class for Private-GPT ingestion"""
    
    def __init__(self, private_gpt_url: str = "http://localhost:8001", 
                 processed_file: str = "processed_emails.json"):
        """
        Initialize the email processor
        
        Args:
            private_gpt_url: Private-GPT server URL
            processed_file: JSON file to track processed emails for deduplication
        """
        self.private_gpt_url = private_gpt_url.rstrip('/')
        self.processed_file = processed_file
        self.processed_emails = self._load_processed_emails()
        
    def _load_processed_emails(self) -> Dict[str, Dict]:
        """Load previously processed emails for deduplication"""
        if os.path.exists(self.processed_file):
            try:
                with open(self.processed_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Corrupted {self.processed_file}, starting fresh")
        return {}
    
    def _save_processed_emails(self):
        """Save processed emails to JSON file"""
        with open(self.processed_file, 'w') as f:
            json.dump(self.processed_emails, f, indent=2)
    
    def _generate_email_hash(self, subject: str, sender: str, date: str) -> str:
        """Generate unique hash for email deduplication"""
        content = f"{subject}|{sender}|{date}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _extract_email_content(self, email_path: Path) -> Optional[Tuple[str, Dict]]:
        """
        Extract email body and metadata from .eml file
        
        Args:
            email_path: Path to .eml file
            
        Returns:
            Tuple of (body_text, metadata_dict) or None if parsing fails
        """
        try:
            with open(email_path, 'r', encoding='utf-8', errors='ignore') as f:
                email_content = f.read()
            
            # Parse email using email library
            msg = email.message_from_string(email_content, policy=email.policy.default)
            
            # Extract metadata
            subject = msg.get('subject', 'No Subject')
            sender = msg.get('from', 'Unknown Sender')
            date_str = msg.get('date', '')
            
            # Parse date
            try:
                if date_str:
                    parsed_date = email.utils.parsedate_to_datetime(date_str)
                    date_formatted = parsed_date.isoformat()
                else:
                    date_formatted = datetime.now().isoformat()
            except:
                date_formatted = datetime.now().isoformat()
            
            # Extract body text
            body_text = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body_text += part.get_content()
                        break
                if not body_text:  # Fallback to HTML if no plain text
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            # Simple HTML to text conversion
                            import re
                            html_content = part.get_content()
                            body_text = re.sub('<[^<]+?>', '', html_content)
                            break
            else:
                if msg.get_content_type() == "text/plain":
                    body_text = msg.get_content()
                elif msg.get_content_type() == "text/html":
                    import re
                    html_content = msg.get_content()
                    body_text = re.sub('<[^<]+?>', '', html_content)
            
            # Clean up body text
            body_text = body_text.strip()
            if not body_text:
                body_text = "[No text content found]"
            
            metadata = {
                "subject": subject,
                "sender": sender,
                "date": date_formatted,
                "source_file": str(email_path),
                "content_type": "email",
                "processed_at": datetime.now().isoformat()
            }
            
            return body_text, metadata
            
        except Exception as e:
            logger.error(f"Failed to parse email {email_path}: {e}")
            return None
    
    def _ingest_to_private_gpt(self, content: str, metadata: Dict) -> bool:
        """
        Ingest email content into Private-GPT
        
        Args:
            content: Email body text
            metadata: Email metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "content": content,
                "metadata": metadata
            }
            
            response = requests.post(
                f"{self.private_gpt_url}/v1/ingest",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully ingested email: {metadata['subject']}")
                return True
            else:
                logger.error(f"Failed to ingest email: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for email ingestion: {e}")
            return False
    
    def process_email_file(self, email_path: Path) -> bool:
        """
        Process a single email file
        
        Args:
            email_path: Path to email file
            
        Returns:
            True if successfully processed, False otherwise
        """
        # Extract content and metadata
        result = self._extract_email_content(email_path)
        if not result:
            return False
            
        body_text, metadata = result
        
        # Check for duplicates
        email_hash = self._generate_email_hash(
            metadata['subject'], 
            metadata['sender'], 
            metadata['date']
        )
        
        if email_hash in self.processed_emails:
            logger.info(f"Email already processed: {metadata['subject']}")
            return True
        
        # Ingest to Private-GPT
        if self._ingest_to_private_gpt(body_text, metadata):
            # Mark as processed
            self.processed_emails[email_hash] = metadata
            self._save_processed_emails()
            return True
        else:
            return False
    
    def process_directory(self, directory_path: str) -> int:
        """
        Process all email files in a directory
        
        Args:
            directory_path: Path to directory containing email files
            
        Returns:
            Number of successfully processed files
        """
        directory = Path(directory_path)
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return 0
        
        processed_count = 0
        email_extensions = {'.eml', '.mbox', '.elmx'}
        
        for file_path in directory.rglob('*'):
            if file_path.suffix.lower() in email_extensions:
                logger.info(f"Processing: {file_path}")
                if self.process_email_file(file_path):
                    processed_count += 1
        
        logger.info(f"Processed {processed_count} email files")
        return processed_count

def main():
    """Main function for testing the email processor"""
    processor = EmailProcessor()
    
    # Example usage
    email_dir = "/Users/singhm/Emails"
    if os.path.exists(email_dir):
        processor.process_directory(email_dir)
    else:
        logger.info(f"Email directory {email_dir} does not exist. Create it and add .eml files.")

if __name__ == "__main__":
    main() 