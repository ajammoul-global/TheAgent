"""
Ollama Model Implementation

This module provides integration with Ollama's local API, allowing the agent
to generate text using locally-hosted language models like Llama, Mistral, etc.

Key Design Decisions:
- Uses /api/chat endpoint for better conversation support
- Non-streaming by default (streaming can be added later)
- Validates model availability on initialization
- Implements retry logic for transient failures
- Provides detailed error messages for debugging
"""

from typing import Dict, Any, Optional, List
import requests
import time
from requests.exceptions import RequestException, Timeout, ConnectionError

from models.base import BaseModel
from infra.config import settings
from infra.logging import logger


class OllamaError(Exception):
    """Base exception for Ollama-related errors"""
    pass


class OllamaConnectionError(OllamaError):
    """Raised when unable to connect to Ollama server"""
    pass


class OllamaModelNotFoundError(OllamaError):
    """Raised when the requested model is not available"""
    pass


class OllamaGenerationError(OllamaError):
    """Raised when text generation fails"""
    pass


class OllamaModel(BaseModel):
    """
    Ollama Model Implementation
    
    Connects to a local Ollama instance to generate text using various LLMs.
    Supports configuration through environment variables and provides robust
    error handling for production use.
    
    Attributes:
        _host: Ollama API endpoint URL
        _model_name: Name of the model to use (e.g., "llama3.1:8b")
        _timeout: Request timeout in seconds
        _max_retries: Maximum number of retry attempts
    
    Example:
        >>> model = OllamaModel()
        >>> response = model.generate("What is Python?")
        >>> print(response)
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3
    ):
        """
        Initialize Ollama model connection
        
        Args:
            host: Ollama API endpoint (defaults to settings.ollama_host)
            model_name: Model to use (defaults to settings.ollama_model)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        
        Raises:
            OllamaConnectionError: If unable to connect to Ollama
            OllamaModelNotFoundError: If specified model is not available
        """
        self._host = host or settings.ollama_host
        self._model_name = model_name or settings.ollama_model
        self._timeout = timeout
        self._max_retries = max_retries
        
        logger.info(f"Initializing OllamaModel with {self._model_name}")
        logger.debug(f"Ollama host: {self._host}")
        
        # Validate connection and model availability
        self._validate_connection()
        self._validate_model()
        
        logger.info("OllamaModel initialized successfully")
    
    def _validate_connection(self) -> None:
        """
        Validate that Ollama server is reachable
        
        Raises:
            OllamaConnectionError: If server is not reachable
        """
        try:
            logger.debug("Validating connection to Ollama server...")
            response = requests.get(
                f"{self._host}/api/tags",
                timeout=5  # Short timeout for connection check
            )
            response.raise_for_status()
            logger.debug("Connection to Ollama server validated")
            
        except ConnectionError as e:
            error_msg = (
                f"Cannot connect to Ollama at {self._host}. "
                f"Please ensure Ollama is running. Error: {str(e)}"
            )
            logger.error(error_msg)
            raise OllamaConnectionError(error_msg) from e
            
        except Timeout as e:
            error_msg = (
                f"Connection to Ollama at {self._host} timed out. "
                f"Server may be overloaded or unreachable. Error: {str(e)}"
            )
            logger.error(error_msg)
            raise OllamaConnectionError(error_msg) from e
            
        except RequestException as e:
            error_msg = f"Failed to connect to Ollama: {str(e)}"
            logger.error(error_msg)
            raise OllamaConnectionError(error_msg) from e
    
    def _validate_model(self) -> None:
        """
        Validate that the specified model is available
        
        Raises:
            OllamaModelNotFoundError: If model is not found
        """
        try:
            logger.debug(f"Validating model availability: {self._model_name}")
            response = requests.get(
                f"{self._host}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            
            available_models = response.json().get("models", [])
            model_names = [model.get("name") for model in available_models]
            
            if self._model_name not in model_names:
                error_msg = (
                    f"Model '{self._model_name}' not found. "
                    f"Available models: {', '.join(model_names)}"
                )
                logger.error(error_msg)
                raise OllamaModelNotFoundError(error_msg)
            
            logger.debug(f"Model {self._model_name} is available")
            
        except OllamaModelNotFoundError:
            raise  # Re-raise our custom exception
            
        except RequestException as e:
            # If we can't check models, log warning but don't fail
            # (server might be up but /api/tags might have issues)
            logger.warning(
                f"Could not validate model availability: {str(e)}. "
                "Proceeding anyway..."
            )
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text using Ollama
        
        This method sends a prompt to the Ollama API and returns the generated
        text. It includes retry logic for transient failures and detailed error
        handling.
        
        Args:
            prompt: The input text prompt
            temperature: Sampling temperature (0.0 to 1.0)
                - Lower values (0.0-0.3): More focused, deterministic
                - Medium values (0.4-0.7): Balanced
                - Higher values (0.8-1.0): More creative, random
            max_tokens: Maximum tokens to generate (None = model default)
        
        Returns:
            Generated text as a string
        
        Raises:
            OllamaGenerationError: If generation fails after retries
            ValueError: If parameters are invalid
        
        Example:
            >>> model = OllamaModel()
            >>> text = model.generate("Explain quantum computing", temperature=0.5)
        """
        # Validate parameters
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        if not 0.0 <= temperature <= 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        logger.info(f"Generating text with {self._model_name}")
        logger.debug(f"Prompt length: {len(prompt)} chars, temperature: {temperature}")
        
        # Build request payload
        payload = {
            "model": self._model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,  
            "options": {
                "temperature": temperature,
            }
        }
        
        # Add max_tokens if specified
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens
        
        # Attempt generation with retries
        last_error = None
        for attempt in range(1, self._max_retries + 1):
            try:
                logger.debug(f"Generation attempt {attempt}/{self._max_retries}")
                
                response = requests.post(
                    f"{self._host}/api/chat",
                    json=payload,
                    timeout=self._timeout
                )
                response.raise_for_status()
                
                # Parse response
                result = response.json()
                generated_text = result.get("message", {}).get("content", "")
                
                if not generated_text:
                    raise OllamaGenerationError("Empty response from Ollama")
                
                logger.info(f"Generated {len(generated_text)} characters")
                logger.debug(f"First 100 chars: {generated_text[:100]}...")
                
                return generated_text.strip()
                
            except Timeout as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt} timed out after {self._timeout}s. "
                    f"Retrying..." if attempt < self._max_retries else "No more retries."
                )
                if attempt < self._max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
            except RequestException as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt} failed: {str(e)}. "
                    f"Retrying..." if attempt < self._max_retries else "No more retries."
                )
                if attempt < self._max_retries:
                    time.sleep(2 ** attempt)
        
        # All retries failed
        error_msg = (
            f"Failed to generate text after {self._max_retries} attempts. "
            f"Last error: {str(last_error)}"
        )
        logger.error(error_msg)
        raise OllamaGenerationError(error_msg) from last_error
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the model and connection
        
        Returns:
            Dictionary containing model metadata
        
        Example:
            >>> model = OllamaModel()
            >>> info = model.get_info()
            >>> print(info["model_name"])
        """
        try:
            # Try to get detailed model info from Ollama
            response = requests.post(
                f"{self._host}/api/show",
                json={"name": self._model_name},
                timeout=5
            )
            response.raise_for_status()
            model_details = response.json()
            
            return {
                "provider": self.provider,
                "model_name": self.name,
                "host": self._host,
                "timeout": self._timeout,
                "max_retries": self._max_retries,
                "model_details": {
                    "parameters": model_details.get("parameters"),
                    "template": model_details.get("template"),
                    "details": model_details.get("details", {}),
                }
            }
            
        except RequestException as e:
            # If detailed info fails, return basic info
            logger.warning(f"Could not fetch detailed model info: {e}")
            return {
                "provider": self.provider,
                "model_name": self.name,
                "host": self._host,
                "timeout": self._timeout,
                "max_retries": self._max_retries,
                "model_details": None
            }
    
    @property
    def name(self) -> str:
        """Return the model name"""
        return self._model_name
    
    @property
    def provider(self) -> str:
        """Return the provider name"""
        return "ollama"