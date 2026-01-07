from typing import Dict, Any, Optional
from models.base import BaseModel
from infra.tool_registry import ToolRegistry
from memory import ConversationStore
from memory.context_manager import ContextManager
from memory.preference_engine import PreferenceEngine
from infra.logging import logger
from datetime import datetime, timedelta
import json
import uuid
import dateparser
# Create or get registry instance
registry = ToolRegistry()

class MemoryEnabledScheduler:
    """
    Memory-enabled task scheduler
    - Remembers conversations
    - Resolves references
    - Applies user preferences
    - Can schedule on Google Calendar if tool is registered
    """
    
    def __init__(self, model: BaseModel, registry: ToolRegistry):
        self.model = model
        self.registry = registry
        
        # Memory components
        self.memory = ConversationStore()
        self.context = ContextManager(self.memory)
        self.preferences = PreferenceEngine(self.memory)
        
        # Session ID
        self.session_id = str(uuid.uuid4())[:8]
        logger.info(f"Memory-enabled scheduler initialized (session: {self.session_id})")
    
    def run(self, user_input: str) -> str:
        logger.info(f"[Session {self.session_id}] User: {user_input}")
        
        # Check for preference statements
        preference = self.preferences.extract_preference_from_text(user_input)
        if preference:
            self.preferences.save_explicit_preference(
                preference['category'],
                preference['key'],
                preference['value']
            )
            return f"✓ Got it! I'll remember that you {user_input.lower()}"
        
        # Check for reference resolution
        if self._has_reference(user_input):
            resolved = self._handle_reference(user_input)
            response = resolved or self._process_new_task(user_input)
        else:
            response = self._process_new_task(user_input)
        
        # Save conversation to memory
        self.memory.save(
            user_message=user_input,
            agent_response=response,
            session_id=self.session_id,
            agent_type="memory_scheduler",
            metadata=self._extract_metadata(user_input, response)
        )
        
        logger.info(f"[Session {self.session_id}] Agent: {response[:100]}...")
        return response
    
    def _has_reference(self, text: str) -> bool:
        reference_words = [
            'that meeting', 'that appointment', 'the meeting', 'the appointment',
            'move it', 'cancel it', 'reschedule it', 'what time', 'when is'
        ]
        return any(ref in text.lower() for ref in reference_words)
    
    def _handle_reference(self, user_input: str) -> Optional[str]:
        context = self.context.get_relevant_context(user_input, max_results=5)
        if not context:
            return None
        
        user_lower = user_input.lower()
        
        # Check for time queries
        if 'what time' in user_lower or 'when is' in user_lower:
            for conv in context:
                metadata = conv.get('metadata', {})
                if metadata and 'time' in metadata:
                    return f"Your {metadata.get('event', 'appointment')} is scheduled for {metadata.get('date', 'soon')} at {metadata.get('time', 'TBD')}"
        
        # Reschedule
        if 'move' in user_lower or 'reschedule' in user_lower:
            resolved = self.context.resolve_reference("that meeting", context)
            if resolved:
                entities = self.context.extract_entities(user_input)
                new_time = entities['times'][0] if entities['times'] else None
                if new_time:
                    return f"✓ Moved {resolved['metadata'].get('event', 'event')} to {new_time}"
                return "What time would you like to reschedule to?"
        
        # Cancel
        if 'cancel' in user_lower:
            resolved = self.context.resolve_reference("that event", context)
            if resolved:
                return f"✓ Cancelled {resolved['metadata'].get('event', 'event')}"
        
        return None
    
    def _process_new_task(self, user_input: str) -> str:
        entities = self.context.extract_entities(user_input)
        task_info = self._understand_task(user_input)
        
        if not task_info.get('needs_scheduling'):
            return "This doesn't seem like a scheduling request. How can I help?"
        
        schedule_details = self._extract_schedule_with_preferences(user_input, entities)
        if not schedule_details.get('valid'):
            return schedule_details.get('error', "Could not understand scheduling details")
        
        # Always save in memory
        self.memory.save(
            user_message=user_input,
            agent_response=f"Scheduled: {schedule_details['title']} on {schedule_details['date']} at {schedule_details['time']}",
            session_id=self.session_id,
            agent_type="memory_scheduler",
            metadata={
                'title': schedule_details['title'],
                'date': schedule_details['date'],
                'time': schedule_details['time'],
                'duration_minutes': schedule_details.get('duration_minutes', 60)
            }
        )
        
        # Schedule on Google Calendar if tool exists
       
        return (
            f"✓ Got it! I'll remember:\n"
            f"📋 {schedule_details['title']}\n"
            f"📅 {schedule_details['date']} at {schedule_details['time']}\n"
            f"⏱️  Duration: {schedule_details.get('duration_minutes', 60)} minutes"
        )
    
    from datetime import datetime, timedelta

    def _schedule_on_calendar(self, details: Dict) -> str:
            """Schedule event on Google Calendar via the registered tool"""
            try:
                start_time_obj = datetime.strptime(details['time'], '%H:%M')
                end_time_obj = start_time_obj + timedelta(minutes=details.get('duration_minutes', 60))

                params = {
                'summary': details['title'],
                'start_time': f"{details['date']}T{start_time_obj.strftime('%H:%M')}:00",
                'end_time': f"{details['date']}T{end_time_obj.strftime('%H:%M')}:00",
                'description': 'Scheduled via MemoryEnabledScheduler',
                }

        # Make sure to use the correct tool name
                if 'google_calendar_create' not in self.registry.list_tools():
                    return f"❌ Google Calendar tool not found. Available tools: {self.registry.list_tools()}"

                result = self.registry.execute_tool('google_calendar_create', **params)

                if result.success:
                    event_data = result.data or {}
                    return (
                        f"✅ Scheduled successfully on Google Calendar!\n"
                        f"📋 {details['title']}\n"
                        f"📅 {details['date']} at {details['time']}\n"
                        f"⏱️  Duration: {details.get('duration_minutes', 60)} minutes\n"
                        f"🔗 {event_data.get('htmlLink', 'N/A')}"
                )
                else:
                    return f"❌ Failed to schedule on Google Calendar: {result.error}"

            except Exception as e:
                return f"❌ Error scheduling on Google Calendar: {str(e)}"

    def _understand_task(self, user_input: str) -> Dict[str, Any]:
        keywords = ['schedule', 'meeting', 'appointment', 'remind', 'event', 'book']
        return {'needs_scheduling': any(k in user_input.lower() for k in keywords), 'task_summary': user_input}
    
    def _extract_schedule_with_preferences(self, user_input: str, entities: Dict) -> Dict[str, Any]:
        details = {'title': ' '.join(user_input.split()[1:5]), 'valid': True}

    # Date/time parsing
        if entities.get('dates') or entities.get('times'):
            dt_str = (entities.get('dates', [''])[0] + ' ' + entities.get('times', [''])[0]).strip()
            dt = dateparser.parse(dt_str) if dt_str else None
        else:
            dt = dateparser.parse(user_input)  # fallback: parse the whole input

        if not dt:
            return {'valid': False, 'error': "Could not understand scheduling date/time"}

        details['date'] = dt.strftime('%Y-%m-%d')
        details['time'] = dt.strftime('%H:%M')
        details['duration_minutes'] = self.preferences.get_preference('scheduling', 'typical_meeting_duration', default=60)
        return details
    
    def _extract_metadata(self, user_input: str, response: str) -> Dict:
        entities = self.context.extract_entities(user_input)
        return {
            'dates': entities.get('dates', []),
            'times': entities.get('times', []),
            'has_reference': self._has_reference(user_input),
            'session': self.session_id
        }
    
    def get_memory_stats(self) -> str:
        stats = self.memory.get_stats()
        prefs = self.preferences.get_preferences_summary()
        return f"""Memory Statistics:
- Total conversations: {stats['total_conversations']}
- Earliest: {stats.get('earliest_conversation', 'N/A')}
- Latest: {stats.get('latest_conversation', 'N/A')}

{prefs}
"""
    
    def search_memory(self, query: str) -> str:
        results = self.memory.search(query, limit=5)
        if not results:
            return "No matching conversations found."
        lines = [f"Found {len(results)} conversations:"]
        for i, conv in enumerate(results, 1):
            lines.append(f"\n{i}. {conv['timestamp']}")
            lines.append(f"   You: {conv['user_message'][:60]}...")
            lines.append(f"   Me: {conv['agent_response'][:60]}...")
        return "\n".join(lines)
