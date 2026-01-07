# 🤖 AI Agent API - Production-Grade Agentic AI System

A comprehensive, production-ready agentic AI system built with FastAPI, featuring multiple reasoning patterns, memory management, tool integration, and scheduling capabilities.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Development](#development)
- [Deployment](#deployment)
- [API Endpoints](#api-endpoints)
- [Tools & Capabilities](#tools--capabilities)
- [Contributing](#contributing)

---

## 🎯 Overview

This project implements a sophisticated agentic AI system that demonstrates:

- **Multiple Reasoning Patterns**: ReAct, Chain-of-Thought (CoT), Tree-of-Thoughts (ToT)
- **Advanced Memory Systems**: Conversation storage, semantic memory, preference management
- **Tool Integration**: Web search, Google Calendar, extensible tool registry
- **API-First Design**: Production-grade FastAPI server with authentication
- **Docker Support**: Containerized deployment with Ollama integration
- **Comprehensive Testing**: Unit tests for all major components

### Use Cases

- Autonomous task scheduling and planning
- Research and information gathering
- Context-aware conversational AI
- Multi-step problem solving
- Calendar and meeting management

---

## ✨ Features

### Core Agent Types

| Agent | Description |
|-------|-------------|
| **Simple Agent** | Basic request-response agent |
| **ReAct Agent** | Reasoning + Acting loop |
| **CoT Agent** | Chain-of-Thought reasoning |
| **ToT Agent** | Tree-of-Thoughts exploration |
| **Memory Agent** | Persistent memory with context |

### Memory Systems

- **Conversation Store**: SQLite-based conversation history
- **Vector Store**: Semantic memory with embeddings
- **Preference Engine**: User preferences and configuration
- **Context Manager**: Dynamic context window management

### Tools

- 🔍 **Web Search**: DuckDuckGo integration (no API key needed)
- 📅 **Google Calendar**: Create and manage calendar events
- 🔗 **Extensible Registry**: Add custom tools easily

---

## 🏗️ Architecture

```
AI Agent API
├── Agents Layer
│   ├── Simple Agent
│   ├── ReAct Agent
│   ├── CoT Agent (Chain-of-Thought)
│   ├── ToT Agent (Tree-of-Thoughts)
│   └── Memory Agent
│
├── FastAPI Server
│   ├── Chat Endpoint
│   ├── Scheduling Endpoint
│   ├── Memory Management
│   ├── Preferences
│   ├── Context Management
│   └── Health Checks
│
├── Memory Systems
│   ├── Conversation Store
│   ├── Vector Store (Semantic)
│   ├── Preference Engine
│   └── Context Manager
│
├── Tools & Services
│   ├── Web Search (DuckDuckGo)
│   ├── Google Calendar
│   ├── Tool Registry
│   └── Agent Manager
│
└── Infrastructure
    ├── Configuration
    ├── Logging
    ├── Security (API Key Auth)
    └── CORS Middleware
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **Docker & Docker Compose** (optional, for containerized setup)
- **Ollama** (for local LLM) - [Install Ollama](https://ollama.ai)

### Option 1: Docker (Recommended)

1. **Start Ollama** (if running locally):
   ```bash
   ollama serve
   ```

2. **Build and run with Docker Compose**:
   ```bash
   docker compose up --build
   ```

3. **Access the API**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health
### Option 2: Local Development

1. **Clone and setup**:
   ```bash
   cd c:\Users\lenovo\Desktop\agent
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env  # Create from template
   # Edit .env with your settings
   ```

4. **Start Ollama**:
   ```bash
   ollama serve
   ```

5. **Run the server**:
   ```bash
   python -m uvicorn FastApi.main:app --reload
   ```

6. **Access Swagger UI**:
   - http://localhost:8000/docs

---

## 📖 API Documentation

### Interactive Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs (Interactive testing)
- **ReDoc**: http://localhost:8000/redoc (Clean documentation)

### Authentication

All endpoints (except `/health`) require API Key authentication:

**Header**: `X-API-Key`

**Available Keys**:
- Development: `dev-key-123`
- Production: `prod-key-456`

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2+2?", "session_id": "user123"}'
```

---

## 📁 Project Structure

```
agent/
├── agents/                      # Agent implementations
│   ├── simple_agent.py         # Basic agent
│   ├── react_agent.py          # ReAct pattern
│   ├── cot_agent.py            # Chain-of-Thought
│   ├── tot_agent.py            # Tree-of-Thoughts
│   └── memory_agent.py         # Memory-enabled agent
│
├── FastApi/                     # FastAPI application
│   ├── main.py                 # Application entry point
│   ├── Api_server.py           # Server configuration
│   ├── core/
│   │   ├── config.py           # Settings & configuration
│   │   ├── security.py         # API key verification
│   │   ├── logging_config.py   # Logging setup
│   │   └── ...
│   ├── endpoints/              # API route handlers
│   │   ├── chat.py             # Chat messages
│   │   ├── scheduling.py       # Task scheduling
│   │   ├── memory.py           # Memory operations
│   │   ├── preferences.py      # User preferences
│   │   ├── context.py          # Context management
│   │   └── healthy.py          # Health checks
│   ├── schemas/
│   │   └── schemas.py          # Pydantic models
│   └── services/
│       └── agent_manager.py    # Agent orchestration
│
├── memory/                      # Memory systems
│   ├── conversation_store.py   # Conversation history
│   ├── vector_store.py         # Semantic memory
│   ├── preference_engine.py    # User preferences
│   └── context_manager.py      # Context management
│
├── tools/                       # Tool implementations
│   ├── base.py                 # Base tool class
│   ├── web_search.py           # DuckDuckGo search
│   ├── google_calendar_*.py    # Calendar tools
│   ├── google_auth.py          # OAuth setup
│   └── __init__.py
│
├── models/                      # LLM model wrappers
│   ├── base.py                 # Base model class
│   └── ollama.py               # Ollama implementation
│
├── infra/                       # Infrastructure
│   ├── config.py               # Infra config
│   ├── logging.py              # Logger setup
│   ├── tool_registry.py        # Tool registry
│   └── ...
│
├── promt/                       # Prompt management
│   ├── Prompt_template.py      # Prompt templates
│   ├── Promt_library.py        # Prompt library
│   └── promt_manager           # Prompt manager
│
├── demo/                        # Demo scripts
│   ├── demo_react.py           # ReAct demo
│   ├── demo_cot.py             # CoT demo
│   ├── demo_tot.py             # ToT demo
│   ├── demo_memory.py          # Memory demo
│   └── ...
│
├── tests/                       # Test suite
│   ├── test_*.py               # Test files
│   └── __init__.py
│
├── docker-compose.yml          # Docker configuration
├── Dockerfile                  # Container definition
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── README.md                   # This file
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# Application
PROJECT_NAME=AI Agent API
ENVIRONMENT=development
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# Ollama
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:3b

# Database
DATABASE_PATH=/app/data/conversations.db

# Logging
LOG_LEVEL=INFO

# CORS
ALLOWED_ORIGINS=*

# API Keys (set in core/config.py)
# Development: dev-key-123
# Production: prod-key-456
```

### Core Configuration (FastApi/core/config.py)

```python
API_KEY_NAME: str = "X-API-Key"
VALID_API_KEYS: dict = {
    "dev-key-123": "development",
    "prod-key-456": "production"
}
```

---

## 🛠️ Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_react.py -v

# Run with coverage
pytest --cov=.
```

### Running Demos

```bash
# ReAct agent demo
python -m demo.demo_react

# Chain-of-Thought demo
python -m demo.demo_cot

# Tree-of-Thoughts demo
python -m demo.demo_tot

# Memory agent demo
python -m demo.demo_memory
```

### Adding Custom Tools

1. Create a new tool in `tools/my_tool.py`:

```python
from tools.base import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "What this tool does"
    
    def execute(self, **kwargs):
        # Implementation
        return result
```

2. Register in `infra/tool_registry.py`:

```python
registry.register(MyTool())
```

---

## 📦 Deployment

### Docker Deployment

1. **Build image**:
   ```bash
   docker build -t ai-agent-api:latest .
   ```

2. **Run container**:
   ```bash
   docker run -p 8000:8000 \
     -e OLLAMA_HOST=http://host.docker.internal:11434 \
     -e ENVIRONMENT=production \
     ai-agent-api:latest
   ```

3. **With Docker Compose**:
   ```bash
   docker compose up -d
   ```

### Production Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Update `VALID_API_KEYS` with secure keys
- [ ] Configure `ALLOWED_ORIGINS` for CORS
- [ ] Set up persistent volumes for database
- [ ] Enable HTTPS/SSL
- [ ] Configure logging aggregation
- [ ] Set up monitoring and alerting
- [ ] Test health checks
- [ ] Configure rate limiting

---

## 🔌 API Endpoints

### Health Check
```
GET /api/v1/health
```
No authentication required.

### Chat
```
POST /api/v1/chat/message
```
Send a message and get agent response.

**Request**:
```json
{
  "message": "What is the weather like?",
  "session_id": "user123",
  "agent_type": "react"
}
```

**Response**:
```json
{
  "response": "Agent response here...",
  "session_id": "user123",
  "timestamp": "2026-01-07T10:30:00Z"
}
```

### Scheduling
```
POST /api/v1/schedule/create
GET /api/v1/schedule/list
```
Create and manage scheduled tasks.

### Memory
```
GET /api/v1/memory/retrieve
POST /api/v1/memory/store
```
Access and manage conversation memory.

### Preferences
```
GET /api/v1/preferences/get
POST /api/v1/preferences/set
```
Manage user preferences.

### Context
```
GET /api/v1/context/get
POST /api/v1/context/update
```
Manage conversation context.

---

## 🧠 Tools & Capabilities

### Web Search
Powered by DuckDuckGo (no API key required)
- Real-time search results
- News, images, and general web search
- No rate limiting concerns

### Google Calendar
Create and manage calendar events
- Requires OAuth authentication
- Create events, list calendar, manage invitations

### Extensible Tool System
- Register custom tools easily
- Tool composition (tools using tools)
- Parallel tool execution
- Error handling and retries

---

## 📊 Agent Types Explained

### Simple Agent
Basic request-response pattern. Good for straightforward queries.

### ReAct Agent (Reasoning + Acting)
Combines reasoning with tool use in a loop:
1. Thought: Agent reasons about the task
2. Action: Agent calls a tool
3. Observation: Tool result is observed
4. Repeat until solution found

### Chain-of-Thought (CoT)
Agent breaks down complex problems into steps:
1. Problem analysis
2. Intermediate steps
3. Final conclusion

### Tree-of-Thoughts (ToT)
Explores multiple reasoning paths:
1. Generate multiple solutions
2. Evaluate each path
3. Select best path
4. Explore further if needed

### Memory Agent
Maintains conversation context across interactions:
- Remembers past conversations
- Uses embeddings for semantic search
- Manages user preferences
- Updates context dynamically

---

## 🐛 Troubleshooting

### Ollama Connection Error
```
Error: Cannot connect to Ollama at http://host.docker.internal:11434
```

**Solution**:
- Ensure Ollama is running: `ollama serve`
- For Docker: Use `http://host.docker.internal:11434` on Windows/Mac
- For Linux: Use `http://localhost:11434` (Docker network)
- Check `OLLAMA_HOST` in `.env`

### API Key Authentication Failed
```
Detail: Invalid API key
```

**Solution**:
- Verify header: `X-API-Key: dev-key-123`
- Check spelling and quotes
- Ensure key exists in `FastApi/core/config.py`

### Module Import Errors
```
ModuleNotFoundError: No module named 'FastApi'
```

**Solution**:
- Ensure `PYTHONPATH` is set correctly
- Run from project root: `python -m uvicorn ...`
- Check virtual environment is activated

### Database Locked
```
sqlite3.OperationalError: database is locked
```

**Solution**:
- Close other processes accessing the database
- Delete `.db-wal` and `.db-shm` files
- Restart the application

---

## 📚 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Ollama Documentation](https://ollama.ai)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)
- [Tree of Thoughts](https://arxiv.org/abs/2305.10601)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Standards
- Follow PEP 8
- Add docstrings to all functions
- Include type hints
- Write unit tests
- Update documentation

---

## 📄 License

This project is provided as-is for educational and development purposes.

---

## 📧 Support

For issues, questions, or suggestions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [Agentic AI Roadmap](Agentic%20ai%20roadmap.md)
3. Check test files for usage examples

---

## 🎓 Roadmap

See [Agentic AI Development Roadmap](Agentic%20ai%20roadmap.md) for detailed development phases and learning objectives.

### Current Status: Phase 1-4 ✅
- [x] Foundation & Architecture
- [x] Agent Types (ReAct, CoT, ToT)
- [x] Memory Systems
- [x] Advanced Tools

### Upcoming: Phase 5-7 🚀
- [ ] Guardrails & Safety
- [ ] Production Observability
- [ ] Scalability & Performance

---

**Happy Building! 🚀**
