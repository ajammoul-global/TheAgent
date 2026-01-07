"""
Pydantic Schemas
Request and response models for API validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# SCHEDULING SCHEMAS
# ============================================================================

class ScheduleRequest(BaseModel):
    """Request to schedule a task"""
    text: str = Field(..., description="Natural language scheduling request", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for context continuity")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Schedule dentist appointment tomorrow at 10am",
                "session_id": "user123"
            }
        }
    }


# ============================================================================
# CHAT SCHEMAS
# ============================================================================

class ChatRequest(BaseModel):
    """General chat request"""
    message: str = Field(..., description="User message", min_length=1)
    agent_type: str = Field("react", description="Agent type: react, cot, tot, scheduler")
    session_id: Optional[str] = Field(None, description="Optional session ID for context")
    max_steps: Optional[int] = Field(5, ge=1, le=10, description="Maximum reasoning steps")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "What are good Python tutorials?",
                "agent_type": "react",
                "session_id": "user123"
            }
        }
    }


# ============================================================================
# MEMORY SCHEMAS
# ============================================================================

class SearchRequest(BaseModel):
    """Memory search request"""
    query: str = Field(..., description="Search query", min_length=1)
    limit: int = Field(10, ge=1, le=50, description="Maximum results to return")
    agent_type: Optional[str] = Field(None, description="Filter by agent type")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "dentist appointment",
                "limit": 10,
                "agent_type": "scheduler"
            }
        }
    }


class ConversationResponse(BaseModel):
    """Single conversation from memory"""
    id: int
    user_message: str
    agent_response: str
    agent_type: Optional[str]
    timestamp: str
    session_id: Optional[str]
    metadata: Optional[Dict[str, Any]]


# ============================================================================
# PREFERENCE SCHEMAS
# ============================================================================

class PreferenceRequest(BaseModel):
    """Update preference request"""
    category: str = Field(..., description="Preference category (e.g., 'scheduling')")
    key: str = Field(..., description="Preference key (e.g., 'preferred_meeting_time')")
    value: Any = Field(..., description="Preference value")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "category": "scheduling",
                "key": "preferred_meeting_time",
                "value": "10:00"
            }
        }
    }


class PreferenceResponse(BaseModel):
    """Preference response"""
    preferences: Dict[str, Any]
    summary: str


# ============================================================================
# CONTEXT SCHEMAS
# ============================================================================

class ReferenceResolveRequest(BaseModel):
    """Request to resolve a reference"""
    reference: str = Field(..., description="Reference text like 'that meeting'", min_length=1)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "reference": "that meeting"
            }
        }
    }


class ResolvedReference(BaseModel):
    """Resolved reference result"""
    conversation_id: int
    entity_type: str
    metadata: Dict[str, Any]
    original_message: str
    timestamp: str


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class AgentResponse(BaseModel):
    """Standard agent response"""
    success: bool
    result: str
    session_id: Optional[str] = None
    agent_type: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str


class StatsResponse(BaseModel):
    """System statistics response"""
    memory: Dict[str, Any]
    tools: Dict[str, Any]
    sessions: Dict[str, int]