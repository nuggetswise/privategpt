#!/usr/bin/env python3
"""
Directory Watcher for Email Processing Pipeline
Monitors a directory for new email files and processes them automatically
"""

import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from email_processor import EmailProcessor

logger = logging.getLogger(__name__)

class EmailFileHandler(FileSystemEventHandler):
    """File system event handler for email files"""
    
    def __init__(self, email_processor: EmailProcessor):
        """
        Initialize the file handler
        
        Args:
            email_processor: EmailProcessor instance to handle file processing
        """
        self.email_processor = email_processor
        self.email_extensions = {'.eml', '.mbox', '.elmx'}
        
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.email_extensions:
                logger.info(f"New email file detected: {file_path}")
                
                # Wait a moment for file to be fully written
                time.sleep(1)
                
                # Process the email file
                if self.email_processor.process_email_file(file_path):
                    logger.info(f"Successfully processed new email: {file_path}")
                else:
                    logger.error(f"Failed to process new email: {file_path}")
    
    def on_moved(self, event):
        """Handle file move events (useful for email clients that move files)"""
        if not event.is_directory:
            file_path = Path(event.dest_path)
            if file_path.suffix.lower() in self.email_extensions:
                logger.info(f"Email file moved to: {file_path}")
                
                # Wait a moment for file to be fully written
                time.sleep(1)
                
                # Process the email file
                if self.email_processor.process_email_file(file_path):
                    logger.info(f"Successfully processed moved email: {file_path}")
                else:
                    logger.error(f"Failed to process moved email: {file_path}")

class DirectoryWatcher:
    """Main directory watcher class"""
    
    def __init__(self, watch_directory: str, private_gpt_url: str = "http://localhost:8001"):
        """
        Initialize the directory watcher
        
        Args:
            watch_directory: Directory to watch for email files
            private_gpt_url: Private-GPT server URL
        """
        self.watch_directory = Path(watch_directory)
        self.private_gpt_url = private_gpt_url
        self.observer = None
        self.email_processor = EmailProcessor(private_gpt_url)
        
    def start_watching(self):
        """Start watching the directory for new email files"""
        if not self.watch_directory.exists():
            logger.error(f"Watch directory does not exist: {self.watch_directory}")
            return False
        
        # Process existing files first
        logger.info("Processing existing email files...")
        self.email_processor.process_directory(str(self.watch_directory))
        
        # Set up file system observer
        event_handler = EmailFileHandler(self.email_processor)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.watch_directory), recursive=True)
        
        # Start watching
        self.observer.start()
        logger.info(f"Started watching directory: {self.watch_directory}")
        logger.info("Press Ctrl+C to stop watching")
        
        return True
    
    def stop_watching(self):
        """Stop watching the directory"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Stopped watching directory")
    
    def run_continuously(self):
        """Run the watcher continuously until interrupted"""
        if not self.start_watching():
            return
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop_watching()

def main():
    """Main function to run the directory watcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Watch directory for email files and process them")
    parser.add_argument(
        "--directory", 
        default="/Users/singhm/Emails",
        help="Directory to watch for email files (default: /Users/singhm/Emails)"
    )
    parser.add_argument(
        "--private-gpt-url",
        default="http://localhost:8001",
        help="Private-GPT server URL (default: http://localhost:8001)"
    )
    
    args = parser.parse_args()
    
    # Create directory if it doesn't exist
    watch_dir = Path(args.directory)
    if not watch_dir.exists():
        watch_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created watch directory: {watch_dir}")
    
    # Start the watcher
    watcher = DirectoryWatcher(args.directory, args.private_gpt_url)
    watcher.run_continuously()

if __name__ == "__main__":
    main() 