#!/bin/bash
# Setup script for Email Processing Pipeline

echo "🚀 Setting up Email Processing Pipeline for Private-GPT"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $python_version detected"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create email directory
EMAIL_DIR="/Users/singhm/Emails"
if [ ! -d "$EMAIL_DIR" ]; then
    echo "📁 Creating email directory: $EMAIL_DIR"
    mkdir -p "$EMAIL_DIR"
else
    echo "✅ Email directory already exists: $EMAIL_DIR"
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x email_processor.py
chmod +x directory_watcher.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start your Private-GPT server (should be running on localhost:8001)"
echo "2. Place .eml files in $EMAIL_DIR"
echo "3. Run the watcher: python directory_watcher.py"
echo ""
echo "🔧 Optional: Test with a single email file:"
echo "   python email_processor.py"
echo ""
echo "📖 For more options, run: python directory_watcher.py --help" 