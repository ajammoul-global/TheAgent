"""
Scheduling Endpoints
Handle task scheduling operations
"""
from fastapi import APIRouter, Depends, HTTPException
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from FastApi.schemas.schemas import ScheduleRequest, AgentResponse
from FastApi.core.security import verify_api_key
from FastApi.services.agent_manager import agent_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=AgentResponse, status_code=200)
async def schedule_task(
    request: ScheduleRequest,
    api_env: str = Depends(verify_api_key)
):
    """
    Schedule a task using natural language
    
    - **text**: Natural language scheduling request (e.g., "Schedule dentist tomorrow at 10am")
    - **session_id**: Optional session ID for maintaining conversation context
    
    Returns the scheduling result with confirmation details.
    """
    try:
        logger.info(f"[{api_env}] Scheduling request: {request.text}")
        
        # Get scheduler agent
        agent = agent_manager.get_agent("scheduler", request.session_id)
        
        # Execute scheduling
        result = agent.run(request.text)
        
        # Get session ID
        session_id = request.session_id or getattr(agent, 'session_id', None)
        
        return AgentResponse(
            success=True,
            result=result,
            session_id=session_id,
            agent_type="scheduler",
            metadata={"request": request.text}
        )
    
    except Exception as e:
        logger.error(f"Scheduling error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))