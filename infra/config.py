"""
Configuration Management

Centralized settings using environment variables.
"""

import os
from typing import Optional


class Settings:
    """Application settings - simple class approach"""
    
    def __init__(self):
        # LLM Configuration
        self.ollama_host = os.getenv(
            "OLLAMA_HOST",
            "http://host.docker.internal:11434" if os.path.exists("/.dockerenv")
            else "http://localhost:11434"
        )
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("MAX_TOKENS")) if os.getenv("MAX_TOKENS") else None
        
        # Agent Configuration
        self.max_iterations = int(os.getenv("MAX_ITERATIONS", "10"))
        self.agent_timeout = int(os.getenv("AGENT_TIMEOUT", "300"))
        
        # Tool Configuration
        self.enable_web_search = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"
        self.enable_tasks = os.getenv("ENABLE_TASKS", "true").lower() == "true"
        self.enable_calendar = os.getenv("ENABLE_CALENDAR", "true").lower() == "true"
        
        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_to_file = os.getenv("LOG_TO_FILE", "false").lower() == "true"
        self.log_file_path = os.getenv("LOG_FILE_PATH", "logs/agent.log")
        
        # Database Configuration (future)
        self.database_url = os.getenv("DATABASE_URL")
        self.redis_url = os.getenv("REDIS_URL")
        
        # API Configuration (future)
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
    
    def to_dict(self):
        """Convert settings to dictionary"""
        return {
            "ollama_host": self.ollama_host,
            "ollama_model": self.ollama_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_iterations": self.max_iterations,
            "agent_timeout": self.agent_timeout,
            "enable_web_search": self.enable_web_search,
            "enable_tasks": self.enable_tasks,
            "enable_calendar": self.enable_calendar,
            "log_level": self.log_level,
            "log_to_file": self.log_to_file,
            "log_file_path": self.log_file_path,
            "database_url": "***" if self.database_url else None,
            "redis_url": "***" if self.redis_url else None,
            "api_host": self.api_host,
            "api_port": self.api_port,
        }
    
    def __repr__(self):
        return f"<Settings: {self.ollama_model} @ {self.ollama_host}>"


# Global settings instance
settings = Settings()