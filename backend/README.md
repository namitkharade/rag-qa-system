# Backend - FastAPI REST API

RESTful API server for session management, authentication, and routing.

## Overview

The backend serves as the central API gateway for the Hybrid RAG System, handling:
- **Session Management**: Create, update, and delete user sessions
- **Authentication**: JWT-based secure authentication with IDOR protection
- **Data Storage**: Redis-backed ephemeral data storage with TTL
- **Request Routing**: Proxy requests to the LangGraph agent service
- **Drawing Validation**: Strict JSON schema validation for architectural drawings

## Core Features

### 1. Session Management
- **Create Sessions**: Generate unique session IDs with metadata
- **Session Persistence**: Store session data in Redis with 1-hour TTL
- **Session Lifecycle**: Full CRUD operations for managing sessions
- **Drawing Association**: Link ephemeral architectural drawings to sessions

### 2. JWT Authentication System
Comprehensive JWT authentication protecting all sensitive endpoints from IDOR attacks.

#### Authentication Features:
- **Password Hashing**: Bcrypt-based secure password storage
- **JWT Token Generation**: HS256 algorithm with configurable expiration (30 minutes default)
- **OAuth2 Bearer Flow**: Standard OAuth2 password flow implementation
- **User Validation**: Middleware dependency injection for authenticated requests
- **IDOR Prevention**: User IDs extracted from cryptographically signed tokens

#### Demo Users:
```
Username: testuser | Password: secret  | User ID: user_123
Username: demo     | Password: demo123 | User ID: user_456
```

#### Security Configuration:
- **Token Expiration**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Secret Key**: Configurable via `SECRET_KEY` environment variable
- **Algorithm**: HS256 (production should use RS256 with public/private keys)

### 3. Redis Integration
- **Connection Management**: Singleton Redis client with health checks
- **TTL Management**: Automatic expiration for ephemeral data (3600 seconds)
- **Key Pattern**: `session:{user_id}:drawing` for user-specific data
- **Ping Health Check**: Real-time connection status monitoring

### 4. Data Validation
Strict Pydantic schema validation for architectural drawings:
- **LINE Objects**: Start/end points with coordinate validation
- **POLYLINE Objects**: Multi-point geometries with closed/open flag
- **Layer Validation**: Enforcement of layer naming conventions
- **Coordinate Precision**: High-precision float support for CAD coordinates
- **Metadata Extraction**: Automatic statistics (object counts, layer types)

### 5. CORS Configuration
- **Allowed Origins**: http://localhost:3000 (frontend)
- **Credentials**: Enabled for cookie-based authentication
- **Methods**: All HTTP methods supported
- **Headers**: All headers allowed for flexibility

## API Endpoints

### Authentication
#### `POST /login`
OAuth2-compatible token login endpoint.

**Request** (form data):
```
username: string
password: string
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/login \
  -d "username=testuser&password=secret"
```

### Session Management
All endpoints require JWT authentication via Bearer token.

#### `POST /api/session/create`
Create a new session with unique ID.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "session_id": "uuid-string",
  "session_name": "Session 2026-01-21T10:30:00",
  "created_at": "2026-01-21T10:30:00Z",
  "user_id": "user_123"
}
```

#### `GET /api/session/{session_id}`
Retrieve session details including associated drawing data.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "session_id": "uuid-string",
  "session_name": "Session 2026-01-21T10:30:00",
  "ephemeral_data": [...],
  "created_at": "2026-01-21T10:30:00Z"
}
```

#### `POST /api/session/update-ephemeral`
Update ephemeral architectural drawing data for a session.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "session_id": "uuid-string",
  "drawing_data": [
    {
      "type": "LINE",
      "layer": "Walls",
      "start": [0.0, 0.0],
      "end": [100.0, 0.0]
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "message": "Ephemeral data updated",
  "ttl_seconds": 3600,
  "metadata": {
    "total_objects": 1,
    "line_count": 1,
    "polyline_count": 0,
    "layers": ["Walls"]
  }
}
```

#### `DELETE /api/session/{session_id}`
Delete a session and associated ephemeral data.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "success": true,
  "message": "Session deleted"
}
```

### Chat
#### `POST /api/chat/message`
Send a message to the AI agent for compliance checking.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "session_id": "uuid-string",
  "message": "Does this building comply with the 2m boundary rule?"
}
```

**Response**:
```json
{
  "answer": "Based on the analysis...",
  "is_compliant": true,
  "citations": [
    {
      "source": "PDR Technical Guidance",
      "reference": "Section 2.1",
      "content": "Extensions must maintain 2m from boundaries",
      "relevance": "Defines the 2m boundary requirement"
    }
  ],
  "reasoning_steps": [
    "Retrieved regulatory documents",
    "Analyzed drawing geometry",
    "Calculated distances"
  ]
}
```

#### `GET /api/chat/history/{session_id}`
Retrieve conversation history for a session.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "session_id": "uuid-string",
  "messages": [
    {
      "role": "user",
      "content": "Does this comply?",
      "timestamp": "2026-01-21T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Yes, it complies because...",
      "timestamp": "2026-01-21T10:30:05Z"
    }
  ]
}
```

