#!/usr/bin/env python3
"""
Enhanced Email Processor for Private-GPT
Advanced email processing with Private-GPT integration
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
import argparse

# Import our Private-GPT client
from rag.privategpt_client import PrivateGPTClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_email_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedEmailProcessor:
    """Enhanced email processing class with Private-GPT integration"""
    
    def __init__(self, private_gpt_url: str = "http://localhost:8001", 
                 processed_file: str = "enhanced_processed_emails.json"):
        """
        Initialize the enhanced email processor
        
        Args:
            private_gpt_url: Private-GPT server URL
            processed_file: JSON file to track processed emails for deduplication
        """
        self.private_gpt_url = private_gpt_url.rstrip('/')
        self.processed_file = processed_file
        self.processed_emails = self._load_processed_emails()
        self.private_gpt_client = PrivateGPTClient(private_gpt_url)
        
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
            
            # Enhanced metadata
            metadata = {
                "subject": subject,
                "sender": sender,
                "date": date_formatted,
                "source_file": str(email_path),
                "content_type": "email",
                "processed_at": datetime.now().isoformat(),
                "email_id": self._generate_email_hash(subject, sender, date_formatted),
                "has_attachments": bool(msg.get_payload()),
                "attachment_count": len([p for p in msg.walk() if p.get_filename()]),
                "labels": self._extract_labels(subject, sender),
                "priority": self._determine_priority(subject, sender)
            }
            
            return body_text, metadata
            
        except Exception as e:
            logger.error(f"Failed to parse email {email_path}: {e}")
            return None
    
    def _extract_labels(self, subject: str, sender: str) -> List[str]:
        """Extract labels from email subject and sender"""
        labels = []
        
        # Common label patterns
        label_patterns = [
            r'\[([^\]]+)\]',  # [Label] format
            r'Label:\s*([^\s]+)',  # Label: format
            r'Category:\s*([^\s]+)',  # Category: format
        ]
        
        import re
        for pattern in label_patterns:
            matches = re.findall(pattern, subject, re.IGNORECASE)
            labels.extend(matches)
        
        # Sender-based labels
        if 'noreply' in sender.lower():
            labels.append('automated')
        if 'newsletter' in sender.lower() or 'newsletter' in subject.lower():
            labels.append('newsletter')
        if 'urgent' in subject.lower() or 'asap' in subject.lower():
            labels.append('urgent')
        
        return list(set(labels))
    
    def _determine_priority(self, subject: str, sender: str) -> str:
        """Determine email priority"""
        priority_indicators = {
            'high': ['urgent', 'asap', 'important', 'critical', 'emergency'],
            'medium': ['update', 'notification', 'reminder'],
            'low': ['newsletter', 'promotion', 'marketing']
        }
        
        subject_lower = subject.lower()
        sender_lower = sender.lower()
        
        for priority, indicators in priority_indicators.items():
            for indicator in indicators:
                if indicator in subject_lower or indicator in sender_lower:
                    return priority
        
        return 'normal'
    
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
            # Check if Private-GPT is available
            if not self.private_gpt_client.health_check():
                logger.error("Private-GPT is not running")
                return False
            
            # Create a temporary file for ingestion
            temp_file = Path(f"temp_email_{metadata['email_id']}.txt")
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Ingest into Private-GPT
            file_id = self.private_gpt_client.ingest_file(temp_file, metadata)
            
            # Clean up temp file
            temp_file.unlink()
            
            if file_id:
                logger.info(f"Successfully ingested email: {metadata['subject']}")
                return True
            else:
                logger.error(f"Failed to ingest email: {metadata['subject']}")
                return False
                
        except Exception as e:
            logger.error(f"Error ingesting to Private-GPT: {e}")
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
        email_hash = metadata['email_id']
        
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
            Number of successfully processed emails
        """
        directory = Path(directory_path)
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return 0
        
        email_extensions = {'.eml', '.mbox', '.elmx'}
        processed_count = 0
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in email_extensions:
                if self.process_email_file(file_path):
                    processed_count += 1
        
        logger.info(f"Processed {processed_count} emails from {directory_path}")
        return processed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'total_processed': len(self.processed_emails),
            'private_gpt_available': self.private_gpt_client.health_check(),
            'processed_file': self.processed_file,
            'last_processed': max([m.get('processed_at', '') for m in self.processed_emails.values()], default='')
        }

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Enhanced Email Processor for Private-GPT")
    parser.add_argument(
        "--directory", 
        help="Directory to process email files from"
    )
    parser.add_argument(
        "--file", 
        help="Single email file to process"
    )
    parser.add_argument(
        "--private-gpt-url",
        default="http://localhost:8001",
        help="Private-GPT server URL"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show processing statistics"
    )
    
    args = parser.parse_args()
    
    processor = EnhancedEmailProcessor(args.private_gpt_url)
    
    if args.stats:
        stats = processor.get_stats()
        print(json.dumps(stats, indent=2))
        return
    
    if args.file:
        file_path = Path(args.file)
        if processor.process_email_file(file_path):
            print(f"Successfully processed: {args.file}")
        else:
            print(f"Failed to process: {args.file}")
    elif args.directory:
        count = processor.process_directory(args.directory)
        print(f"Processed {count} emails from {args.directory}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 