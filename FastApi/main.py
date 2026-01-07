"""
Main FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
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
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"Python path: {sys.path}")
    raise

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


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



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "FastApi.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )