from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseModel(ABC):
    """
    Abstract base class for all LLM models.
    
    ABC = Abstract Base Class
    This means: You CANNOT create an instance of BaseModel directly.
    You MUST create a subclass that implements all @abstractmethod methods.
    
    Example:
        # This will ERROR:
        model = BaseModel()  # ❌ Can't instantiate abstract class
        
        # This will WORK:
        model = OllamaModel()  # ✅ OllamaModel implements BaseModel
    """
    
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response from the LLM.
        
        This is the MAIN method - every model MUST implement this!
        
        Args:
            prompt: The input text to send to the model
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum length of response (None = model default)
            
        Returns:
            str: The generated response text
            
        Example:
            >>> model = OllamaModel(...)
            >>> response = model.generate("What is Python?")
            >>> print(response)
            "Python is a programming language..."
        """
        pass  # Subclasses MUST implement this
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this model.
        
        Returns metadata like provider name, model name, etc.
        Useful for logging, debugging, and user interfaces.
        
        Returns:
            Dict with model information
            
        Example:
            >>> model.get_info()
            {
                'provider': 'ollama',
                'model': 'llama3.1:8b',
                'host': 'http://localhost:11434'
            }
        """
        pass  # Subclasses MUST implement this
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        The name/identifier of this model.
        
        @property makes this behave like an attribute, not a method.
        You access it as: model.name (not model.name())
        
        Returns:
            Model name (e.g., 'llama3.1:8b', 'gpt-4', 'claude-3')
            
        Example:
            >>> model = OllamaModel(model='llama3.1:8b')
            >>> print(model.name)
            'llama3.1:8b'
        """
        pass  # Subclasses MUST implement this
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """
        The provider of this model.
        
        Returns:
            Provider name (e.g., 'ollama', 'openai', 'anthropic')
            
        Example:
            >>> model = OllamaModel(...)
            >>> print(model.provider)
            'ollama'
        """
        pass  # Subclasses MUST implement this

