"""
Preference Endpoints
Handle user preference management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from FastApi.schemas.schemas import PreferenceRequest, PreferenceResponse
from FastApi.core.security import verify_api_key
from FastApi.services.agent_manager import agent_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=PreferenceResponse, status_code=200)
async def get_preferences(
    api_env: str = Depends(verify_api_key)
):
    """
    Get all user preferences
    
    Returns:
    - All stored preferences (explicit and learned patterns)
    - Human-readable summary
    """
    try:
        prefs = agent_manager.preference_engine
        
        summary = prefs.get_preferences_summary()
        
        return PreferenceResponse(
            preferences=prefs.preferences,
            summary=summary
        )
    
    except Exception as e:
        logger.error(f"Get preferences error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("", status_code=200)
async def update_preference(
    request: PreferenceRequest,
    api_env: str = Depends(verify_api_key)
):
    """
    Update a user preference
    
    - **category**: Preference category (e.g., "scheduling", "communication")
    - **key**: Preference key (e.g., "preferred_meeting_time")
    - **value**: Preference value (any type)
    
    Saves the preference for future use.
    """
    try:
        logger.info(f"[{api_env}] Setting preference: {request.category}.{request.key} = {request.value}")
        
        prefs = agent_manager.preference_engine
        
        prefs.save_explicit_preference(
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


@router.post("/detect", status_code=200)
async def detect_patterns(
    agent_type: str = Query("task_scheduler", description="Agent type to analyze"),
    api_env: str = Depends(verify_api_key)
):
    """
    Detect patterns in user behavior
    
    - **agent_type**: Which agent's interactions to analyze (default: task_scheduler)
    
    Analyzes past interactions to learn implicit preferences.
    """
    try:
        logger.info(f"[{api_env}] Detecting patterns for: {agent_type}")
        
        prefs = agent_manager.preference_engine
        
        prefs.detect_patterns(agent_type=agent_type)
        
        return {
            "success": True,
            "message": "Pattern detection complete",
            "patterns": prefs.preferences.get('patterns', {})
        }
    
    except Exception as e:
        logger.error(f"Pattern detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))