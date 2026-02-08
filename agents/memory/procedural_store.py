"""
Procedural Memory Store for HabitatOS V2.
Redis-based working memory for active sessions and task state.
"""

import json
from typing import Optional
from datetime import datetime

from db.redis_client import get_redis
from agents.memory.context_protocol import ProceduralMemory


# Default TTL: 60 minutes
DEFAULT_SESSION_TTL = 3600


class ProceduralMemoryStore:
    """
    Redis-based store for procedural (working) memory.
    Handles current task state, active agent tracking, and session context.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_SESSION_TTL):
        self.redis = get_redis()
        self.ttl = ttl_seconds
        self.key_prefix = "session:"

    def _make_key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"{self.key_prefix}{session_id}"

    def create_session(self, session_id: str, user_id: str) -> ProceduralMemory:
        """
        Create a new session with empty procedural memory.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            
        Returns:
            ProceduralMemory: New procedural memory instance
        """
        memory = ProceduralMemory(
            session_id=session_id,
            user_id=user_id
        )
        self._save(memory)
        return memory

    def get_session(self, session_id: str) -> Optional[ProceduralMemory]:
        """
        Retrieve session procedural memory.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ProceduralMemory if exists, None otherwise
        """
        key = self._make_key(session_id)
        data = self.redis.get(key)
        
        if data is None:
            return None
        
        try:
            parsed = json.loads(data)
            return ProceduralMemory.from_dict(parsed)
        except (json.JSONDecodeError, KeyError):
            return None

    def update_session(
        self,
        session_id: str,
        active_agent: Optional[str] = None,
        task_state: Optional[str] = None,
        task_context: Optional[dict] = None,
        increment_turn: bool = True
    ) -> Optional[ProceduralMemory]:
        """
        Update existing session memory.
        
        Args:
            session_id: Session identifier
            active_agent: Currently active agent (None to clear)
            task_state: Current task state
            task_context: Task-specific context data
            increment_turn: Whether to increment turn counter
            
        Returns:
            Updated ProceduralMemory, or None if session doesn't exist
        """
        memory = self.get_session(session_id)
        if memory is None:
            return None
        
        if active_agent is not None:
            memory.active_agent = active_agent if active_agent != "" else None
        if task_state is not None:
            memory.task_state = task_state if task_state != "" else None
        if task_context is not None:
            memory.task_context = task_context
        if increment_turn:
            memory.turn_count += 1
        
        memory.last_activity = datetime.utcnow().isoformat()
        self._save(memory)
        return memory

    def clear_active_agent(self, session_id: str) -> Optional[ProceduralMemory]:
        """
        Clear active agent (task complete/escalate).
        
        Args:
            session_id: Session identifier
            
        Returns:
            Updated ProceduralMemory
        """
        return self.update_session(
            session_id,
            active_agent="",  # Clears to None
            task_state="",
            task_context={},
            increment_turn=False
        )

    def set_active_agent(
        self,
        session_id: str,
        agent_name: str,
        task_state: str = "started",
        task_context: Optional[dict] = None
    ) -> Optional[ProceduralMemory]:
        """
        Set active agent for session (agent takes control).
        
        Args:
            session_id: Session identifier
            agent_name: Name of agent taking control
            task_state: Initial task state
            task_context: Initial task context
            
        Returns:
            Updated ProceduralMemory
        """
        return self.update_session(
            session_id,
            active_agent=agent_name,
            task_state=task_state,
            task_context=task_context or {}
        )

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session from memory.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if didn't exist
        """
        key = self._make_key(session_id)
        return self.redis.delete(key) > 0

    def refresh_ttl(self, session_id: str) -> bool:
        """
        Refresh session TTL (extend expiry).
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if refreshed, False if session doesn't exist
        """
        key = self._make_key(session_id)
        return self.redis.expire(key, self.ttl)

    def get_active_agent(self, session_id: str) -> Optional[str]:
        """
        Quick check for active agent without loading full memory.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Agent name if active, None otherwise
        """
        memory = self.get_session(session_id)
        if memory is None:
            return None
        return memory.active_agent

    def _save(self, memory: ProceduralMemory) -> None:
        """Save procedural memory to Redis with TTL."""
        key = self._make_key(memory.session_id)
        data = json.dumps(memory.to_dict())
        self.redis.setex(key, self.ttl, data)
