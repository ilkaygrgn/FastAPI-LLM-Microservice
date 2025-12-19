# 🤖 AI Agent Microservice with Next.js Frontend

A production-ready **Full-Stack AI Application** featuring a **modern conversational UI**, **autonomous agent capabilities**, **RAG (Retrieval-Augmented Generation)**, and **asynchronous background processing**. Built with a Microservices architecture using FastAPI, Next.js, and Google Gemini.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.123.5-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

### 🖥️ Modern Frontend (Next.js 14)
- **Rich User Interface**: Built with Tailwind CSS, Shadcn UI, and Lucide Icons.
- **Dark Mode Support**: Aesthetic dark/light mode toggle with OKLCH color palettes.
- **Smart Indicators**: 
  - **"Used RAG" Badge**: Only appears when the model *actually* uses retrieved context.
  - **"Agent Used" Badge**: Displays exactly which tools (e.g., Stock Price, Search) were executed.
- **Real-time Streaming**: Seamless NDJSON streaming of text and "Thought" events.
- **Interactive Chat**: Markdown rendering, code highlighting, and message history.

### 🧠 Backend & AI Agent
- **Autonomous Agent Mode**: logic to intercept LLM tool requests, execute them, and feed results back in a loop.
- **Manual Tool Control**: Fine-grained control over "Thought" emission for UI feedback.
- **Chat History**: Redis-backed session persistence for infinite-scroll context.
- **Long-term Memory**: Background tasks analyze conversation to update User Profiles.

### 📚 Advanced RAG
- **Smart Retrieval**: Context is only injected when relevant.
- **PDF Ingestion**: Drag-and-drop info extraction pipeline.
- **Vector Search**: High-performance similarity search using **PostgreSQL + pgvector**.

## 🏗️ Architecture

```mermaid
graph TD
    Client[Next.js Frontend] <-->|HTTP/Stream| API[FastAPI Gateway]
    API <-->|Auth/State| Redis[Redis (Cache/Broker)]
    API <-->|Vector Search| DB[(PostgreSQL + pgvector)]
    API -->|Async Task| Worker[Celery Worker]
    Worker -->|Update| Redis
    Worker -->|Index/Store| DB
    API <-->|GenAI| Gemini[Google Gemini API]
    Worker <-->|GenAI| Gemini
```

### Tech Stack

| Domain | Technology |
|--------|-----------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Shadcn UI, Axios |
| **Backend** | FastAPI, Uvicorn, Gunicorn, Pydantic |
| **LLM Provider** | Google Gemini (gemini-2.5-flash) |
| **Orchestration** | LangGraph, LangChain (Stateful Agent Flows) |
| **Database** | PostgreSQL 16 (Relational + Vector) |
| **Async Queue** | Celery + Redis |
| **DevOps** | Docker, Docker Compose |

## 🕹️ Agent Orchestration (LangGraph Flow)

This project leverages **LangGraph** to manage complex, stateful agentic workflows. Instead of linear RAG, we use a graph-based approach:
1.  **State Management**: The agent's conversation history and tool results are maintained in a persistent state.
2.  **Autonomous Decisions**: The LLM evaluates the state and decides whether to fetch more data (RAG), use a real-time tool (Stock API), or respond to the user.
3.  **Human-in-the-loop Ready**: The architecture is designed to support breakpoints where human intervention can be required for sensitive tool executions.

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/ilkaygrgn/FastAPI-LLM-Microservice.git
cd FastAPI-LLM-Microservice
```

### 2. Environment Setup
Create a `.env` file in the root directory:
```bash
GOOGLE_API_KEY=your_google_api_key_here
SECRET_KEY=your_secure_secret_key
DATABASE_URL=postgresql://user:password@db:5432/llm_db
REDIS_URL=redis://redis:6379/0
```

### 3. Start Application
```bash
docker-compose up --build
```

Access the services:
- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

## � Key Workflows

### 🤖 Agentic Tool Usage
1. User asks: *"What is the stock price of Google?"*
2. **Backend**: Intercepts the intent, holds the stream.
3. **Agent**: Executes `get_stock_price("GOOG")`.
4. **Stream**: Emits a `Thought` event: `🔍 Agent is executing tool: Get Stock Price...`
5. **Frontend**: Displays the specific agent badge.
6. **Final**: Model uses the tool result to generate the natural language answer.

### 📚 "Smart" RAG
1. **Upload**: User uploads a PDF via the Chat UI.
2. **Indexing**: Celery worker processes and embeds the chunks into pgvector.
3. **Query**: User asks a question with "Use RAG" toggled.
4. **Attribution**: 
   - If the answer uses the doc, the model tags it. 
   - Frontend shows a green **"Used RAG"** badge.
   - If the doc is irrelevant, no badge is shown (even if RAG mode was on).

## 🗂️ Project Structure
```
├── app/                  # FastAPI Backend
│   ├── api/v1/           # Endpoints (Auth, Chat, Users)
│   ├── core/             # Config & Security
│   ├── services/         # LLM, RAG, & Vector Logic
│   └── tools/            # Agent Tools (Stock, Search, etc.)
├── frontend/             # Next.js Frontend
│   ├── src/app/          # App Router Pages
│   ├── src/components/   # Chat & UI Components
│   └── src/lib/          # Utils & API Hooks
├── documents/            # Storage for uploaded RAG files
├── docker-compose.yml    # Orchestration
└── Dockerfile            # Backend Image
```

## � Author

**Ilkay Girgin**
- GitHub: [@ilkaygrgn](https://github.com/ilkaygrgn)


---
⭐ **Star this repo if you like modern AI architectures!**