# Hybrid RAG System - Regulatory Compliance Checker

A production-grade Hybrid RAG (Retrieval-Augmented Generation) system that combines **persistent regulatory data** with **ephemeral session-specific data** for intelligent compliance checking and architectural analysis.

## 🎯 Overview

This system demonstrates a sophisticated approach to RAG architecture by separating two distinct data types:

- **🗄️ Persistent Data**: Regulatory PDFs stored permanently in ChromaDB vector database, searchable across all sessions
- **⚡ Ephemeral Data**: User-uploaded architectural drawing JSON passed at runtime, stored in Redis with 1-hour TTL, never indexed in vector store

The system uses **LangGraph** for multi-step reasoning, **GPT-4** for natural language understanding, and custom **geometry analysis tools** to check architectural compliance against building regulations.

## 🚀 Quick Start

### Setup in 3 Steps
```bash
# 1. Set your OpenAI API key
export OPENAI_API_KEY=sk-your-key-here  # Linux/Mac
# OR
$env:OPENAI_API_KEY="sk-your-key-here"  # Windows PowerShell

# 2. Start all services
docker-compose up -d

# 3. Open the application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# ChromaDB: http://localhost:8001
```

### Using the Application

1. **💬 Chat Interface**: Open http://localhost:3000 to ask compliance questions
2. **📝 Load Drawing Data**: Use the JSON editor (right side) to load architectural drawings
3. **📄 Add Regulations**: Ingest PDFs using the ingestion script (see [Data Ingestion](#data-ingestion))


## ✨ Top Features

### 1. **Hybrid RAG Architecture**
- Combines persistent vector database with ephemeral runtime data
- Semantic search over regulatory documents
- Zero-shot geometry analysis from JSON drawings
- Parent Document Retriever for hierarchical chunking

### 2. **Advanced LangGraph Workflow**
Multi-step reasoning pipeline:
- **Retrieve**: Query ChromaDB for relevant regulations
- **Analyze**: Process drawing geometry with custom tools
- **Reason**: LLM synthesizes both data sources
- **Critique**: Self-validation before responding
- **Respond**: Structured output with citations

### 3. **Intelligent Geometry Analysis**
Custom Shapely-based tool for spatial reasoning:
- Calculate polygon areas (e.g., 50% curtilage rule)
- Measure distances between objects (e.g., 2m boundary rule)
- Analyze overlaps and intersections
- Layer-based object categorization

### 4. **Advanced PDF Processing**
Uses `unstructured` library with hi_res strategy:
- Multi-column document parsing
- Table extraction with structure preservation
- Automatic metadata tagging
- Hierarchical chunking (parent 2000 chars, child 400 chars)

### 5. **JWT Authentication**
Secure API with IDOR protection:
- Bcrypt password hashing
- OAuth2 bearer token flow
- 30-minute token expiration
- User-specific data isolation

### 6. **Real-time Session Management**
- UUID-based session IDs
- Redis-backed storage with TTL
- Drawing data association
- Full session lifecycle management

### 7. **Modern React Frontend**
- Real-time chat interface
- Monaco JSON editor with validation
- Tailwind CSS responsive design
- React Query for state management

### 8. **Structured Compliance Output**
Pydantic-validated responses:
- Compliance verdict (boolean)
- Detailed explanation
- Cited regulatory sources with references
- Reasoning step traces

## 🏗️ Architecture

### System Components

```
┌──────────────────────────────────────────────────────────────────┐
│                     User Interface (React)                       │
│  • Chat Interface  • JSON Editor  • Session Management           │
└─────────────────────────┬────────────────────────────────────────┘
                          │ HTTP/REST
┌─────────────────────────▼────────────────────────────────────────┐
│                   Backend API (FastAPI)                          │
│  • JWT Auth  • Session CRUD  • Redis Storage  • Request Proxy   │
└──────────────┬──────────────────────────┬────────────────────────┘
               │                          │
   ┌───────────▼──────────┐   ┌──────────▼──────────┐
   │   Redis Cache        │   │   Agent Service     │
   │  • Session Data      │   │   (LangGraph)       │
   │  • Drawing JSON      │   │  • Multi-step       │
   │  • 1-hour TTL        │   │    Reasoning        │
   └──────────────────────┘   │  • Tool Calling     │
                              └────┬─────────┬──────┘
                                   │         │
                    ┌──────────────▼──┐   ┌─▼─────────────┐
                    │  ChromaDB       │   │  Geometry     │
                    │  Vector Store   │   │  Analysis     │
                    │  • Regulations  │   │  Tool         │
                    │  • Embeddings   │   │  • Shapely    │
                    │  • Persistent   │   │  • Spatial    │
                    └─────────────────┘   └───────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18, Tailwind CSS, Vite | Modern responsive UI |
| **Backend** | FastAPI, Python 3.11+ | RESTful API server |
| **Agent** | LangGraph, LangChain, GPT-4 | Multi-step reasoning |
| **Vector DB** | ChromaDB 0.4.24 | Persistent document storage |
| **Cache** | Redis 7 Alpine | Ephemeral data with TTL |
| **Authentication** | JWT, Bcrypt, python-jose | Secure API access |
| **Validation** | Pydantic | Data schema validation |
| **Geometry** | Shapely | Spatial analysis |
| **PDF Processing** | unstructured | Advanced document parsing |

## 📦 Project Structure

```
hybrid-rag/
├── frontend/                    # React + Tailwind UI
│   ├── src/
│   │   ├── App.jsx             # Main application
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx       # Chat UI
│   │   │   ├── ComplianceWorkbench.tsx # Compliance features
│   │   │   └── JsonEditor.jsx          # Monaco editor
│   │   └── api/
│   │       └── api.js          # API client
│   ├── Dockerfile
│   └── README.md               # Frontend documentation
│
├── backend/                     # FastAPI REST API
│   ├── app/
│   │   ├── main.py             # FastAPI app & routes
│   │   ├── auth.py             # JWT authentication
│   │   ├── config.py           # Configuration
│   │   ├── redis_client.py     # Redis connection
│   │   ├── session_manager.py  # Session lifecycle
│   │   └── routers/
│   │       ├── agent.py        # Agent proxy
│   │       ├── chat.py         # Chat endpoints
│   │       └── session.py      # Session endpoints
│   ├── schemas.py              # Pydantic schemas
│   ├── Dockerfile
│   └── README.md               # Backend documentation
│
├── agent/                       # LangGraph AI Agent
│   ├── agent.py                # Legacy agent (deprecated)
│   ├── graph.py                # LangGraph workflow ⭐
│   ├── geometry_tool.py        # Spatial analysis tool
│   ├── vector_store.py         # ChromaDB client
│   ├── ingest_pdf.py           # PDF ingestion CLI
│   ├── ingest.py               # Ingestion logic
│   ├── state.py                # Graph state definition
│   ├── main.py                 # Agent API server
│   ├── Dockerfile
│   └── README.md               # Agent documentation
│
├── pdfs/                        # Regulatory documents
├── tests/                       # Integration tests
│   ├── test_api_citations.py   # API citation tests
│   ├── test_full_citations.py  # E2E citation tests
│   ├── test_geometry.py        # Geometry tool tests
│   ├── test_graph.py           # LangGraph tests
│   ├── test_retrieval.py       # Vector store tests
│   └── fixtures/
│       └── 240314_Drawing.json # Sample drawing
│
├── docker-compose.yml           # Container orchestration
├── digest.txt                   # Project summary
└── README.md                    # This file
```

## 🔄 Data Flow

### Chat Query Processing
```
1. User asks compliance question in frontend
        ↓
2. Frontend → Backend /api/chat/message
        ↓
3. Backend retrieves session & drawing data from Redis
        ↓
4. Backend → Agent /process (with query + drawing JSON)
        ↓
5. Agent runs LangGraph workflow:
   ├─ Retrieve regulations from ChromaDB
   ├─ Analyze geometry from drawing JSON
   ├─ Reason with LLM (GPT-4)
   ├─ Critique response quality
   └─ Generate structured response
        ↓
6. Agent → Backend → Frontend
        ↓
7. Display answer + citations + reasoning steps
```

### Drawing Upload Flow
```
1. User pastes JSON in editor
        ↓
2. Frontend validates schema
        ↓
3. Frontend → Backend /api/session/update-ephemeral
        ↓
4. Backend validates with Pydantic
        ↓
5. Backend → Redis (key: session:{session_id}:drawing, TTL: 3600s)
        ↓
6. Redis stores ephemeral data
        ↓
7. Backend → Frontend (success + metadata)
```

### PDF Ingestion Flow
```
1. Run: docker-compose run --rm agent python ingest_pdf.py /pdfs/doc.pdf
        ↓
2. unstructured library parses PDF (hi_res strategy)
        ↓
3. Extract text, tables, headings with metadata
        ↓
4. Parent Document Retriever chunks:
   ├─ Parent chunks: 2000 chars (context)
   └─ Child chunks: 400 chars (search)
        ↓
5. Generate embeddings (OpenAI text-embedding-ada-002)
        ↓
6. Store in ChromaDB with metadata
        ↓
7. Persistent storage in Docker volume chroma_data
```

## 📄 Data Ingestion

### Adding Regulatory PDFs

The system uses hierarchical chunking for optimal retrieval:
- **Parent chunks**: 2000 characters - preserves document context
- **Child chunks**: 400 characters - precise semantic matching
- **Overlap**: 100 characters - maintains continuity
- **Table preservation**: Tables stored with HTML/Markdown formatting

#### Ingest Single PDF
```bash
docker-compose run --rm agent python ingest_pdf.py /pdfs/document.pdf
```

#### Ingest Entire Directory
```bash
docker-compose run --rm agent python ingest_pdf.py /pdfs
```

#### Ingestion Features
- ✅ Advanced PDF parsing with `unstructured` library
- ✅ Table extraction with structure preservation
- ✅ Multi-column document support
- ✅ Automatic metadata tagging
- ✅ Element type classification (title, text, table)
- ✅ Page number tracking
- ✅ Hierarchical chunking strategy
- ✅ Verification queries after ingestion
See [agent/README.md](agent/README.md) for detailed ingestion documentation.


## 🌐 API Endpoints

### Backend API (http://localhost:8000)

#### Authentication
- `POST /login` - Get JWT access token

#### Session Management (requires JWT)
- `POST /api/session/create` - Create new session
- `GET /api/session/{session_id}` - Get session details
- `POST /api/session/update-ephemeral` - Update drawing data
- `DELETE /api/session/{session_id}` - Delete session

#### Chat (requires JWT)
- `POST /api/chat/message` - Send compliance query
- `GET /api/chat/history/{session_id}` - Get conversation history

#### Drawing Management (requires JWT)
- `POST /upload_drawing` - Upload architectural drawing
- `GET /get_drawing` - Get user's drawing
- `DELETE /delete_drawing` - Delete user's drawing

#### Health
- `GET /health` - Health check with Redis status
- `GET /` - API information

### Agent API (Internal - http://agent:8001)
- `POST /process` - Process query with LangGraph workflow

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional - JWT Authentication
SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional - LangChain Tracing
LANGCHAIN_API_KEY=your-langchain-key
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=hybrid-rag

# Optional - Service Configuration (Docker defaults)
CHROMA_HOST=chromadb
CHROMA_PORT=8000
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
AGENT_HOST=agent
AGENT_PORT=8001
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### Demo Users (for testing JWT auth)
```
Username: testuser | Password: secret  | User ID: user_123
Username: demo     | Password: demo123 | User ID: user_456
```



#### 6. **Scaling Strategy**
```
Frontend:   3+ replicas behind CDN
Backend:    5+ replicas with load balancer
Agent:      3+ replicas with load balancer
ChromaDB:   Managed service or replicated setup
Redis:      Cluster with 3+ master nodes
```

## 📚 Additional Documentation

- **[Agent Documentation](agent/README.md)** - LangGraph workflow, geometry tools, PDF ingestion
- **[Backend Documentation](backend/README.md)** - API endpoints, authentication, Redis storage
- **[Frontend Documentation](frontend/README.md)** - React components, UI features, styling
- **[Tests Documentation](tests/README.md)** - Test suites, fixtures, running tests


## 📝 License

This project is part of the AICI Challenge submission.