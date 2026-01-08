"""
Main FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
import logging
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import from your structure
try:
    from FastApi.core.config import settings
    from FastApi.core.logging_config import setup_logging
    from FastApi.endpoints.scheduling import router as scheduling_router
    from FastApi.endpoints.chat import router as chat_router
    from FastApi.endpoints.memory import router as memory_router
    from FastApi.endpoints.preferences import router as preferences_router
    from FastApi.endpoints.context import router as context_router
    from FastApi.endpoints.healthy import router as health_router
    from models.huggingface import HuggingFaceModel
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"Python path: {sys.path}")
    raise

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class NewsVerificationRequest(BaseModel):
    """Request model for news verification"""
    news: str = Field(..., description="News text to verify")
    
    class Config:
        schema_extra = {
            "example": {
                "news": "The Earth is flat"
            }
        }


class NewsVerificationResponse(BaseModel):
    """Response model for news verification"""
    news: str = Field(..., description="The original news text")
    result: str = Field(..., description="Classification result (REAL or FAKE)")
    confidence: float = Field(..., description="Confidence score (0-1)")
    
    class Config:
        schema_extra = {
            "example": {
                "news": "The Earth is flat",
                "result": "FAKE",
                "confidence": 0.95
            }
        }

# ============================================================================
# INITIALIZE MODELS
# ============================================================================

# Initialize HuggingFace classifier for news verification
# You can use different models. Some popular ones:
# - "bert-base-multilingual-uncased-sentiment"
# - "distilbert-base-uncased-finetuned-sst-2-english"
# - "facebook/bart-large-mnli" (for zero-shot classification)
try:
    hf_model = HuggingFaceModel("Ali-jammoul/fake-news-detector-3b")
    logger.info("✅ HuggingFace model loaded successfully")
except Exception as e:
    logger.warning(f"⚠️ Could not load HuggingFace model: {e}")
    hf_model = None

# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("=" * 80)
    logger.info("AI AGENT API SERVER STARTING")
    logger.info("=" * 80)
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Version: {settings.API_VERSION}")
    logger.info(f"Docs URL: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info("=" * 80)
    yield
    logger.info("AI Agent API Server shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.API_VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
API_PREFIX = "/api/v1"
app.include_router(health_router, prefix=API_PREFIX, tags=["health"])
app.include_router(scheduling_router, prefix=f"{API_PREFIX}/schedule", tags=["scheduling"])
app.include_router(chat_router, prefix=f"{API_PREFIX}/chat", tags=["chat"])
app.include_router(memory_router, prefix=f"{API_PREFIX}/memory", tags=["memory"])
app.include_router(preferences_router, prefix=f"{API_PREFIX}/preferences", tags=["preferences"])
app.include_router(context_router, prefix=f"{API_PREFIX}/context", tags=["context"])


@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.API_VERSION
    }
@app.get("/karim")
async def karim():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.API_VERSION
    }


@app.post(
    "/api/v1/verify-news",
    response_model=NewsVerificationResponse,
    summary="Verify if news is real or fake",
    tags=["news-verification"]
)
async def verify_news(request: NewsVerificationRequest):
    """
    Verify if a news article is real or fake using HuggingFace classifier.
    
    **Parameters:**
    - `news` (str): The news text to verify
    
    **Returns:**
    - `news`: Original news text
    - `result`: Classification (REAL/FAKE)
    - `confidence`: Confidence score (0-1)
    
    **Example:**
    ```json
    {
        "news": "The Earth is flat"
    }
    ```
    """
    if not hf_model:
        return {
            "error": "HuggingFace model not loaded",
            "news": request.news,
            "result": "ERROR",
            "confidence": 0.0
        }
    
    try:
        # Get classification from model
        classification_result = hf_model.generate(request.news)
        
        # Parse the result (format: "Analysis: LABEL (Confidence: 0.XX)")
        # Extract label and confidence
        result_parts = classification_result.split("(Confidence: ")
        label = result_parts[0].replace("Analysis: ", "").strip()
        confidence = float(result_parts[1].rstrip(")"))
        
        return NewsVerificationResponse(
            news=request.news,
            result=label,
            confidence=confidence
        )
    except Exception as e:
        logger.error(f"Error verifying news: {str(e)}")
        return {
            "error": str(e),
            "news": request.news,
            "result": "ERROR",
            "confidence": 0.0
        }




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "FastApi.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )