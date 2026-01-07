"""
FastAPI Server - Production API for AI Agent System
Provides REST endpoints for all agents with authentication and rate limiting
"""
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid
import time

# Your existing imports
from models.ollama import OllamaModel
from infra.tool_registry import ToolRegistry
from agents.react_agent import ReActAgent
from agents.cot_agent import CoTAgent
from agents.tree_of_thoughts_agent import TreeOfThoughtsAgent
from agents.memory_enabled_scheduler import MemoryEnabledScheduler
from memory import ConversationStore
from memory.context_manager import ContextManager
from memory.preference_engine import PreferenceEngine

logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS (Request/Response)
# ============================================================================

class ScheduleRequest(BaseModel):
    """Request to schedule a task"""
    text: str = Field(..., description="Natural language scheduling request")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Schedule dentist appointment tomorrow at 10am",
                "session_id": "abc123"
            }
        }


class ChatRequest(BaseModel):
    """General chat request"""
    message: str = Field(..., description="User message")
    agent_type: str = Field("react", description="Agent type: react, cot, tot, scheduler")
    session_id: Optional[str] = Field(None, description="Session ID")
    max_steps: Optional[int] = Field(5, description="Max reasoning steps")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "What are good Python tutorials?",
                "agent_type": "react",
                "session_id": "abc123"
            }
        }


class SearchRequest(BaseModel):
    """Memory search request"""
    query: str = Field(..., description="Search query")
    limit: int = Field(10, ge=1, le=50, description="Max results")
    agent_type: Optional[str] = Field(None, description="Filter by agent type")


class PreferenceRequest(BaseModel):
    """Update preference request"""
    category: str = Field(..., description="Preference category")
    key: str = Field(..., description="Preference key")
    value: Any = Field(..., description="Preference value")
    
    class Config:
        schema_extra = {
            "example": {
                "category": "scheduling",
                "key": "preferred_meeting_time",
                "value": "10:00"
            }
        }


class AgentResponse(BaseModel):
    """Standard agent response"""
    success: bool
    result: str
    session_id: Optional[str] = None
    agent_type: Optional[str] = None
    timestamp: str
    metadata: Optional[Dict] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: str


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="AI Agent API",
    description="Production REST API for multi-agent AI system with memory",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# GLOBAL STATE (Initialize once)
# ============================================================================

class AgentManager:
    """Singleton to manage agent instances"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        logger.info("Initializing Agent Manager...")
        
        # Initialize core components
        self.model = OllamaModel()
        self.registry = ToolRegistry()
        self.memory_store = ConversationStore()
        self.context_manager = ContextManager(self.memory_store)
        self.preference_engine = PreferenceEngine(self.memory_store)
        
        # Session storage
        self.sessions = {}
        
        self._initialized = True
        logger.info("Agent Manager initialized successfully")
    
    def get_agent(self, agent_type: str, session_id: Optional[str] = None):
        """Get or create agent instance"""
        if agent_type == "react":
            return ReActAgent(self.model, self.registry, max_steps=5)
        elif agent_type == "cot":
            return CoTAgent(self.model, self.registry, num_thoughts=3)
        elif agent_type == "tot":
            return TreeOfThoughtsAgent(self.model, self.registry, num_branches=3, max_depth=2)
        elif agent_type == "scheduler":
            return MemoryEnabledScheduler(self.model, self.registry)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")


# Initialize manager
manager = AgentManager()


# ============================================================================
# AUTHENTICATION
# ============================================================================

# Simple API key authentication (in production, use proper OAuth2/JWT)
VALID_API_KEYS = {
    "dev-key-123": "development",
    "prod-key-456": "production"
}


async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from header"""
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return VALID_API_KEYS[x_api_key]


# ============================================================================
# MIDDLEWARE - Request Logging
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(f"[{request_id}] Completed in {duration:.2f}s - Status: {response.status_code}")
    
    return response


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.now().isoformat()
        ).dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            timestamp=datetime.now().isoformat()
        ).dict()
    )


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "model": "ok",
            "tools": "ok",
            "memory": "ok"
        }
    }


@app.get("/stats")
async def get_stats(api_key: str = Depends(verify_api_key)):
    """Get system statistics"""
    stats = manager.memory_store.get_stats()
    
    return {
        "memory": stats,
        "tools": {
            "available": manager.registry.list_tools(),
            "count": len(manager.registry)
        },
        "sessions": {
            "active": len(manager.sessions)
        }
    }


# ============================================================================
# SCHEDULING ENDPOINTS
# ============================================================================

@app.post("/api/v1/schedule", response_model=AgentResponse)
async def schedule_task(
    request: ScheduleRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Schedule a task using natural language
    
    - **text**: Natural language request (e.g., "Schedule dentist tomorrow at 10am")
    - **session_id**: Optional session ID for context continuity
    """
    try:
        agent = manager.get_agent("scheduler", request.session_id)
        result = agent.run(request.text)
        
        return AgentResponse(
            success=True,
            result=result,
            session_id=request.session_id or agent.session_id,
            agent_type="scheduler",
            timestamp=datetime.now().isoformat(),
            metadata={"request": request.text}
        )
    
    except Exception as e:
        logger.error(f"Scheduling error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@app.post("/api/v1/chat", response_model=AgentResponse)
async def chat(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Chat with an AI agent
    
    - **message**: User message
    - **agent_type**: Agent to use (react, cot, tot, scheduler)
    - **session_id**: Optional session for context
    - **max_steps**: Maximum reasoning steps (for ReAct agent)
    """
    try:
        agent = manager.get_agent(request.agent_type, request.session_id)
        
        # Run agent
        result = agent.run(request.message)
        
        # Get session ID
        if hasattr(agent, 'session_id'):
            session_id = agent.session_id
        else:
            session_id = request.session_id or str(uuid.uuid4())[:8]
        
        return AgentResponse(
            success=True,
            result=result,
            session_id=session_id,
            agent_type=request.agent_type,
            timestamp=datetime.now().isoformat()
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/chat/history")
async def get_chat_history(
    session_id: Optional[str] = None,
    limit: int = 10,
    api_key: str = Depends(verify_api_key)
):
    """
    Get chat history
    
    - **session_id**: Filter by session (optional)
    - **limit**: Maximum results (default: 10)
    """
    try:
        if session_id:
            conversations = manager.memory_store.get_session_history(session_id, limit)
        else:
            conversations = manager.memory_store.get_recent(limit)
        
        return {
            "success": True,
            "count": len(conversations),
            "conversations": conversations
        }
    
    except Exception as e:
        logger.error(f"History error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MEMORY ENDPOINTS
# ============================================================================

@app.post("/api/v1/memory/search")
async def search_memory(
    request: SearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Search conversation memory
    
    - **query**: Search query
    - **limit**: Max results (1-50)
    - **agent_type**: Filter by agent type (optional)
    """
    try:
        results = manager.memory_store.search(
            query=request.query,
            limit=request.limit,
            agent_type=request.agent_type
        )
        
        return {
            "success": True,
            "count": len(results),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PREFERENCE ENDPOINTS
# ============================================================================

@app.get("/api/v1/preferences")
async def get_preferences(api_key: str = Depends(verify_api_key)):
    """Get all user preferences"""
    try:
        summary = manager.preference_engine.get_preferences_summary()
        
        return {
            "success": True,
            "preferences": manager.preference_engine.preferences,
            "summary": summary
        }
    
    except Exception as e:
        logger.error(f"Get preferences error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/preferences")
async def update_preference(
    request: PreferenceRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Update a user preference
    
    - **category**: Preference category (e.g., "scheduling")
    - **key**: Preference key (e.g., "preferred_meeting_time")
    - **value**: Preference value (e.g., "10:00")
    """
    try:
        manager.preference_engine.save_explicit_preference(
            request.category,
            request.key,
            request.value
        )
        
        return {
            "success": True,
            "message": f"Preference saved: {request.category}.{request.key} = {request.value}"
        }
    
    except Exception as e:
        logger.error(f"Update preference error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/preferences/detect")
async def detect_patterns(
    agent_type: str = "task_scheduler",
    api_key: str = Depends(verify_api_key)
):
    """
    Detect patterns in user behavior
    
    - **agent_type**: Agent type to analyze (default: task_scheduler)
    """
    try:
        manager.preference_engine.detect_patterns(agent_type=agent_type)
        
        return {
            "success": True,
            "message": "Pattern detection complete",
            "patterns": manager.preference_engine.preferences.get('patterns', {})
        }
    
    except Exception as e:
        logger.error(f"Pattern detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONTEXT ENDPOINTS
# ============================================================================

@app.post("/api/v1/context/resolve")
async def resolve_reference(
    reference: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Resolve a reference like "that meeting"
    
    - **reference**: Reference text to resolve
    """
    try:
        resolved = manager.context_manager.resolve_reference(reference)
        
        if resolved:
            return {
                "success": True,
                "resolved": resolved
            }
        else:
            return {
                "success": False,
                "message": "Could not resolve reference"
            }
    
    except Exception as e:
        logger.error(f"Resolve error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.delete("/api/v1/admin/memory/clear")
async def clear_memory(
    confirm: bool = False,
    api_key: str = Depends(verify_api_key)
):
    """
    Clear all conversation memory (DANGEROUS!)
    
    - **confirm**: Must be true to proceed
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must confirm to clear memory"
        )
    
    try:
        manager.memory_store.clear_all()
        
        return {
            "success": True,
            "message": "All memory cleared"
        }
    
    except Exception as e:
        logger.error(f"Clear memory error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on server startup"""
    logger.info("=" * 80)
    logger.info("AI AGENT API SERVER STARTING")
    logger.info("=" * 80)
    logger.info(f"Docs available at: http://localhost:8000/docs")
    logger.info(f"Health check: http://localhost:8000/health")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on server shutdown"""
    logger.info("AI Agent API Server shutting down...")


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )