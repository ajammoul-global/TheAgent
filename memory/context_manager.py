"""
Context Manager - Intelligent context retrieval and reference resolution
Helps agents understand "that meeting", "the appointment", etc.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from memory.conversation_store import ConversationStore
import re
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages conversation context and resolves references
    Helps agents understand what users are referring to
    """
    
    def __init__(self, store: ConversationStore):
        """
        Initialize context manager
        
        Args:
            store: Conversation store instance
        """
        self.store = store
        self.entity_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict:
        """Compile regex patterns for entity extraction"""
        return {
            'dates': [
                r'\b(tomorrow|today|yesterday)\b',
                r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                r'\b(\d{1,2}/\d{1,2}(/\d{2,4})?)\b',
                r'\b(next|this|last)\s+(week|month|year)\b',
            ],
            'times': [
                r'\b(\d{1,2}:\d{2}\s*(?:am|pm)?)\b',
                r'\b(\d{1,2}\s*(?:am|pm))\b',
            ],
            'references': [
                r'\b(that|the|this)\s+(meeting|appointment|task|event)\b',
                r'\b(it|them)\b',
            ],
            'people': [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',  # Names
            ]
        }
    
    def get_relevant_context(
        self,
        query: str,
        max_results: int = 5,
        recency_weight: float = 0.7
    ) -> List[Dict]:
        """
        Get relevant context for a query
        
        Args:
            query: Current user query
            max_results: Maximum context items to return
            recency_weight: Weight for recent conversations (0-1)
            
        Returns:
            List of relevant conversations
        """
        # Extract key terms from query
        keywords = self._extract_keywords(query)
        
        if not keywords:
            # No keywords, return recent conversations
            return self.store.get_recent(limit=max_results)
        
        # Search for relevant conversations
        results = []
        for keyword in keywords[:3]:  # Top 3 keywords
            found = self.store.search(keyword, limit=max_results)
            results.extend(found)
        
        # Remove duplicates
        seen_ids = set()
        unique_results = []
        for conv in results:
            if conv['id'] not in seen_ids:
                seen_ids.add(conv['id'])
                unique_results.append(conv)
        
        # Score and sort
        scored = self._score_relevance(query, unique_results, recency_weight)
        
        return scored[:max_results]
    
    def resolve_reference(
        self,
        reference: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Optional[Dict]:
        """
        Resolve references like "that meeting", "the appointment"
        
        Args:
            reference: Reference text to resolve
            conversation_history: Recent conversation history
            
        Returns:
            Resolved entity dict or None
        """
        reference_lower = reference.lower()
        
        # Common reference words
        if 'meeting' in reference_lower:
            entity_type = 'meeting'
        elif 'appointment' in reference_lower:
            entity_type = 'appointment'
        elif 'task' in reference_lower or 'event' in reference_lower:
            entity_type = 'task'
        else:
            entity_type = None
        
        # Search recent conversations for this entity type
        if entity_type:
            recent = self.store.get_recent(limit=10, agent_type='task_scheduler')
            
            for conv in recent:
                metadata = conv.get('metadata', {})
                if not metadata:
                    continue
                
                # Check if this conversation is about the entity type
                task_type = metadata.get('task_type', '').lower()
                event = metadata.get('event', '').lower()
                
                if entity_type in task_type or entity_type in event:
                    logger.info(f"Resolved '{reference}' to: {metadata}")
                    return {
                        'conversation_id': conv['id'],
                        'entity_type': entity_type,
                        'metadata': metadata,
                        'original_message': conv['user_message'],
                        'timestamp': conv['timestamp']
                    }
        
        logger.warning(f"Could not resolve reference: {reference}")
        return None
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities from text (dates, times, people, etc.)
        
        Args:
            text: Text to extract from
            
        Returns:
            Dict of entity types and their values
        """
        entities = {
            'dates': [],
            'times': [],
            'references': [],
            'people': []
        }
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Flatten tuples if needed
                    flat_matches = []
                    for match in matches:
                        if isinstance(match, tuple):
                            flat_matches.extend([m for m in match if m])
                        else:
                            flat_matches.append(match)
                    entities[entity_type].extend(flat_matches)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def get_session_summary(
        self,
        session_id: str,
        max_length: int = 500
    ) -> str:
        """
        Generate summary of a conversation session
        
        Args:
            session_id: Session to summarize
            max_length: Max length of summary
            
        Returns:
            Summary text
        """
        history = self.store.get_session_history(session_id)
        
        if not history:
            return "No conversation history found."
        
        # Simple summarization - list key topics
        topics = []
        for conv in history:
            # Extract first few words as topic
            user_msg = conv['user_message']
            words = user_msg.split()[:5]
            topic = ' '.join(words)
            topics.append(topic)
        
        summary = f"Discussed {len(history)} topics: " + ", ".join(topics[:5])
        
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return summary
    
    def find_related_conversations(
        self,
        conversation_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find conversations related to a given conversation
        
        Args:
            conversation_id: Reference conversation
            limit: Max related conversations
            
        Returns:
            List of related conversations
        """
        # Get the reference conversation
        ref_conv = self.store.get_by_id(conversation_id)
        if not ref_conv:
            return []
        
        # Extract keywords from it
        keywords = self._extract_keywords(
            ref_conv['user_message'] + ' ' + ref_conv['agent_response']
        )
        
        # Search for related
        related = []
        for keyword in keywords[:3]:
            found = self.store.search(keyword, limit=limit)
            related.extend(found)
        
        # Remove the original and duplicates
        seen = {conversation_id}
        unique = []
        for conv in related:
            if conv['id'] not in seen:
                seen.add(conv['id'])
                unique.append(conv)
        
        return unique[:limit]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction - remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'what', 'when', 'where', 'why', 'how'
        }
        
        # Tokenize and filter
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Return unique keywords
        return list(dict.fromkeys(keywords))
    
    def _score_relevance(
        self,
        query: str,
        conversations: List[Dict],
        recency_weight: float
    ) -> List[Dict]:
        """Score and sort conversations by relevance"""
        query_keywords = set(self._extract_keywords(query))
        
        scored = []
        for conv in conversations:
            # Keyword match score
            conv_text = conv['user_message'] + ' ' + conv['agent_response']
            conv_keywords = set(self._extract_keywords(conv_text))
            
            keyword_score = len(query_keywords & conv_keywords) / max(len(query_keywords), 1)
            
            # Recency score (hours ago)
            try:
                timestamp = datetime.fromisoformat(conv['timestamp'])
                hours_ago = (datetime.now() - timestamp).total_seconds() / 3600
                recency_score = 1.0 / (1.0 + hours_ago / 24)  # Decay over days
            except:
                recency_score = 0.5
            
            # Combined score
            total_score = (
                keyword_score * (1 - recency_weight) +
                recency_score * recency_weight
            )
            
            conv['_score'] = total_score
            scored.append(conv)
        
        # Sort by score
        scored.sort(key=lambda x: x['_score'], reverse=True)
        
        return scored