# 🤖 FastAPI LLM Microservice

A production-ready FastAPI microservice featuring **conversational AI**, **RAG (Retrieval-Augmented Generation)**, and **asynchronous background job processing**. Built with modern Python best practices and enterprise-level architecture.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.123.5-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

### Core Capabilities
- **🗨️ Conversational AI**: Multi-turn chat with streaming responses using Google Gemini
- **📚 RAG Implementation**: Document upload, chunking, vectorization, and intelligent retrieval
- **🔐 JWT Authentication**: Secure endpoints with access/refresh token mechanism
- **⚡ Async Processing**: Background tasks with Celery for document indexing and user profiling
- **📊 Vector Search**: PostgreSQL with pgvector extension for similarity search
- **🔄 Real-time Updates**: Server-Sent Events (SSE) for streaming chat responses

### Technical Highlights
- **Microservices Architecture**: Containerized services with Docker Compose
- **Persistent Session Management**: Redis-based conversation history
- **User Profiling**: Automated background analysis of user conversations
- **Document Processing**: PDF parsing, text chunking, and embedding generation
- **Production-Ready**: Gunicorn with Uvicorn workers, proper error handling

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI   │────▶│    Redis     │     │  PostgreSQL │
│   Service   │     │   (Broker)   │     │  + pgvector │
└──────┬──────┘     └──────────────┘     └──────┬──────┘
       │                    │                     │
       │            ┌───────▼────────┐           │
       └───────────▶│ Celery Worker  │───────────┘
                    └────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| **Web Framework** | FastAPI 0.123.5 |
| **LLM Provider** | Google Gemini (gemini-2.5-flash) |
| **Embeddings** | Google Generative AI Embeddings |
| **Vector Database** | PostgreSQL 16 + pgvector |
| **Message Broker** | Redis 7.2 |
| **Task Queue** | Celery 5.5.3 |
| **Authentication** | JWT (python-jose) |
| **Document Processing** | LangChain, PyPDF |
| **Containerization** | Docker + Docker Compose |

## 📋 Prerequisites

- Docker & Docker Compose
- Google AI API Key ([Get one here](https://ai.google.dev/))
- Python 3.11+ (for local development)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/ilkaygrgn/FastAPI-LLM-Microservice.git
cd FastAPI-LLM-Microservice
```

### 2. Set Environment Variables
Create a `.env` file:
```bash
GOOGLE_API_KEY=your_google_api_key_here
SECRET_KEY=your_secret_key_for_jwt
OPENAI_API_KEY=your_openai_key_optional
```

### 3. Start Services
```bash
docker-compose up -d
```

Services will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🔑 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/llm/chat` | Stream chat response with RAG |

### Document Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/llm/upload-document` | Upload PDF for RAG indexing |

### User Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get current user profile |

### Background Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/jobs/start` | Start a background task |
| GET | `/api/v1/jobs/{job_id}` | Check job status |

## 💡 Usage Examples

### 1. Register & Login
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password",
    "full_name": "John Doe"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=secure_password"
```

### 2. Upload Document for RAG
```bash
curl -X POST http://localhost:8000/api/v1/llm/upload-document \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@document.pdf"
```

### 3. Chat with RAG
```bash
curl -X POST http://localhost:8000/api/v1/llm/chat \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does the document say about...?",
    "session_id": "session_123"
  }'
```

## 🗂️ Project Structure

```
fastapi-llm-microservice/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── users.py         # User management
│   │       ├── llm.py           # Chat & document upload
│   │       └── jobs.py          # Background job management
│   ├── core/
│   │   ├── config.py            # Configuration management
│   │   └── security.py          # JWT & password hashing
│   ├── db/
│   │   ├── database.py          # Database connection
│   │   └── models.py            # SQLAlchemy models
│   ├── schemas/
│   │   ├── user.py              # User schemas
│   │   └── chat.py              # Chat request/response
│   ├── services/
│   │   ├── llm_service.py       # LLM integration & streaming
│   │   ├── vector_db_service.py # RAG & embeddings
│   │   └── chat_history.py      # Conversation persistence
│   ├── workers/
│   │   ├── worker.py            # Celery app configuration
│   │   └── tasks.py             # Background tasks
│   └── main.py                  # FastAPI application
├── docker-compose.yml           # Multi-container orchestration
├── Dockerfile                   # Application container
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI API key | Required |
| `SECRET_KEY` | JWT secret key | Required |
| `DATABASE_URL` | PostgreSQL connection string | Auto-configured in Docker |
| `REDIS_HOST` | Redis server hostname | `redis` |
| `GOOGLE_LLM_MODEL` | Gemini model name | `gemini-2.5-flash` |

### Docker Compose Services

- **api**: FastAPI application (4 Gunicorn workers)
- **worker**: Celery worker for background tasks
- **db**: PostgreSQL 16 with pgvector extension
- **redis**: Redis 7.2 for session storage & task queue

## 📊 Database Schema

### Users Table
```sql
- id: SERIAL PRIMARY KEY
- email: VARCHAR UNIQUE
- hashed_password: VARCHAR
- full_name: VARCHAR
- user_profile: TEXT (AI-generated from conversations)
- is_active: BOOLEAN
- created_at: TIMESTAMP
```

### Vector Store (pgvector)
- `langchain_pg_collection`: Document collections
- `langchain_pg_embedding`: Vector embeddings with metadata

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/
# Response: {"status":"ok","service":"FastAPI LLM Microservice"}
```

### Check Running Containers
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
```

## 🔐 Security Features

- **Password Hashing**: Bcrypt with salt
- **JWT Tokens**: Short-lived access tokens (30 min) + refresh tokens (7 days)
- **Protected Endpoints**: Bearer token authentication
- **SQL Injection Prevention**: SQLAlchemy ORM
- **CORS Configuration**: Configurable allowed origins

## 🚧 Known Limitations

- **Google API Quota**: Free tier has embedding limits (1,500 requests/day)
- **File Upload**: Currently supports PDF only
- **Streaming**: SSE may not work with some reverse proxies

## 🛣️ Roadmap

- [ ] Multi-LLM support (Claude, OpenAI, local models)
- [ ] OpenAI embeddings fallback
- [ ] Document chunking strategies (semantic, sliding window)
- [ ] Conversation summarization
- [ ] Rate limiting
- [ ] Prometheus metrics
- [ ] Kubernetes deployment configs

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Ilkay Girgin**
- GitHub: [@ilkaygrgn](https://github.com/ilkaygrgn)
- LinkedIn: [linkedin.com/in/ilkaygirgin](https://linkedin.com/in/ilkaygirgin)

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [LangChain](https://langchain.com/) - LLM application framework
- [Google AI](https://ai.google.dev/) - Gemini API
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search

---

⭐ **If you find this project useful, please consider giving it a star!**