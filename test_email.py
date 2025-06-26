#!/usr/bin/env python3
"""
Test script for email processing pipeline
Creates a sample email and tests the processing functionality
"""

import tempfile
import os
from pathlib import Path
from email_processor import EmailProcessor

def create_sample_email():
    """Create a sample .eml file for testing"""
    
    sample_email_content = """From: newsletter@example.com
To: user@example.com
Subject: Weekly Tech Newsletter - Issue #42
Date: Mon, 15 Jan 2024 10:30:00 +0000
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8

Hello Tech Enthusiasts!

This week's newsletter brings you the latest developments in AI and machine learning:

1. **New Developments in Large Language Models**
   Researchers at OpenAI have released new findings on GPT-5 architecture improvements.

2. **Privacy-First AI Solutions**
   Local AI processing is becoming more popular as concerns about data privacy grow.

3. **Open Source AI Tools**
   Several new open-source AI frameworks have been released this week.

Key Takeaways:
- Local AI processing is the future
- Privacy concerns are driving innovation
- Open source is accelerating AI development

Best regards,
The Tech Newsletter Team

---
To unsubscribe, click here: https://example.com/unsubscribe
"""

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.eml', delete=False) as f:
        f.write(sample_email_content)
        temp_path = f.name
    
    return Path(temp_path)

def test_email_processing():
    """Test the email processing functionality"""
    
    print("🧪 Testing Email Processing Pipeline")
    print("=" * 50)
    
    # Create sample email
    print("📧 Creating sample email...")
    sample_email_path = create_sample_email()
    print(f"✅ Created sample email: {sample_email_path}")
    
    # Initialize processor (without actual ingestion for testing)
    print("\n🔧 Initializing email processor...")
    processor = EmailProcessor()
    
    # Test content extraction
    print("\n📖 Testing content extraction...")
    result = processor._extract_email_content(sample_email_path)
    
    if result:
        content, metadata = result
        print("✅ Content extraction successful!")
        print(f"📋 Subject: {metadata['subject']}")
        print(f"👤 Sender: {metadata['sender']}")
        print(f"📅 Date: {metadata['date']}")
        print(f"📄 Content length: {len(content)} characters")
        print(f"📄 Content preview: {content[:200]}...")
        
        # Test deduplication
        print("\n🔍 Testing deduplication...")
        email_hash = processor._generate_email_hash(
            metadata['subject'], 
            metadata['sender'], 
            metadata['date']
        )
        print(f"🔑 Generated hash: {email_hash}")
        
        # Test metadata structure
        print("\n📊 Metadata structure:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
            
    else:
        print("❌ Content extraction failed!")
    
    # Cleanup
    print(f"\n🧹 Cleaning up test file: {sample_email_path}")
    try:
        os.unlink(sample_email_path)
        print("✅ Test file cleaned up")
    except:
        print("⚠️  Could not clean up test file")
    
    print("\n🎉 Test completed!")

def test_private_gpt_connection():
    """Test connection to Private-GPT server"""
    
    print("\n🔗 Testing Private-GPT Connection")
    print("=" * 40)
    
    import requests
    
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ Private-GPT server is running and accessible")
        else:
            print(f"⚠️  Private-GPT server responded with status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Private-GPT server")
        print("   Make sure Private-GPT is running on localhost:8001")
    except requests.exceptions.Timeout:
        print("❌ Connection to Private-GPT server timed out")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_email_processing()
    test_private_gpt_connection() 