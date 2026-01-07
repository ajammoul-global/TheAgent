"""
Prompt Library - Collection of pre-built prompt templates
Used by all agents for consistency and easy updates
"""
from promt.Prompt_template import (
    PromptTemplate,
    ReasoningPrompt,
    DecisionPrompt,
    EvaluationPrompt,
    ExtractionPrompt,
    GenerationPrompt
)
from typing import Dict, Optional


class PromptLibrary:
    """
    Central library of all prompt templates
    Agents load prompts from here instead of hardcoding
    """
    
    def __init__(self):
        """Initialize library with all templates"""
        self._prompts: Dict[str, PromptTemplate] = {}
        self._load_default_prompts()
    
    def _load_default_prompts(self):
        """Load all default prompt templates"""
        
        # ===== REASONING PROMPTS =====
        
        self.register(ReasoningPrompt(
            name="react_thought",
            template="""Task: {query}

Previous steps:
{context}

Step {step}: What should I think about next? What do I need to know?

Thought:""",
            version="1.0",
            description="ReAct agent thought generation"
        ))
        
        self.register(ReasoningPrompt(
            name="cot_reasoning_chain",
            template="""Question: {query}

Let's think through this step by step:

Step 1:""",
            version="1.0",
            description="Chain of Thought reasoning generation"
        ))
        
        self.register(ReasoningPrompt(
            name="tot_branch_generation",
            template="""Original question: {query}

Current reasoning path:
{context}

Generate {num_branches} DIFFERENT possible next steps or approaches.
Each should be a distinct way to proceed.

For depth {depth}, consider:
- Different strategies
- Alternative perspectives  
- Various solutions

Respond with ONLY a JSON array of {num_branches} distinct options:
["option 1", "option 2", "option 3"]

JSON:""",
            version="1.0",
            description="Tree of Thoughts branch generation"
        ))
        
        # ===== DECISION PROMPTS =====
        
        self.register(DecisionPrompt(
            name="tool_decision",
            template="""Thought: {thought}

Available tools:
{tools_list}

CRITICAL: If the thought mentions needing to "search", "find", "look up", or get current information, you MUST use the appropriate tool.

Examples:
- Thought: "I need to find Python tutorials" → USE web_search
- Thought: "I should search for AI news" → USE web_search  
- Thought: "I already know what Python is" → NO tool needed

Respond with ONLY valid JSON (no explanation, no markdown):
{{"needs_tool": true, "tool_name": "tool_name", "parameters": {{"param": "value"}}}}

OR if no tool needed:
{{"needs_tool": false}}

JSON:""",
            version="2.0",
            description="Decide whether to use tools and which one"
        ))
        
        self.register(DecisionPrompt(
            name="task_understanding",
            template="""Analyze this user request: "{user_input}"

Answer these questions:
1. Does this need to be scheduled on a calendar? (yes/no)
2. Do we need to search for more information? (yes/no)
3. If search needed, what should we search for?
4. What is the main task/event?

Respond with ONLY valid JSON (no explanation):
{{
    "needs_scheduling": true/false,
    "needs_search": true/false,
    "search_query": "query here" or null,
    "task_summary": "brief summary",
    "task_type": "meeting/appointment/reminder/deadline/other"
}}

JSON:""",
            version="1.0",
            description="Understand if user input is a task to schedule"
        ))
        
        # ===== EVALUATION PROMPTS =====
        
        self.register(EvaluationPrompt(
            name="path_evaluation",
            template="""Original question: {query}

Reasoning path to evaluate:
{path}

Evaluate this path based on: {criteria}

Respond with ONLY valid JSON:
{{
    "score": 7.5,
    "evaluation": "This path is good because... However...",
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1"]
}}

Score should be 0-10 (10 is best).

JSON:""",
            version="1.0",
            description="Evaluate a reasoning path in Tree of Thoughts"
        ))
        
        # ===== EXTRACTION PROMPTS =====
        
        self.register(ExtractionPrompt(
            name="schedule_details",
            template="""Extract scheduling details from this request: "{user_input}"

Task summary: {task_summary}
Additional context: {context}

Current date: {current_date}
Current time: {current_time}

Extract:
1. Event title (what to put on calendar)
2. Date (YYYY-MM-DD format)
3. Time (HH:MM in 24-hour format)
4. Duration in minutes
5. Any location or description

If date/time is relative (e.g., "tomorrow at 2pm"), calculate the actual date/time.
If duration not specified, assume 60 minutes.

Respond with ONLY valid JSON:
{{
    "title": "event title",
    "date": "YYYY-MM-DD",
    "time": "HH:MM",
    "duration_minutes": 60,
    "description": "optional description",
    "location": "optional location",
    "valid": true
}}

If you cannot extract enough info, set "valid": false and include "error" field.

JSON:""",
            version="1.0",
            description="Extract date, time, and details from natural language"
        ))
        
        # ===== GENERATION PROMPTS =====
        
        self.register(GenerationPrompt(
            name="final_answer",
            template="""Question: {query}

{context_section}

Based on {source}, provide a {style} final answer.

Answer:""",
            version="1.0",
            description="Generate final answer from reasoning/observations"
        ))
        
        self.register(GenerationPrompt(
            name="final_answer_with_data",
            template="""Question: {query}

My reasoning process:
{reasoning}

Information gathered:
{observation}

Based on my reasoning and the information found, provide a clear, comprehensive final answer:

Answer:""",
            version="1.0",
            description="Generate final answer with both reasoning and data"
        ))
        
        self.register(GenerationPrompt(
            name="final_answer_reasoning_only",
            template="""Question: {query}

My reasoning process:
{reasoning}

Based on my reasoning alone, provide a clear, comprehensive final answer:

Answer:""",
            version="1.0",
            description="Generate final answer from reasoning only"
        ))
    
    def register(self, prompt: PromptTemplate):
        """
        Register a new prompt template
        
        Args:
            prompt: PromptTemplate instance
        """
        self._prompts[prompt.name] = prompt
    
    def get(self, name: str) -> Optional[PromptTemplate]:
        """
        Get prompt template by name
        
        Args:
            name: Template name
            
        Returns:
            PromptTemplate or None if not found
        """
        return self._prompts.get(name)
    
    def list_prompts(self, prompt_type: Optional[str] = None) -> list:
        """
        List all prompt templates
        
        Args:
            prompt_type: Filter by type (optional)
            
        Returns:
            List of prompt metadata
        """
        prompts = self._prompts.values()
        
        if prompt_type:
            prompts = [p for p in prompts if p.prompt_type.value == prompt_type]
        
        return [p.get_metadata() for p in prompts]
    
    def render(self, name: str, **kwargs) -> str:
        """
        Get and render a prompt template
        
        Args:
            name: Template name
            **kwargs: Template variables
            
        Returns:
            Rendered prompt string
        """
        prompt = self.get(name)
        if not prompt:
            raise ValueError(f"Prompt template '{name}' not found")
        
        return prompt.render(**kwargs)
    
    def update(self, name: str, template: str, version: str):
        """
        Update existing prompt template
        
        Args:
            name: Template name
            template: New template text
            version: New version number
        """
        if name not in self._prompts:
            raise ValueError(f"Prompt template '{name}' not found")
        
        old_prompt = self._prompts[name]
        
        # Create new prompt with updated template
        new_prompt = type(old_prompt)(
            name=name,
            template=template,
            version=version,
            description=old_prompt.description,
            examples=old_prompt.examples
        )
        
        self._prompts[name] = new_prompt
    
    def __len__(self):
        return len(self._prompts)
    
    def __contains__(self, name: str):
        return name in self._prompts


# Global library instance
_library = None


def get_prompt_library() -> PromptLibrary:
    """Get global prompt library instance (singleton)"""
    global _library
    if _library is None:
        _library = PromptLibrary()
    return _library