"""
Conversation Store - SQLite-based conversation memory
Stores and retrieves all agent conversations with metadata
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConversationStore:
    """
    Stores conversations in SQLite database
    Provides search, retrieval, and context management
    """
    
    def __init__(self, db_path: str = "/app/data/conversations.db"):
        """
        Initialize conversation store
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
        logger.info(f"Conversation store initialized: {db_path}")
    
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    user_message TEXT NOT NULL,
                    agent_response TEXT NOT NULL,
                    agent_type TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for faster searches
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON conversations(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session 
                ON conversations(session_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_type 
                ON conversations(agent_type)
            """)
            
            # Create FTS (Full Text Search) table for searching
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS conversations_fts 
                USING fts5(
                    id UNINDEXED,
                    user_message,
                    agent_response,
                    content='conversations',
                    content_rowid='id'
                )
            """)
            
            # Create triggers to keep FTS in sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS conversations_ai 
                AFTER INSERT ON conversations BEGIN
                    INSERT INTO conversations_fts(id, user_message, agent_response)
                    VALUES (new.id, new.user_message, new.agent_response);
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS conversations_ad 
                AFTER DELETE ON conversations BEGIN
                    DELETE FROM conversations_fts WHERE id = old.id;
                END
            """)
            
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS conversations_au 
                AFTER UPDATE ON conversations BEGIN
                    UPDATE conversations_fts 
                    SET user_message = new.user_message,
                        agent_response = new.agent_response
                    WHERE id = new.id;
                END
            """)
            
            conn.commit()
    
    def save(
        self,
        user_message: str,
        agent_response: str,
        session_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Save a conversation
        
        Args:
            user_message: User's input
            agent_response: Agent's response
            session_id: Optional session identifier
            agent_type: Type of agent (react, cot, tot, scheduler)
            metadata: Additional metadata as dict
            
        Returns:
            Conversation ID
        """
        metadata_json = json.dumps(metadata) if metadata else None
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO conversations 
                (session_id, user_message, agent_response, agent_type, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, user_message, agent_response, agent_type, metadata_json))
            
            conn.commit()
            conversation_id = cursor.lastrowid
            
            logger.info(f"Saved conversation {conversation_id}")
            return conversation_id
    
    def search(
        self,
        query: str,
        limit: int = 10,
        agent_type: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Search conversations using full-text search
        
        Args:
            query: Search query
            limit: Maximum results
            agent_type: Filter by agent type
            session_id: Filter by session
            
        Returns:
            List of conversation dicts
        """
        sql = """
            SELECT c.*, 
                   rank
            FROM conversations c
            JOIN conversations_fts fts ON c.id = fts.id
            WHERE conversations_fts MATCH ?
        """
        
        params = [query]
        
        if agent_type:
            sql += " AND c.agent_type = ?"
            params.append(agent_type)
        
        if session_id:
            sql += " AND c.session_id = ?"
            params.append(session_id)
        
        sql += " ORDER BY rank, c.timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            
            results = []
            for row in cursor:
                result = dict(row)
                if result['metadata']:
                    result['metadata'] = json.loads(result['metadata'])
                results.append(result)
            
            logger.info(f"Search '{query}' returned {len(results)} results")
            return results
    
    def get_recent(
        self,
        limit: int = 10,
        agent_type: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get recent conversations
        
        Args:
            limit: Maximum results
            agent_type: Filter by agent type
            session_id: Filter by session
            
        Returns:
            List of conversation dicts
        """
        sql = "SELECT * FROM conversations WHERE 1=1"
        params = []
        
        if agent_type:
            sql += " AND agent_type = ?"
            params.append(agent_type)
        
        if session_id:
            sql += " AND session_id = ?"
            params.append(session_id)
        
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            
            results = []
            for row in cursor:
                result = dict(row)
                if result['metadata']:
                    result['metadata'] = json.loads(result['metadata'])
                results.append(result)
            
            logger.info(f"Retrieved {len(results)} recent conversations")
            return results
    
    def get_by_id(self, conversation_id: int) -> Optional[Dict]:
        """
        Get conversation by ID
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation dict or None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result['metadata']:
                    result['metadata'] = json.loads(result['metadata'])
                return result
            
            return None
    
    def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get all conversations in a session
        
        Args:
            session_id: Session identifier
            limit: Optional limit
            
        Returns:
            List of conversations in chronological order
        """
        sql = """
            SELECT * FROM conversations 
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """
        
        params = [session_id]
        
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            
            results = []
            for row in cursor:
                result = dict(row)
                if result['metadata']:
                    result['metadata'] = json.loads(result['metadata'])
                results.append(result)
            
            logger.info(f"Retrieved {len(results)} conversations for session {session_id}")
            return results
    
    def get_by_date_range(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        agent_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get conversations in date range
        
        Args:
            start_date: Start datetime
            end_date: End datetime (default: now)
            agent_type: Filter by agent type
            
        Returns:
            List of conversations
        """
        if end_date is None:
            end_date = datetime.now()
        
        sql = """
            SELECT * FROM conversations 
            WHERE timestamp BETWEEN ? AND ?
        """
        
        params = [start_date.isoformat(), end_date.isoformat()]
        
        if agent_type:
            sql += " AND agent_type = ?"
            params.append(agent_type)
        
        sql += " ORDER BY timestamp DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            
            results = []
            for row in cursor:
                result = dict(row)
                if result['metadata']:
                    result['metadata'] = json.loads(result['metadata'])
                results.append(result)
            
            logger.info(f"Retrieved {len(results)} conversations between {start_date} and {end_date}")
            return results
    
    def count(self, agent_type: Optional[str] = None) -> int:
        """
        Count total conversations
        
        Args:
            agent_type: Optional filter by agent type
            
        Returns:
            Total count
        """
        if agent_type:
            sql = "SELECT COUNT(*) FROM conversations WHERE agent_type = ?"
            params = (agent_type,)
        else:
            sql = "SELECT COUNT(*) FROM conversations"
            params = ()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchone()[0]
    
    def delete_old(self, days: int = 30) -> int:
        """
        Delete conversations older than specified days
        
        Args:
            days: Delete conversations older than this
            
        Returns:
            Number of deleted conversations
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM conversations 
                WHERE timestamp < datetime(?, 'unixepoch')
            """, (cutoff_date,))
            
            conn.commit()
            deleted = cursor.rowcount
            
            logger.info(f"Deleted {deleted} conversations older than {days} days")
            return deleted
    
    def clear_all(self):
        """Clear all conversations (use with caution!)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM conversations")
            conn.commit()
            logger.warning("Cleared all conversations")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored conversations
        
        Returns:
            Dict with statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            # Total count
            total = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            
            # By agent type
            by_agent = {}
            cursor = conn.execute("""
                SELECT agent_type, COUNT(*) as count
                FROM conversations
                WHERE agent_type IS NOT NULL
                GROUP BY agent_type
            """)
            for row in cursor:
                by_agent[row[0]] = row[1]
            
            # Date range
            cursor = conn.execute("""
                SELECT MIN(timestamp), MAX(timestamp)
                FROM conversations
            """)
            min_date, max_date = cursor.fetchone()
            
            return {
                'total_conversations': total,
                'by_agent_type': by_agent,
                'earliest_conversation': min_date,
                'latest_conversation': max_date
            }