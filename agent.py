"""
Life Scheduler & Research Agent
Uses local Ollama (llama3.1:8b) to schedule tasks and research topics.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

print(f"🤖 Using Ollama: {OLLAMA_MODEL} at {OLLAMA_HOST}\n")

# ============================================================================
# MODEL
# ============================================================================

class OllamaModel:
    """Local Ollama model"""
    
    def __init__(self, host: str, model: str):
        self.host = host
        self.model = model
    
    def generate(self, prompt: str) -> str:
        """Generate response from Ollama"""
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.RequestException as e:
            return f"Error calling Ollama: {e}"


# ============================================================================
# TOOLS - The agent's capabilities
# ============================================================================

class TaskDatabase:
    """Simple in-memory task storage"""
    
    def __init__(self):
        self.tasks = []
        self.next_id = 1
    
    def create_task(self, title: str, due_date: str, priority: str = "medium") -> Dict:
        """Create a new task"""
        task = {
            "id": self.next_id,
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.tasks.append(task)
        self.next_id += 1
        print(f"  ✅ Created task #{task['id']}: {title}")
        return task
    
    def list_tasks(self, status: str = None) -> List[Dict]:
        """List all tasks"""
        if status:
            return [t for t in self.tasks if t["status"] == status]
        return self.tasks


class WebSearch:
    """Real web search using DuckDuckGo (free, no API key needed)"""
    
    def __init__(self):
        try:
            from ddgs import DDGS  # Changed from duckduckgo_search
            self.ddgs = DDGS()
            self.available = True
            print("✅ DuckDuckGo Search connected (free, unlimited)")
        except ImportError:
            print("⚠️ ddgs not installed - using mock")
            self.available = False
    
    def search(self, query: str) -> str:
        """Search the web for real information"""
        print(f"  🔍 Searching web for: {query}")
        
        if not self.available:
            return f"[Mock] Information about '{query}'"
        
        try:
            # Search DuckDuckGo
            results = list(self.ddgs.text(query, max_results=5))
            
            if not results:
                return "No results found."
            
            # Format results
            search_results = []
            for i, result in enumerate(results[:3], 1):
                title = result.get("title", "")
                body = result.get("body", "")
                url = result.get("href", "")
                search_results.append(
                    f"{i}. {title}\n"
                    f"   {body}\n"
                    f"   Source: {url}"
                )
            
            return "\n\n".join(search_results)
                
        except Exception as e:
            print(f"  ⚠️ Search error: {e}")
            return f"Could not complete search: {e}"

class Calendar:
    """Calendar management (mock for now)"""
    
    def __init__(self):
        self.events = []
    
    def find_free_time(self, date: str, duration_minutes: int) -> List[Dict]:
        """Find free time slots"""
        print(f"  📅 Finding free time on {date} for {duration_minutes} minutes")
        base_date = datetime.fromisoformat(date)
        return [
            {
                "start": (base_date.replace(hour=9, minute=0)).isoformat(),
                "duration": duration_minutes,
                "label": "Morning slot (9:00 AM)"
            },
            {
                "start": (base_date.replace(hour=14, minute=0)).isoformat(),
                "duration": duration_minutes,
                "label": "Afternoon slot (2:00 PM)"
            },
            {
                "start": (base_date.replace(hour=19, minute=0)).isoformat(),
                "duration": duration_minutes,
                "label": "Evening slot (7:00 PM)"
            }
        ]
    
    def schedule_event(self, title: str, start_time: str, duration_minutes: int) -> Dict:
        """Schedule a calendar event"""
        event = {
            "title": title,
            "start": start_time,
            "duration": duration_minutes,
            "created": datetime.now().isoformat()
        }
        self.events.append(event)
        print(f"  📌 Scheduled: {title} at {start_time}")
        return event


# ============================================================================
# AGENT - The brain that orchestrates everything
# ============================================================================

class LifeAgent:
    """Main agent that combines scheduling and research"""
    
    def __init__(self, model):
        self.model = model
        self.task_db = TaskDatabase()
        self.web_search = WebSearch()
        self.calendar = Calendar()
    
    def process(self, user_input: str, max_iterations: int = 6) -> str:
        """Main agent loop"""
        print(f"\n{'='*70}")
        print(f"👤 USER REQUEST: {user_input}")
        print(f"{'='*70}\n")
        
        conversation_history = []
        
        for iteration in range(max_iterations):
            print(f"\n🔄 ITERATION {iteration + 1}/{max_iterations}")
            print("-" * 70)
            
            # Build prompt with tools and history
            prompt = self._build_prompt(user_input, conversation_history)
            
            # Get model response
            print("🤔 Agent is thinking...")
            response = self.model.generate(prompt)
            
            # Parse for tool calls
            tool_call = self._parse_tool_call(response)
            
            if tool_call is None:
                # No tool call - agent is done
                print("\n✅ Agent has completed the task!")
                return self._extract_final_answer(response)
            
            # Execute tool
            print(f"\n🔧 Calling tool: {tool_call['tool']}")
            print(f"   Parameters: {tool_call['params']}")
            tool_result = self._execute_tool(tool_call)
            
            # Add to history
            conversation_history.append({
                "tool": tool_call["tool"],
                "params": tool_call["params"],
                "result": tool_result
            })
        
        # Max iterations reached
        print("\n⚠️ Reached max iterations")
        return "Task planning completed. You can now review the tasks and schedule."
    
    def _build_prompt(self, user_input: str, history: List[Dict]) -> str:
        """Build the prompt for the model"""
        
        tools_description = """You are a helpful life planning assistant. You can use these tools:

