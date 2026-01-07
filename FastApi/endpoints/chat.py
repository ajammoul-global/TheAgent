"""
Chat Endpoints
Handle chat and conversation operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from FastApi.schemas.schemas import ChatRequest, AgentResponse, ConversationResponse
from FastApi.core.security import verify_api_key
from FastApi.services.agent_manager import agent_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=AgentResponse, status_code=200)
async def chat_with_agent(
    request: ChatRequest,
    api_env: str = Depends(verify_api_key)
):
    try:
        # 1️⃣ Enforce user identity
        session_id = request.session_id

        if not session_id:
            # Optionally derive from API key / env
            session_id = f"anon_{api_env}"

        logger.info(
            f"[{api_env}] User [{session_id}] → {request.message} "
            f"(agent: {request.agent_type})"
        )

        # 2️⃣ Always pass user-id-as-session-id
        agent = agent_manager.get_agent(
            request.agent_type,
            session_id
        )

        # 3️⃣ Run agent
        result = agent.run(request.message)

        agent_manager.memory_store.save(
            user_message=request.message,
            agent_response=result,
            session_id=session_id,          
            agent_type=request.agent_type,
            metadata={
                "api_env": api_env,
                "max_steps": request.max_steps
            }
        )
        

        return AgentResponse(
            success=True,
            result=result,
            session_id=session_id,   # ✅ user id
            agent_type=request.agent_type
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", status_code=200)
async def get_chat_history(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    api_env: str = Depends(verify_api_key)
):
    """
    Get chat history
    
    - **session_id**: Optional filter by session
    - **limit**: Maximum number of conversations to return (1-50)
    
    Returns conversation history.
    """
    try:
        memory = agent_manager.memory_store
        
        if session_id:
            conversations = memory.get_session_history(session_id, limit)
        else:
            conversations = memory.get_recent(limit)
        
        return {
            "success": True,
            "count": len(conversations),
            "conversations": conversations
        }
    
    except Exception as e:
        logger.error(f"History retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))