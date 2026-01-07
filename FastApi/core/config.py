"""
Configuration Settings
"""
from pydantic_settings import BaseSettings
from typing import List, Any
from pydantic import field_validator
import json


class Settings(BaseSettings):
    # Settings model configuration. We allow extra env vars (so stray keys in .env
    # don't crash startup), set the env file, and keep case sensitivity.
    model_config = {
        "extra": "allow",
        "env_file": ".env",
        "case_sensitive": True,
    }
    PROJECT_NAME: str = "AI Agent API"
    DESCRIPTION: str = "AI Agent System with FastAPI"
    API_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Keep type loose so dotenv values won't be JSON-decoded by the settings source
    # (which attempts json.loads for complex types). We parse/normalize in the
    # validator below to always produce a List[str].
    ALLOWED_ORIGINS: Any = ["*"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    def _parse_allowed_origins(cls, v: Any) -> List[str]:
        """Accept JSON array, comma-separated string, or single value in env var."""
        # If already a list, return directly
        if isinstance(v, list):
            return v

        # If empty or None, keep default
        if v is None:
            return ["*"]

        if isinstance(v, str):
            v_str = v.strip()
            if not v_str:
                return ["*"]

            # Try JSON first
            try:
                parsed = json.loads(v_str)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass

            # Fallback: comma-separated
            return [item.strip() for item in v_str.split(",") if item.strip()]

        # Fallback to default
        return ["*"]
    
    API_KEY_NAME: str = "X-API-Key"
    VALID_API_KEYS: dict = {
        "dev-key-123": "development",
        "prod-key-456": "production"
    }
    
    OLLAMA_HOST: str = "http://host.docker.internal:11434"
    # Use full Ollama model identifier where possible (e.g. 'llama3.2:3b') to
    # match the model names returned by /api/tags
    OLLAMA_MODEL: str = "llama3.2:3b"
    DATABASE_PATH: str = "/app/data/conversations.db"
    LOG_LEVEL: str = "INFO"
    
    # NOTE: 'Config' inner class is intentionally omitted because pydantic v2
    # uses `model_config` at the class level. See docs for details.


settings = Settings()