### Drawing Management (Authenticated)
User-specific drawing endpoints that prevent IDOR attacks.

#### `POST /upload_drawing`
Upload architectural drawing data for authenticated user.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "drawing": [
    {"type": "LINE", "layer": "Walls", "start": [0, 0], "end": [10, 0]}
  ]
}
```

**Response**:
```json
{
  "success": true,
  "message": "Drawing uploaded successfully",
  "user_id": "user_123",
  "metadata": {
    "total_objects": 1,
    "line_count": 1,
    "polyline_count": 0
  },
  "ttl_seconds": 3600
}
```

#### `GET /get_drawing`
Retrieve drawing data for authenticated user only.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "user_id": "user_123",
  "drawing": [...],
  "metadata": {...}
}
```

#### `DELETE /delete_drawing`
Delete drawing data for authenticated user.

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "success": true,
  "message": "Drawing deleted"
}
```

### Agent Proxy
#### `POST /api/agent/query`
Direct proxy to agent service (internal use).

**Request Body**:
```json
{
  "query": "Does this comply with regulations?",
  "session_id": "uuid-string",
  "ephemeral_data": [...]
}
```

### Health & Status
#### `GET /`
Root endpoint with API information.

**Response**:
```json
{
  "message": "Hybrid RAG API",
  "version": "1.0.0",
  "status": "running"
}
```

#### `GET /health`
Health check with Redis connection status.

**Response**:
```json
{
  "status": "healthy",
  "redis": "connected"
}
```

## Architecture & Components

### Directory Structure
```
backend/
├── app/
│   ├── __init__.py           # FastAPI application initialization
│   ├── main.py               # Main application with routes
│   ├── config.py             # Configuration and environment variables
│   ├── auth.py               # JWT authentication system
│   ├── models.py             # SQLAlchemy models (if using DB)
│   ├── redis_client.py       # Redis connection manager
│   ├── session_manager.py    # Session lifecycle management
│   └── routers/
│       ├── __init__.py
│       ├── agent.py          # Agent proxy routes
│       ├── chat.py           # Chat endpoints
│       └── session.py        # Session management routes
├── schemas.py                # Pydantic validation schemas
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container image definition
└── README.md                 # This file
```

### Key Components

#### 1. Authentication Module (`app/auth.py`)
- Password hashing with bcrypt
- JWT token generation and validation
- OAuth2 bearer token scheme
- User authentication and authorization
- Dependency injection for protected routes

#### 2. Redis Client (`app/redis_client.py`)
- Singleton connection pattern
- Automatic reconnection
- Health check monitoring
- TTL-based data expiration
- Context manager support

#### 3. Session Manager (`app/session_manager.py`)
- Session creation with UUID generation
- Session metadata storage
- Drawing data association
- Session cleanup and expiration

#### 4. Request Schemas (`schemas.py`)
- `LineObject`: LINE geometry validation
- `PolylineObject`: POLYLINE geometry validation
- `Point`: Coordinate validation
- Drawing metadata extraction
- Comprehensive validation rules

#### 5. Routers
- **Agent Router**: Proxy to LangGraph service
- **Chat Router**: Message handling and history
- **Session Router**: Session CRUD operations

## Running Locally

### Prerequisites
- Python 3.11+
- Redis server running on localhost:6379
- OpenAI API key

### Setup & Run
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=sk-your-key-here
export SECRET_KEY=your-secret-key-here  # Optional, has default

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker
```bash
docker build -t hybrid-rag-backend .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  -e REDIS_HOST=redis \
  hybrid-rag-backend
```

## Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional (with defaults)
SECRET_KEY=your-secret-key            # JWT secret
REDIS_HOST=localhost                   # Redis server host
REDIS_PORT=6379                        # Redis server port
REDIS_DB=0                             # Redis database number
BACKEND_HOST=0.0.0.0                   # Server bind host
BACKEND_PORT=8000                      # Server bind port
AGENT_HOST=localhost                   # Agent service host
AGENT_PORT=8001                        # Agent service port
```

### Security Best Practices
1. **Change SECRET_KEY**: Generate with `openssl rand -hex 32`
2. **Use RS256 in Production**: Switch from HS256 to RS256 with key pairs
3. **HTTPS Only**: Always use HTTPS in production
4. **Rotate Tokens**: Implement refresh token mechanism
5. **Rate Limiting**: Add rate limiting for authentication endpoints
6. **Database Backend**: Replace fake_users_db with real database

## API Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Dependencies

Key Python packages:
- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **pydantic**: Data validation
- **redis**: Redis client
- **python-jose**: JWT token handling
- **passlib**: Password hashing
- **bcrypt**: Bcrypt algorithm for passwords
- **httpx**: HTTP client for agent proxy

See [requirements.txt](requirements.txt) for complete list.
