"""
Agent Manager Service
Singleton service to manage agent instances and components
Adapted for your project structure
"""
from typing import Optional
import logging
import sys
import os

# Add parent directory to path so we can import from root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from models.ollama import OllamaModel
from infra.tool_registry import ToolRegistry
from memory import ConversationStore
from memory.context_manager import ContextManager
from memory.preference_engine import PreferenceEngine

logger = logging.getLogger(__name__)


class AgentManager:
    """
    Singleton service to manage all agents and shared resources
    """
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
        
        # Initialize core components
        self.model = OllamaModel()
        self.registry = ToolRegistry()
        
        # Memory components
        self.memory_store = ConversationStore()
        self.context_manager = ContextManager(self.memory_store)
        self.preference_engine = PreferenceEngine(self.memory_store)
        
        # Session storage
        self.sessions = {}
        
        self._initialized = True
        logger.info("Agent Manager initialized successfully")
    
    def get_agent(self, agent_type: str, session_id: Optional[str] = None):
        """
        Get or create agent instance
        
        Args:
            agent_type: Type of agent (react, cot, tot, scheduler)
            session_id: Optional session ID
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If agent_type is unknown
        """
        if agent_type == "react":
            from agents.react_agent import ReActAgent
            return ReActAgent(self.model, self.registry, max_steps=5)
        
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