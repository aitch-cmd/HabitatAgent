"""
Context Protocol Schemas for HabitatOS V2.
Defines the data structures for memory and agent communication.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal, Any
from datetime import datetime
from enum import Enum


class HandoffSignal(str, Enum):
    """Agent handoff signals for session management."""
    CONTINUE = "CONTINUE"   # Task in progress, keep agent active
    COMPLETE = "COMPLETE"   # Task finished, release to orchestrator
    ESCALATE = "ESCALATE"   # User wants different agent


@dataclass
class ProceduralMemory:
    """
    Working memory: Current task state and context.
    Stored in Redis with TTL.
    """
    session_id: str
    user_id: str
    active_agent: Optional[str] = None
    task_state: Optional[str] = None
    task_context: dict = field(default_factory=dict)
    turn_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "active_agent": self.active_agent,
            "task_state": self.task_state,
            "task_context": self.task_context,
            "turn_count": self.turn_count,
            "created_at": self.created_at,
            "last_activity": self.last_activity
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ProceduralMemory":
        return cls(
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            active_agent=data.get("active_agent"),
            task_state=data.get("task_state"),
            task_context=data.get("task_context", {}),
            turn_count=data.get("turn_count", 0),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            last_activity=data.get("last_activity", datetime.utcnow().isoformat())
        )


@dataclass
class EpisodicTurn:
    """Single turn in conversation history."""
    turn: int
    role: Literal["user", "assistant"]
    content: str
    timestamp: str
    agent: Optional[str] = None
    routed_to: Optional[str] = None


@dataclass 
class EpisodicMemory:
    """
    Short-term memory: Conversation history.
    Stored in MongoDB.
    """
    session_id: str
    user_id: str
    conversation_history: list[EpisodicTurn] = field(default_factory=list)
    summary: Optional[str] = None
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    ended_at: Optional[str] = None


@dataclass
class SemanticMemory:
    """
    Long-term memory: User profile and learned facts.
    Stored in MongoDB permanently.
    """
    user_id: str
    user_profile: dict = field(default_factory=dict)
    preferences: dict = field(default_factory=dict)
    owned_properties: list[dict] = field(default_factory=list)
    interaction_history: dict = field(default_factory=dict)
    learned_facts: list[str] = field(default_factory=list)


@dataclass
class RoutingInfo:
    """Information about how message was routed."""
    source: Literal["orchestrator", "direct_session"]
    reasoning: Optional[str] = None
    confidence: float = 1.0


@dataclass
class ContextPackage:
    """
    Full context passed to agents.
    Contains all memory types and routing information.
    """
    message: str
    routing_info: RoutingInfo
    procedural_memory: Optional[ProceduralMemory] = None
    episodic_memory: Optional[EpisodicMemory] = None
    semantic_memory: Optional[SemanticMemory] = None
    
    def to_dict(self) -> dict:
        return {
            "message": self.message,
            "routing_info": {
                "source": self.routing_info.source,
                "reasoning": self.routing_info.reasoning,
                "confidence": self.routing_info.confidence
            },
            "procedural_memory": self.procedural_memory.to_dict() if self.procedural_memory else None,
            "episodic_memory": None,  # TODO: Implement in Phase 2
            "semantic_memory": None   # TODO: Implement in Phase 2
        }


@dataclass
class MemoryUpdate:
    """Updates to apply to memory stores after agent response."""
    add_to_semantic: list[str] = field(default_factory=list)
    episodic_note: Optional[str] = None


@dataclass
class AgentResponse:
    """
    Standardized response from agents.
    Includes handoff signal and memory updates.
    """
    message: str
    handoff_signal: HandoffSignal = HandoffSignal.COMPLETE
    updated_procedural_memory: Optional[dict] = None
    memory_updates: Optional[MemoryUpdate] = None
    suggested_next_agent: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "message": self.message,
            "handoff_signal": self.handoff_signal.value,
            "updated_procedural_memory": self.updated_procedural_memory,
            "memory_updates": {
                "add_to_semantic": self.memory_updates.add_to_semantic if self.memory_updates else [],
                "episodic_note": self.memory_updates.episodic_note if self.memory_updates else None
            },
            "suggested_next_agent": self.suggested_next_agent
        }
