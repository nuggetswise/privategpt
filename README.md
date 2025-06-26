# 🔒 Private-GPT Email RAG Assistant

A **100% private** AI-powered email assistant that processes your emails locally using [Private-GPT](https://github.com/zylon-ai/private-gpt) as the backend. No data leaves your machine - everything runs locally with Ollama models and Qdrant vector storage.

## 🎯 Features

### 🤖 **Core AI Capabilities**
- **100% Offline AI Chat**: Full conversation with your emails using local LLMs
- **Smart Email Analysis**: Automatic summarization, topic extraction, and sentiment analysis
- **Advanced Search**: Semantic search across all your emails with context-aware responses
- **Persona Detection**: AI-powered sender analysis and relationship insights
- **Document Processing**: Handle PDFs, images, and attachments with OCR

### 📧 **Email Processing**
- **Automatic Ingestion**: Watches directories for new `.eml`, `.mbox`, and `.elmx` files
- **Smart Deduplication**: Prevents reprocessing of identical emails
- **Rich Metadata**: Extracts subject, sender, date, labels, and attachment information
- **Multi-format Support**: Handles multipart emails, HTML content, and various formats
- **Real-time Processing**: Instant processing of new emails as they arrive

### 🖥️ **User Interface**
- **Modern Streamlit UI**: NotebookLM-style interface for intuitive email exploration
- **Real-time Chat**: Interactive AI conversations about your emails
- **Advanced Filtering**: Filter by sender, date range, labels, and content
- **Source Attribution**: See exactly which emails inform AI responses
- **Export Capabilities**: Download conversations and email insights

### 🔒 **Privacy & Security**
- **100% Local Processing**: No data ever leaves your machine
- **Zero Cloud Dependencies**: Everything runs on your local infrastructure
- **Encrypted Storage**: All data encrypted at rest and in transit
- **User Control**: Complete ownership and control over your data
- **Audit Trail**: Full logging of all processing activities

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Email Source  │───▶│  Email Parser   │───▶│  Private-GPT    │
│   (Local Files) │    │  (Content +     │    │   (Ingestion)   │
│                 │    │   Metadata)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │◀───│  Private-GPT    │◀───│   Qdrant DB     │
│  (Streamlit)    │    │  (Query API)    │    │ (Local Vector)  │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Ollama        │
                       │   (Local LLM)   │
                       └─────────────────┘
```

## 📋 Prerequisites

### **System Requirements**
- **OS**: macOS, Linux, or Windows
- **Python**: 3.8 or higher
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 10GB+ free space for models and data
- **CPU**: Multi-core processor (4+ cores recommended)

### **Software Dependencies**
- **Docker & Docker Compose**: For Private-GPT and Qdrant
- **Ollama**: For local LLM inference
- **Python Virtual Environment**: For Python dependencies

## 🚀 Quick Start

### **1. Clone and Setup**

```bash
# Clone the repository
git clone https://github.com/nuggetswise/privategpt.git
cd privategpt

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **2. Start Private-GPT Infrastructure**

```bash
# Start Private-GPT, Qdrant, and Ollama
docker-compose up -d

# Verify services are running
curl http://localhost:8001/health
curl http://localhost:11434/api/tags
```

### **3. Download AI Models**

```bash
# Download required Ollama models
ollama pull llama2:13b
ollama pull llama2:7b
ollama pull codellama:7b
```

### **4. Start the Email Processor**

```bash
# Start watching for emails
python directory_watcher.py --directory "/path/to/your/emails"

# Or process existing emails
python email_processor.py --directory "/path/to/your/emails"
```

### **5. Launch the Web Interface**

```bash
# Start Streamlit frontend
streamlit run frontend/app.py --server.port 8501
```

### **6. Access the System**

- **Web Interface**: http://localhost:8501
- **API Documentation**: http://localhost:8001/docs
- **Private-GPT Health**: http://localhost:8001/health

## 📁 Project Structure

```
privategpt/
├── email_processor.py      # Core email processing logic
├── directory_watcher.py    # File system watcher
├── frontend/              # Streamlit web interface
│   ├── app.py            # Main UI application
│   ├── components.py     # Reusable UI components
│   └── api_client.py     # Private-GPT API client
├── rag/                  # RAG pipeline components
│   ├── privategpt_client.py  # Private-GPT API wrapper
│   ├── ollama_client.py      # Ollama client
│   ├── qdrant_client.py      # Qdrant vector database
│   └── prompts.py            # AI prompt management
├── data/                 # Data storage
│   ├── emails/           # Email files
│   ├── processed/        # Processed email data
│   └── logs/             # Processing logs
├── docker-compose.yml    # Infrastructure orchestration
├── requirements.txt      # Python dependencies
├── setup.sh             # Setup script
└── README.md            # This file
```

## 🔧 Configuration

### **Environment Variables**

Create a `.env` file in the project root:

```bash
# Private-GPT Configuration
PRIVATE_GPT_URL=http://localhost:8001
PRIVATE_GPT_API_KEY=your-api-key

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2:13b
OLLAMA_EMBEDDING_MODEL=llama2:7b

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=your-api-key

# Email Processing
EMAIL_WATCH_DIRECTORY=/path/to/your/emails
EMAIL_PROCESSING_INTERVAL=30

# System Configuration
DEBUG=true
LOG_LEVEL=INFO
```

### **Docker Compose Configuration**

```yaml
# docker-compose.yml
version: '3.8'

services:
  private-gpt:
    image: ghcr.io/zylon-ai/private-gpt:latest
    container_name: private-gpt
    ports:
      - "8001:8001"
    environment:
      - PRIVATE_GPT_SERVER_HOST=0.0.0.0
      - PRIVATE_GPT_SERVER_PORT=8001
      - PRIVATE_GPT_SERVER_CORS_ALLOW_ORIGINS=["http://localhost:8501"]
      - PRIVATE_GPT_SERVER_AUTHENTICATION_GLOBAL_ENABLED=false
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    depends_on:
      - qdrant
      - ollama

  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  qdrant_data:
  ollama_data:
```

## 📧 Email Integration

### **Supported Formats**
- **`.eml`**: Standard email format (RFC 5322)
- **`.mbox`**: Mailbox format (multiple emails in one file)
- **`.elmx`**: Apple Mail format

### **Email Client Setup**

#### **Apple Mail**
1. Set up email rules to save emails as `.elmx` files
2. Configure save location to your watched directory

#### **Thunderbird**
1. Use add-ons to export emails as `.eml` files
2. Set up automatic export to the watched directory

#### **Gmail**
1. Use Gmail API or forwarding to save emails locally
2. Configure automatic download to watched directory

### **Manual Processing**

```bash
# Process a single email file
python email_processor.py --file "/path/to/email.eml"

# Process all emails in a directory
python email_processor.py --directory "/path/to/emails"

# Process with custom Private-GPT URL
python email_processor.py --private-gpt-url "http://localhost:8001"
```

## 🎯 Usage Examples

### **1. Basic Email Query**
```
Question: "What emails did I receive about project updates?"
Response: Lists relevant emails with context and metadata
```

### **2. Label-Specific Search**
```
Question: "Show me all AI-related emails from the last week"
Response: Filters by "AI" label and recent dates
```

### **3. Sender Analysis**
```
Question: "What does John usually email me about?"
Response: AI analysis of communication patterns and topics
```

### **4. Document Search**
```
Question: "Find emails with PDF attachments about budgets"
Response: Searches content and attachment metadata
```

### **5. Sentiment Analysis**
```
Question: "What's the overall tone of emails from my boss?"
Response: Sentiment analysis with specific examples
```

## 🔒 Privacy & Security

### **Data Privacy Guarantees**
- ✅ **100% Private Processing**: All data processed locally
- ✅ **Zero Data Sharing**: No data ever leaves your machine
- ✅ **Complete Control**: You own and control all your data
- ✅ **No Tracking**: No analytics or tracking of any kind

### **Security Measures**
- 🔐 **End-to-End Encryption**: All data encrypted in transit and at rest
- 🛡️ **Local Storage**: All data stored on your local machine
- 🔒 **No Cloud Dependencies**: Zero reliance on external services
- 📊 **Audit Trail**: Complete logging of all processing activities

### **Compliance**
- 📋 **GDPR Compliant**: Full data control and deletion capabilities
- 🏢 **Enterprise Ready**: Suitable for sensitive corporate data
- 🔐 **SOC 2 Ready**: Security controls and monitoring in place

## 🛠️ Troubleshooting

### **Common Issues**

#### **Private-GPT Connection Issues**
```bash
# Test connection
curl http://localhost:8001/health

# Check logs
docker-compose logs private-gpt
```

#### **Ollama Model Issues**
```bash
# List available models
curl http://localhost:11434/api/tags

# Pull missing models
ollama pull llama2:13b
```

#### **Email Processing Errors**
```bash
# Check processing logs
tail -f email_processor.log

# Reset processed emails (reprocess all)
rm processed_emails.json
```

#### **Permission Issues**
```bash
# Make scripts executable
chmod +x *.py
chmod +x setup.sh

# Check directory permissions
ls -la /path/to/your/emails
```

### **Performance Optimization**

#### **For Large Email Collections**
```bash
# Increase memory limits
export OLLAMA_HOST=0.0.0.0
export OLLAMA_GPU_LAYERS=35

# Use larger models for better quality
ollama pull llama2:70b
```

#### **For Faster Processing**
```bash
# Use smaller models for speed
ollama pull llama2:7b
ollama pull codellama:7b

# Enable GPU acceleration
export OLLAMA_GPU_LAYERS=35
```

## 🔄 Development

### **Running Components Individually**

#### **Email Processor Only**
```bash
python email_processor.py --directory "/path/to/emails"
```

#### **Directory Watcher Only**
```bash
python directory_watcher.py --directory "/path/to/emails"
```

#### **Frontend Only**
```bash
streamlit run frontend/app.py --server.port 8501
```

### **Adding New Features**

#### **Custom Email Processors**
```python
from email_processor import EmailProcessor

class CustomEmailProcessor(EmailProcessor):
    def _extract_email_content(self, email_path):
        # Add custom processing logic
        result = super()._extract_email_content(email_path)
        if result:
            content, metadata = result
            # Modify content or metadata as needed
            return content, metadata
        return None
```

#### **Custom RAG Components**
```python
from rag.privategpt_client import PrivateGPTClient

class CustomPrivateGPTClient(PrivateGPTClient):
    def custom_query(self, question: str, context: str):
        # Add custom query logic
        return self.query(question, context)
```

## 📊 Monitoring & Logging

### **Log Files**
- `email_processor.log`: Email processing activities
- `directory_watcher.log`: File system monitoring
- `frontend.log`: Web interface activities
- `private_gpt.log`: Private-GPT server logs

### **Health Checks**
```bash
# Check all services
curl http://localhost:8001/health
curl http://localhost:11434/api/tags
curl http://localhost:6333/health

# Check processing status
python -c "from email_processor import EmailProcessor; print(EmailProcessor().get_stats())"
```

## 🚀 Advanced Features

### **Batch Processing**
```bash
# Process all emails in a directory
python email_processor.py --directory "/path/to/emails" --batch-size 100

# Process with custom metadata
python email_processor.py --metadata '{"source": "backup", "priority": "high"}'
```

### **Custom Prompts**
```python
# Modify prompts in rag/prompts.py
CUSTOM_PROMPT = """
You are an email assistant. Answer questions about the user's emails.
Context: {context}
Question: {question}
Answer:"""
```

### **API Integration**
```python
import requests

# Query the system programmatically
response = requests.post("http://localhost:8001/v1/chat/completions", json={
    "query": "What emails did I receive about AI?",
    "top_k": 5
})
```

## 📚 Additional Resources

- [Private-GPT Documentation](https://docs.privategpt.dev/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Streamlit Documentation](https://docs.streamlit.io/)

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/nuggetswise/privategpt/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nuggetswise/privategpt/discussions)
- **Documentation**: [Project Wiki](https://github.com/nuggetswise/privategpt/wiki)

---

**Built with ❤️ for privacy-first AI email processing**

*This system ensures your emails remain completely private while providing powerful AI capabilities for email analysis and search.* 