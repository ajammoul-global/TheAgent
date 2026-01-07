"""
Memory Endpoints
Handle memory search and retrieval operations
"""
from fastapi import APIRouter, Depends, HTTPException
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from FastApi.schemas.schemas import SearchRequest
from FastApi.core.security import verify_api_key
from FastApi.services.agent_manager import agent_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/search", status_code=200)
async def search_memory(
    request: SearchRequest,
    api_env: str = Depends(verify_api_key)
):
    """
    Search conversation memory
    
    - **query**: Search query text
    - **limit**: Maximum results to return (1-50)
    - **agent_type**: Optional filter by agent type
    
    Returns matching conversations from memory.
    """
    try:
        logger.info(f"[{api_env}] Memory search: {request.query}")
        
        memory = agent_manager.memory_store
        
        results = memory.search(
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
        logger.error(f"Memory search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))