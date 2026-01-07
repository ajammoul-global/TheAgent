"""
Health and Statistics Endpoints
System health and statistics monitoring
"""
from fastapi import APIRouter, Depends
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from FastApi.schemas.schemas import StatsResponse
from FastApi.core.security import verify_api_key
from FastApi.services.agent_manager import agent_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats", response_model=StatsResponse, status_code=200)
async def get_system_stats(
    api_env: str = Depends(verify_api_key)
):
    """
    Get system statistics
    
    Returns:
    - Memory statistics (total conversations, date ranges, etc.)
    - Available tools and count
    - Active sessions count
    
    Requires authentication.
    """
    try:
        stats = agent_manager.get_stats()
        return stats
    
    except Exception as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        return {
            "error": str(e),
            "memory": {},
            "tools": {},
            "sessions": {}
        }