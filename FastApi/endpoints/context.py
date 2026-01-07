"""
Context Endpoints
Handle context awareness and reference resolution
"""
from fastapi import APIRouter, Depends, HTTPException, Query
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from FastApi.schemas.schemas import ReferenceResolveRequest, ResolvedReference
from FastApi.core.security import verify_api_key
from FastApi.services.agent_manager import agent_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/resolve", status_code=200)
async def resolve_reference(
    reference: str = Query(..., description="Reference text to resolve (e.g., 'that meeting')"),
    api_env: str = Depends(verify_api_key)
):
    """
    Resolve a reference like "that meeting", "the appointment", etc.
    
    - **reference**: The reference text to resolve
    
    Returns the resolved entity with metadata if found.
    """
    try:
        logger.info(f"[{api_env}] Resolving reference: {reference}")
        
        context_mgr = agent_manager.context_manager
        
        resolved = context_mgr.resolve_reference(reference)
        
        if resolved:
            return {
                "success": True,
                "resolved": resolved
            }
        else:
            return {
                "success": False,
                "message": f"Could not resolve reference: {reference}"
            }
    
    except Exception as e:
        logger.error(f"Reference resolution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))