"""
Session Manager for HabitatOS V2.
Handles session lifecycle, routing decisions, and memory coordination.
"""

import uuid
from typing import Optional, Tuple
from datetime import datetime

from agents.memory.procedural_store import ProceduralMemoryStore
from agents.memory.context_protocol import (
    ProceduralMemory,
    ContextPackage,
    RoutingInfo,
    AgentResponse,
    HandoffSignal
)


class SessionManager:
    """
    Central session management for multi-turn conversations.
    
    Responsibilities:
    - Create and manage sessions
    - Determine message routing (direct to agent vs orchestrator)
    - Build context packages for agents
    - Process agent responses and handoff signals
    """

    def __init__(self):
        self.procedural_store = ProceduralMemoryStore()
        # TODO Phase 2: Add episodic and semantic stores

    def create_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        """
        Create a new session for user.
        
        Args:
            user_id: User identifier
            session_id: Optional custom session ID (generates UUID if not provided)
            
        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        self.procedural_store.create_session(session_id, user_id)
        return session_id

    def get_or_create_session(self, session_id: str, user_id: str) -> ProceduralMemory:
        """
        Get existing session or create new one.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            ProceduralMemory for the session
        """
        memory = self.procedural_store.get_session(session_id)
        if memory is None:
            memory = self.procedural_store.create_session(session_id, user_id)
        return memory

    def should_route_to_orchestrator(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """
        Determine if message should go to orchestrator or direct to active agent.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Tuple of (should_use_orchestrator, active_agent_name)
            - (True, None): No active agent, use orchestrator
            - (False, agent_name): Active agent exists, route directly
        """
        active_agent = self.procedural_store.get_active_agent(session_id)
        
        if active_agent is None:
            return (True, None)
        else:
            return (False, active_agent)

    def build_context_package(
        self,
        session_id: str,
        user_id: str,
        message: str,
        routed_via: str = "orchestrator",
        routing_reasoning: Optional[str] = None
    ) -> ContextPackage:
        """
        Build full context package for agent consumption.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            message: User's message
            routed_via: How the message was routed
            routing_reasoning: Why this agent was chosen
            
        Returns:
            ContextPackage with all available memory
        """
        # Get or create procedural memory
        procedural_memory = self.get_or_create_session(session_id, user_id)
        
        # Refresh TTL on activity
        self.procedural_store.refresh_ttl(session_id)
        
        # Build routing info
        routing_info = RoutingInfo(
            source="direct_session" if routed_via != "orchestrator" else "orchestrator",
            reasoning=routing_reasoning,
            confidence=1.0 if routed_via != "orchestrator" else 0.8
        )
        
        # TODO Phase 2: Load episodic and semantic memory
        
        return ContextPackage(
            message=message,
            routing_info=routing_info,
            procedural_memory=procedural_memory,
            episodic_memory=None,
            semantic_memory=None
        )

    def process_agent_response(
        self,
        session_id: str,
        agent_name: str,
        response: AgentResponse
    ) -> None:
        """
        Process agent response and update session state.
        
        Args:
            session_id: Session identifier
            agent_name: Name of responding agent
            response: Agent's response with handoff signal
        """
        # Handle handoff signal
        if response.handoff_signal == HandoffSignal.COMPLETE:
            # Task complete, clear active agent
            self.procedural_store.clear_active_agent(session_id)
            
        elif response.handoff_signal == HandoffSignal.CONTINUE:
            # Task in progress, update context
            if response.updated_procedural_memory:
                self.procedural_store.update_session(
                    session_id,
                    active_agent=agent_name,
                    task_state=response.updated_procedural_memory.get("task_state"),
                    task_context=response.updated_procedural_memory.get("task_context", {})
                )
            else:
                # Just refresh activity, keep agent active
                self.procedural_store.update_session(
                    session_id,
                    active_agent=agent_name
                )
                
        elif response.handoff_signal == HandoffSignal.ESCALATE:
            # User wants different agent, clear and route to orchestrator next
            self.procedural_store.clear_active_agent(session_id)
        
        # TODO Phase 2: Update episodic memory with conversation turn
        # TODO Phase 2: Update semantic memory with learned facts

    def set_active_agent(
        self,
        session_id: str,
        agent_name: str,
        initial_state: str = "started",
        initial_context: Optional[dict] = None
    ) -> None:
        """
        Explicitly set active agent (called by orchestrator after routing decision).
        
        Args:
            session_id: Session identifier
            agent_name: Name of agent to activate
            initial_state: Initial task state
            initial_context: Initial task context
        """
        self.procedural_store.set_active_agent(
            session_id,
            agent_name,
            initial_state,
            initial_context
        )

    def end_session(self, session_id: str) -> None:
        """
        End and cleanup session.
        
        Args:
            session_id: Session identifier
        """
        self.procedural_store.delete_session(session_id)
        # TODO Phase 2: Archive episodic memory with summary

    def get_session_info(self, session_id: str) -> Optional[dict]:
        """
        Get session info for debugging/monitoring.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session info dict or None
        """
        memory = self.procedural_store.get_session(session_id)
        if memory is None:
            return None
        return {
            "session_id": memory.session_id,
            "user_id": memory.user_id,
            "active_agent": memory.active_agent,
            "task_state": memory.task_state,
            "turn_count": memory.turn_count,
            "last_activity": memory.last_activity
        }