1. create_task - Create a task
   Parameters: title (string), due_date (YYYY-MM-DD), priority (high/medium/low)

2. research_topic - Search for information on a topic
   Parameters: query (string)

3. find_free_time - Find available time slots
   Parameters: date (YYYY-MM-DD), duration_minutes (integer)

4. schedule_event - Schedule a calendar event
   Parameters: title (string), start_time (ISO datetime), duration_minutes (integer)

5. list_tasks - List all current tasks
   Parameters: none

6. DONE - When you've completed helping the user
   Use this when you've created tasks, done research, and scheduled as needed

IMPORTANT: Respond with ONLY valid JSON, no other text. Format:
{"tool": "tool_name", "params": {"param1": "value1"}}

Or when done:
{"tool": "DONE", "response": "summary of what you did for the user"}
"""
        
        history_text = ""
        if history:
            history_text = "What you've done so far:\n"
            for i, h in enumerate(history, 1):
                history_text += f"{i}. Used {h['tool']} → Result: {str(h['result'])[:100]}\n"
        else:
            history_text = "You haven't done anything yet. Start by analyzing what the user needs."
        
        prompt = f"""{tools_description}

{history_text}

User's request: {user_input}

What should you do next? Respond with JSON only:"""
        
        return prompt
    
    def _parse_tool_call(self, response: str) -> Optional[Dict]:
        """Parse tool call from model response"""
        try:
            # Clean up response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            # Find JSON in the response
            start = response.find("{")
            end = response.rfind("}") + 1
            
            if start == -1 or end == 0:
                return None
            
            json_str = response[start:end]
            parsed = json.loads(json_str)
            
            tool_name = parsed.get("tool")
            
            if tool_name == "DONE":
                return None  # Signal completion
            
            return {
                "tool": tool_name,
                "params": parsed.get("params", {})
            }
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"  ⚠️ Could not parse tool call: {e}")
            print(f"  Raw response: {response[:200]}")
            return None
    
    def _execute_tool(self, tool_call: Dict) -> Any:
        """Execute the requested tool"""
        tool_name = tool_call["tool"]
        params = tool_call["params"]
        
        try:
            if tool_name == "create_task":
                return self.task_db.create_task(**params)
            elif tool_name == "list_tasks":
                tasks = self.task_db.list_tasks()
                return f"Found {len(tasks)} tasks: {tasks}"
            elif tool_name == "research_topic":
                return self.web_search.search(params.get("query", ""))
            elif tool_name == "find_free_time":
                return self.calendar.find_free_time(
                    params.get("date"),
                    params.get("duration_minutes", 60)
                )
            elif tool_name == "schedule_event":
                return self.calendar.schedule_event(**params)
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Error executing {tool_name}: {e}"
    
    def _extract_final_answer(self, response: str) -> str:
        """Extract final answer from response"""
        try:
            # Try to find JSON with response field
            if "{" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                parsed = json.loads(response[start:end])
                if "response" in parsed:
                    return parsed["response"]
        except:
            pass
        
        # Return cleaned response
        return response.strip()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("🚀 Starting Life Scheduler & Research Agent\n")
    
    # Initialize model and agent
    model = OllamaModel(OLLAMA_HOST, OLLAMA_MODEL)
    agent = LifeAgent(model)
    
    # Test requests - try different ones!
    test_requests = [
        "I need to write a research paper on quantum computing by December 15th. Help me plan this out and schedule time for it.",
        
        # Uncomment to try others:
        # "I have a meeting about AI safety next week. Research the topic and help me prepare.",
        # "Schedule time for exercise 3 times this week",
    ]
    
    # Run the agent
    result = agent.process(test_requests[0])
    
    print("\n" + "="*70)
    print("🎉 FINAL RESULT")
    print("="*70)
    print(result)
    
    # Show created tasks
    print("\n" + "="*70)
    print("📋 ALL TASKS CREATED")
    print("="*70)
    for task in agent.task_db.list_tasks():
        print(f"  • [{task['priority'].upper()}] {task['title']} (Due: {task['due_date']})")
    
    print("\n✨ Agent completed!\n")