"""
Preference Engine - Learn and apply user preferences
Tracks patterns and explicit preferences to personalize agent behavior
"""
from typing import Dict, List, Optional, Any
from collections import Counter
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class PreferenceEngine:
    """
    Learns user preferences from conversations
    Applies preferences to improve agent decisions
    """
    
    def __init__(self, store):
        """
        Initialize preference engine
        
        Args:
            store: Conversation store instance
        """
        self.store = store
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> Dict:
        """Load preferences from storage"""
        # For now, start with empty preferences
        # In production, this would load from a preferences file/database
        return {
            'explicit': {},      # User-stated preferences
            'patterns': {},      # Learned patterns
            'metadata': {
                'last_updated': datetime.now().isoformat()
            }
        }
    
    def save_explicit_preference(
        self,
        category: str,
        key: str,
        value: Any
    ):
        """
        Save explicit user preference
        
        Args:
            category: Preference category (e.g., 'scheduling', 'notifications')
            key: Preference key (e.g., 'preferred_time')
            value: Preference value (e.g., '10:00')
        """
        if category not in self.preferences['explicit']:
            self.preferences['explicit'][category] = {}
        
        self.preferences['explicit'][category][key] = value
        self.preferences['metadata']['last_updated'] = datetime.now().isoformat()
        
        logger.info(f"Saved preference: {category}.{key} = {value}")
    
    def get_preference(
        self,
        category: str,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Get user preference
        
        Args:
            category: Preference category
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        explicit = self.preferences['explicit'].get(category, {}).get(key)
        if explicit is not None:
            return explicit
        
        # Check learned patterns
        pattern = self.preferences['patterns'].get(category, {}).get(key)
        if pattern is not None:
            return pattern
        
        return default
    
    def detect_patterns(
        self,
        agent_type: str = 'task_scheduler',
        min_occurrences: int = 3
    ):
        """
        Detect patterns in user behavior
        
        Args:
            agent_type: Filter by agent type
            min_occurrences: Minimum occurrences to consider a pattern
        """
        logger.info(f"Detecting patterns for {agent_type}...")
        
        # Get recent conversations
        conversations = self.store.get_recent(limit=50, agent_type=agent_type)
        
        if agent_type == 'task_scheduler':
            self._detect_scheduling_patterns(conversations, min_occurrences)
    
    def _detect_scheduling_patterns(
        self,
        conversations: List[Dict],
        min_occurrences: int
    ):
        """Detect scheduling patterns"""
        times = []
        days = []
        durations = []
        
        for conv in conversations:
            metadata = conv.get('metadata', {})
            if not metadata:
                continue
            
            # Collect times
            if 'time' in metadata:
                times.append(metadata['time'][:2])  # Hour only
            
            # Collect days
            if 'date' in metadata:
                try:
                    date = datetime.fromisoformat(metadata['date'])
                    days.append(date.strftime('%A'))  # Day name
                except:
                    pass
            
            # Collect durations
            if 'duration_minutes' in metadata:
                durations.append(metadata['duration_minutes'])
        
        # Find most common
        if times:
            most_common_time = Counter(times).most_common(1)[0]
            if most_common_time[1] >= min_occurrences:
                preferred_time = f"{most_common_time[0]}:00"
                self.preferences['patterns'].setdefault('scheduling', {})[
                    'preferred_meeting_time'
                ] = preferred_time
                logger.info(f"Detected pattern: preferred_meeting_time = {preferred_time}")
        
        if days:
            most_common_day = Counter(days).most_common(1)[0]
            if most_common_day[1] >= min_occurrences:
                preferred_day = most_common_day[0]
                self.preferences['patterns'].setdefault('scheduling', {})[
                    'preferred_meeting_day'
                ] = preferred_day
                logger.info(f"Detected pattern: preferred_meeting_day = {preferred_day}")
        
        if durations:
            avg_duration = sum(durations) // len(durations)
            self.preferences['patterns'].setdefault('scheduling', {})[
                'typical_meeting_duration'
            ] = avg_duration
            logger.info(f"Detected pattern: typical_meeting_duration = {avg_duration}min")
    
    def extract_preference_from_text(self, text: str) -> Optional[Dict]:
        """
        Extract explicit preferences from user text
        
        Args:
            text: User message text
            
        Returns:
            Dict with preference info or None
        """
        text_lower = text.lower()
        
        # Pattern: "I prefer [X]"
        if 'i prefer' in text_lower or 'i like' in text_lower:
            # Morning/afternoon preferences
            if 'morning' in text_lower:
                return {
                    'category': 'scheduling',
                    'key': 'preferred_time_of_day',
                    'value': 'morning'
                }
            elif 'afternoon' in text_lower:
                return {
                    'category': 'scheduling',
                    'key': 'preferred_time_of_day',
                    'value': 'afternoon'
                }
            
            # Day preferences
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            for day in days:
                if day in text_lower:
                    return {
                        'category': 'scheduling',
                        'key': 'preferred_meeting_day',
                        'value': day.capitalize()
                    }
        
        # Pattern: "Always [X]" or "Never [X]"
        if 'always' in text_lower or 'never' in text_lower:
            if 'meeting' in text_lower and 'morning' in text_lower:
                return {
                    'category': 'scheduling',
                    'key': 'meeting_time_rule',
                    'value': 'always_morning' if 'always' in text_lower else 'never_morning'
                }
        
        return None
    
    def suggest_time(
        self,
        event_type: str = 'meeting',
        context: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Suggest a time based on preferences and patterns
        
        Args:
            event_type: Type of event
            context: Additional context
            
        Returns:
            Suggested time string or None
        """
        # Check explicit preference
        explicit_time = self.get_preference('scheduling', 'preferred_meeting_time')
        if explicit_time:
            logger.info(f"Using explicit preference: {explicit_time}")
            return explicit_time
        
        # Check explicit time of day
        time_of_day = self.get_preference('scheduling', 'preferred_time_of_day')
        if time_of_day == 'morning':
            return '10:00'
        elif time_of_day == 'afternoon':
            return '14:00'
        
        # Check patterns
        pattern_time = self.get_preference('scheduling', 'preferred_meeting_time')
        if pattern_time:
            logger.info(f"Using pattern: {pattern_time}")
            return pattern_time
        
        # Default
        return '10:00'
    
    def get_preferences_summary(self) -> str:
        """Get human-readable summary of preferences"""
        lines = []
        
        # Explicit preferences
        if self.preferences['explicit']:
            lines.append("Your Preferences:")
            for category, prefs in self.preferences['explicit'].items():
                for key, value in prefs.items():
                    lines.append(f"  • {key}: {value}")
        
        # Learned patterns
        if self.preferences['patterns']:
            lines.append("\nDetected Patterns:")
            for category, patterns in self.preferences['patterns'].items():
                for key, value in patterns.items():
                    lines.append(f"  • {key}: {value}")
        
        if not lines:
            return "No preferences set yet."
        
        return "\n".join(lines)
    
    def export_preferences(self) -> str:
        """Export preferences as JSON"""
        return json.dumps(self.preferences, indent=2)
    
    def import_preferences(self, json_data: str):
        """Import preferences from JSON"""
        try:
            imported = json.loads(json_data)
            self.preferences = imported
            logger.info("Imported preferences successfully")
        except Exception as e:
            logger.error(f"Failed to import preferences: {e}")