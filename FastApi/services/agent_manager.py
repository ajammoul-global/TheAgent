from typing import Optional
import logging
import sys
import os

# New Import: Replace Ollama with HuggingFace
from models.huggingface import HuggingFaceModel
from infra.tool_registry import ToolRegistry
from memory import ConversationStore
from memory.context_manager import ContextManager
from memory.preference_engine import PreferenceEngine

logger = logging.getLogger(__name__)

class AgentManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
     
    def __init__(self):
        if self._initialized:
            return
        
        logger.info("Initializing Agent Manager...")
        self.model = None  # Don't load the model here!
        self.registry = ToolRegistry()
        self.memory_store = ConversationStore()
        self.context_manager = ContextManager(self.memory_store)
        self.preference_engine = PreferenceEngine(self.memory_store)
        self.sessions = {}
        self._initialized = True

    def get_model(self):
        """Lazy load the model only when an agent is actually requested."""
        if self.model is None:
            from models.huggingface import HuggingFaceModel
            model_id = os.getenv("HF_MODEL_ID", "Ali-jammoul/fake-news-detector-3b")
            logger.info(f"Loading Hugging Face model: {model_id}")
            self.model = HuggingFaceModel(model_id=model_id)
        return self.model

    def get_agent(self, agent_type: str, session_id: Optional[str] = None):
        # Pass self.get_model() instead of self.model
        current_model = self.get_model()
        
        if agent_type == "react":
            from agents.react_agent import ReActAgent
            return ReActAgent(current_model, self.registry, max_steps=5)
        elif agent_type == "cot":
            from agents.cot_agent import CoTAgent
            return CoTAgent(self.model, self.registry, num_thoughts=3)
        
        elif agent_type == "tot":
            from agents.tot_agent import TreeOfThoughtsAgent
            return TreeOfThoughtsAgent(
                self.model, 
                self.registry, 
                num_branches=3, 
                max_depth=2
            )
        
        elif agent_type == "scheduler":
            from agents.memory_agent import MemoryEnabledScheduler
            return MemoryEnabledScheduler(self.model, self.registry)
        
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    
    def get_stats(self) -> dict:
        """Get system statistics"""
        return {
            "memory": self.memory_store.get_stats(),
            "tools": {
                "available": self.registry.list_tools(),
                "count": len(self.registry)
            },
            "sessions": {
                "active": len(self.sessions)
            }
        }


# Global manager instance
agent_manager = AgentManager()