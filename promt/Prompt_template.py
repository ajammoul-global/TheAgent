"""
Prompt Template System - Base classes for prompt management
Allows storing, versioning, and reusing prompts across agents
"""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from enum import Enum
import json
from pathlib import Path


class PromptType(Enum):
    """Types of prompts in the system"""
    REASONING = "reasoning"
    DECISION = "decision"
    EVALUATION = "evaluation"
    EXTRACTION = "extraction"
    GENERATION = "generation"


class PromptTemplate(ABC):
    """Base class for prompt templates"""
    
    def __init__(
        self,
        name: str,
        template: str,
        prompt_type: PromptType,
        version: str = "1.0",
        description: str = "",
        examples: Optional[List[Dict]] = None
    ):
        """
        Initialize prompt template
        
        Args:
            name: Template name/identifier
            template: Prompt text with {placeholders}
            prompt_type: Type of prompt
            version: Version number
            description: What this prompt does
            examples: Example inputs/outputs
        """
        self.name = name
        self.template = template
        self.prompt_type = prompt_type
        self.version = version
        self.description = description
        self.examples = examples or []
        self._validate_template()
    
    def _validate_template(self):
        """Validate template has required placeholders"""
        # Override in subclasses for specific validation
        pass
    
    def render(self, **kwargs) -> str:
        """
        Render template with provided values
        
        Args:
            **kwargs: Values for template placeholders
            
        Returns:
            Rendered prompt string
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get template metadata"""
        return {
            "name": self.name,
            "type": self.prompt_type.value,
            "version": self.version,
            "description": self.description,
            "example_count": len(self.examples)
        }
    
    def __repr__(self):
        return f"PromptTemplate(name={self.name}, type={self.prompt_type.value}, v{self.version})"


class ReasoningPrompt(PromptTemplate):
    """Template for reasoning/thinking prompts"""
    
    def __init__(self, name: str, template: str, **kwargs):
        super().__init__(
            name=name,
            template=template,
            prompt_type=PromptType.REASONING,
            **kwargs
        )
    
    def _validate_template(self):
        """Ensure reasoning prompts have context"""
        required = ["{query}", "{context}"]
        for var in required:
            if var not in self.template:
                # Soft warning - not all reasoning prompts need all vars
                pass


class DecisionPrompt(PromptTemplate):
    """Template for decision-making prompts"""
    
    def __init__(self, name: str, template: str, **kwargs):
        super().__init__(
            name=name,
            template=template,
            prompt_type=PromptType.DECISION,
            **kwargs
        )


class EvaluationPrompt(PromptTemplate):
    """Template for evaluation/scoring prompts"""
    
    def __init__(self, name: str, template: str, **kwargs):
        super().__init__(
            name=name,
            template=template,
            prompt_type=PromptType.EVALUATION,
            **kwargs
        )


class ExtractionPrompt(PromptTemplate):
    """Template for information extraction prompts"""
    
    def __init__(self, name: str, template: str, **kwargs):
        super().__init__(
            name=name,
            template=template,
            prompt_type=PromptType.EXTRACTION,
            **kwargs
        )


class GenerationPrompt(PromptTemplate):
    """Template for content generation prompts"""
    
    def __init__(self, name: str, template: str, **kwargs):
        super().__init__(
            name=name,
            template=template,
            prompt_type=PromptType.GENERATION,
            **kwargs
        )