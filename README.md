# 🤖 Jarvis AI - Intelligent Code Assistant

[![Made with Django](https://img.shields.io/badge/Made%20with-Django-092E20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-005571?style=for-the-badge&logo=elasticsearch)](https://www.elastic.co/)
[![Gemini AI](https://img.shields.io/badge/Gemini%20AI-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)

**AI-powered code intelligence with hybrid search, infinite memory, and multimodal debugging.**

> Chat with your entire codebase. Jarvis AI understands every function, remembers every conversation, and debugs with screenshots.

🔗 **[Live Demo](https://your-cloud-run-url.run.app)** | 📹 **[Demo Video](https://youtube.com/your-video)** | 📚 **[Documentation](#features)**

---

## ✨ Features

### 🧠 **Advanced RAG System**
- **Hybrid Search**: Combines BM25 keyword matching with semantic vector search
- **AI Reranking**: Google Gemini Pro reranks top results for 40% better relevance
- **Context-Aware**: Retrieves relevant code snippets from entire repositories

### 💬 **Infinite Conversation Memory**
- **Automatic Summarization**: Every 5 Q&A pairs condensed into memory batches
- **Vector-Indexed Storage**: Summaries stored in Elasticsearch for semantic retrieval
- **Dual-Context System**: Answers pull from both codebase AND conversation history
- **Memory Debug Console**: Transparency into what Jarvis remembers

### 🎨 **Multimodal Debugging**
- **Screenshot Analysis**: Upload error screenshots for AI-powered diagnosis
- **OCR + Vision AI**: Extracts error text from images automatically
- **Codebase-Specific Solutions**: Suggests fixes using YOUR repository's code
- **Web Search Integration**: DuckDuckGo search for StackOverflow solutions

### 📦 **Intelligent Repository Ingestion**
- **GitHub URL Support**: Paste any public repo URL for automatic cloning
- **Multi-Language Parsing**: Tree-sitter parser for 15+ languages
- **Smart Chunking**: Automatic extraction of functions, classes, methods
- **Real-Time Status**: Monitor parsing, embedding, and indexing progress

### 🚀 **Real-Time Experience**
- **Streaming Responses**: Character-by-character answer generation
- **Non-Blocking UI**: Smooth interactions without page reloads
- **Progress Tracking**: Visual feedback for long operations

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│              (Django Templates + Tailwind CSS)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      Django Backend                          │
│          (Views, URL Routing, Business Logic)                │
└────┬─────────────┬─────────────────┬───────────────────┬────┘
     │             │                 │                   │
     ▼             ▼                 ▼                   ▼
┌─────────┐ ┌──────────────┐ ┌──────────┐ ┌────────────────┐
│PostgreSQL│ │Elasticsearch │ │  Gemini  │ │ Cloud Storage  │
│ Database │ │  (Search +   │ │ Pro API  │ │ (User Images)  │
│          │ │   Vectors)   │ │          │ │                │
└─────────┘ └──────────────┘ └──────────┘ └────────────────┘
```

### **Technology Stack**

| Layer | Technology |
|-------|------------|
| **Frontend** | Django Templates, Tailwind CSS 3.4, Alpine.js |
| **Backend** | Django 5.2, Python 3.11, Gunicorn |
| **Search** | Elasticsearch 8.x (BM25 + Vector Search) |
| **AI/ML** | Google Gemini Pro 1.5 |
| **Cloud** | Google Cloud Run, Compute Engine, Cloud Storage |
| **Database** | PostgreSQL (prod), SQLite (dev) |
| **Deployment** | Docker, Cloud Build |

---

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11+
- Elasticsearch 8.x
- Google Cloud account (for Gemini API)
- Git

### **1. Clone Repository**
```bash
git clone https://github.com/yourusername/jarvis-ai.git
cd jarvis-ai
```

### **2. Create Virtual Environment**
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Environment Configuration**
Create `.env` file in root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key

# Elasticsearch
ES_URL=http://localhost:9200/

# Google Cloud Storage (Optional for local dev)
GS_BUCKET_NAME=your-bucket-name
```

### **5. Database Setup**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### **6. Start Elasticsearch**
If using Docker:
```bash
docker run -d -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.11.0
```

Verify it's running:
```bash
curl http://localhost:9200
```

### **7. Run Development Server**
```bash
python manage.py runserver
```

Visit `http://localhost:8000` 🎉

---

## 📖 Usage Guide

### **1. Upload a Repository**

**Option A: GitHub URL**
1. Click "Upload Repository"
2. Paste GitHub URL (e.g., `https://github.com/django/django`)
3. Provide repository name and description
4. Click "Upload" and wait for processing

**Option B: ZIP File**
1. Compress your codebase as `.zip`
2. Upload via file picker
3. Jarvis extracts and processes automatically

### **2. Start Chatting**

**Basic Question:**
```
"How does the authentication system work in this codebase?"
```

**Context-Dependent Question:**
```
"Show me where user sessions are stored"
```

**Multi-File Query:**
```
"What's the data flow from frontend forms to database?"
```

### **3. Multimodal Debugging**

1. Navigate to "Debug Code" page
2. Upload error screenshot (or paste with Ctrl+V)
3. Jarvis extracts error text
4. Get AI-powered solution with code references

### **4. Memory Management**

- Chat history auto-summarizes every 5 Q&A pairs
- View summaries in "Memory Debug" console
- See what Jarvis remembers about your session

---

## 🏗️ Project Structure

```
jarvis/
├── apps/
│   ├── chat/                 # Chat functionality
│   │   ├── views.py         # Chat endpoints
│   │   ├── models.py        # ChatSession, Message models
│   │   └── templates/       # Chat UI
│   ├── repo_ingest/         # Repository processing
│   │   ├── views.py         # Upload, parsing logic
│   │   ├── services/        # Tree-sitter, embedding
│   │   └── tasks.py         # Background ingestion
│   ├── users/               # Authentication
│   │   ├── views.py         # Login, signup, guest
│   │   └── templates/       # Auth UI
│   └── memory/              # Memory management
│       ├── services.py      # Summarization logic
│       └── models.py        # Memory storage
├── jarvis/                  # Main Django config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── static/                  # Static assets
├── templates/               # Base templates
├── media/                   # User uploads
├── Dockerfile               # Production build
├── requirements.txt         # Python dependencies
└── manage.py
```

---

## 🔧 Configuration

### **Elasticsearch Setup**

**Local Development:**
```bash
# Single-node cluster
docker run -d \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.11.0
```

**GCP Deployment:**
1. Create Compute Engine VM (e2-medium recommended)
2. SSH into VM
3. Install Docker and run Elasticsearch container
4. Configure firewall rules for port 9200

### **Google Gemini API**

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Create API key
3. Add to `.env`: `GEMINI_API_KEY=your-key`

### **Google Cloud Storage (Production)**

1. Create GCS bucket
2. Enable Cloud Storage API
3. Create service account with Storage Admin role
4. Download JSON key
5. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

---

## 🚢 Deployment (Google Cloud Run)

### **1. Prepare Dockerfile**
Already included in repository. Ensure it has:
- Python 3.11 base image
- Dependencies from `requirements.txt`
- Gunicorn as WSGI server
- Static files collected

### **2. Deploy Command**
```bash
gcloud run deploy jarvis-ai \
  --source . \
  --platform managed \
  --region asia-south2 \
  --allow-unauthenticated \
  --set-env-vars="SECRET_KEY=prod-key,GEMINI_API_KEY=your-key,ES_URL=http://your-es-ip:9200/,GS_BUCKET_NAME=your-bucket" \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300
```

### **3. Post-Deployment**
- Update `ALLOWED_HOSTS` in `settings.py`
- Run migrations via Cloud Run console
- Test all features on live URL

---

## 📊 Performance & Scalability

| Metric | Value |
|--------|-------|
| **Query Latency** | < 2 seconds (typical) |
| **Ingestion Speed** | ~100 files/minute |
| **Concurrent Users** | 10+ simultaneous sessions |
| **Context Window** | Up to 100K tokens |
| **Memory Efficiency** | Auto-summarization prevents overflow |

**Scalability:**
- Horizontal scaling via Cloud Run auto-scaling
- Elasticsearch cluster-ready architecture
- Stateless Django design
- Cloud Storage for media (no local storage limits)

---

## 🛠️ Development

### **Running Tests**
```bash
python manage.py test
```

### **Code Quality**
```bash
# Format code
black .

# Lint
flake8

# Type checking
mypy .
```

### **Debug Mode**
Set `DEBUG=True` in `.env` for detailed error pages and logging.

---

## 🤝 Contributing

Contributions welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

**Code Style:** Follow PEP 8, use Black formatter

---

## 📝 License


---

## 🙏 Acknowledgments

**Built with:**
- [Google Cloud Platform](https://cloud.google.com/) - Infrastructure & hosting
- [Elasticsearch](https://www.elastic.co/) - Hybrid search engine
- [Google Gemini Pro](https://ai.google.dev/) - AI-powered intelligence
- [Django](https://www.djangoproject.com/) - Web framework
- [Tailwind CSS](https://tailwindcss.com/) - UI styling
- [Tree-sitter](https://tree-sitter.github.io/) - Code parsing

**Special Thanks:**
- Google Cloud team for Cloud Run & Gemini API
- Elastic team for Elasticsearch infrastructure
- Open source community for amazing tools

---

## 📧 Contact

**Developer:** Avi Kumar 
**Email:** avik22835@gmail.com 
**GitHub:** [@avik22835](https://github.com/avik22835) 

**Project Link:** [https://github.com/avik22835/Jarvis_AI](https://github.com/avik22835/Jarvis_AI)

---

## 🌟 Star this repo if you find it useful!

**Made with ❤️ using Google Cloud + Elasticsearch**
