from collections.abc import AsyncIterable
import json
from typing import Any
from uuid import uuid4
from V2.utilities.a2a.agent_connect import AgentConnector
from V2.utilities.a2a.agent_discovery import AgentDiscovery
from V2.utilities.common.file_loader import load_instructions_file
from google.adk.agents import LlmAgent
from google.adk import Runner

from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.tools.function_tool import FunctionTool

from google.genai import types
from rich import print as rprint
from rich.syntax import Syntax

from a2a.types import AgentCard

from dotenv import load_dotenv
load_dotenv()

class HostAgent:
    """
    Orchestrator Agent
    - Discovers A2A agents via agent discovery
    - Routes the user query by picking the correct agent
    """

    def __init__(self):
        self.system_instruction = load_instructions_file("agents/host_agent/instructions.txt")
        self.description = load_instructions_file("agents/host_agent/descriptions.txt")
        self.AgentDiscovery = AgentDiscovery()
        self._agent = None
        self._user_id = "host_agent_user"
        self._runner = None

    async def create(self):
        self._agent = await self._build_agent()
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    async def _list_agents(self) -> list[dict]:
        """
        A2A tool: returns the list of dictionaries with agent card 
        objects of registered A2A child agents

        Returns:
            list[dict]: List of agent card object dictionaries
        """
        cards = await self.AgentDiscovery.list_agents_cards()

        return [card.model_dump(exclude_none=True) for card in cards]

    async def _delegate_task(self, agent_name: str, message: str) -> str:
        """
        Delegate a task to a child agent by name or ID
        
        Args:
            agent_name: Name or ID of the agent to delegate to
            message: Message/task to send to the agent
            
        Returns:
            str: Response from the child agent
        """
        cards = await self.AgentDiscovery.list_agents_cards()
        
        print(f"🔍 Looking for agent: {agent_name}")
        print(f"📋 Available agents: {[card.name for card in cards]}")

        matched_card = None
        for card in cards:
            if card.name.lower() == agent_name.lower():
                matched_card = card
                break
            elif getattr(card, "id", "").lower() == agent_name.lower():
                matched_card = card
                break
        
        if matched_card is None:
            available = [c.name for c in cards]
            return f"❌ Agent '{agent_name}' not found. Available agents: {available}"
        
        print(f"✅ Delegating to {matched_card.name}")
        connector = AgentConnector(agent_card=matched_card)

        try:
            response = await connector.send_task(message=message, session_id=str(uuid4()))
            return response
        except Exception as e:
            return f"❌ Error delegating to {agent_name}: {str(e)}"
    
    async def _build_agent(self) -> LlmAgent:
        """
        Build the host agent with delegation tools only.
        The host agent routes requests to specialized child agents.
        
        Returns:
            LlmAgent: Configured host agent with delegation capabilities
        """
        return LlmAgent(
            name="host_agent",  
            model="gemini-2.5-flash",
            instruction=self.system_instruction,
            description=self.description,
            tools=[  
                FunctionTool(self._delegate_task),
                FunctionTool(self._list_agents),
            ]
        )
    
    async def invoke(self, query: str, session_id: str) -> AsyncIterable[dict]:
        """
        Invoke the agent
        Return a stream of updates back to the caller as the agent processes the query

        Yields:
            dict: Stream of updates with structure:
                {
                    'is_task_complete': bool,  # Indicates if the task is complete
                    'updates': str,  # Updates on the task progress
                    'content': str  # Final result of the task if complete
                }
        
        Args:
            query: User query to process
            session_id: Session identifier for conversation continuity
        """

        if not self._runner:
            raise ValueError("Runner is not initialized. Call create() first.")
    
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            session_id=session_id,
            user_id=self._user_id,
        )

        if not session:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                session_id=session_id,
                user_id=self._user_id,
            )
        
        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )

        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session_id,
            new_message=user_content
        ):
            print_json_response(event, "================ HOST AGENT EVENT ================")
            
            print(f"is_final_response: {event.is_final_response()}")    
            
            if event.is_final_response():
                
                final_response = ""
                if event.content and event.content.parts and event.content.parts[-1].text:
                    final_response = event.content.parts[-1].text
                
                yield {
                    'is_task_complete': True,
                    'content': final_response
                }
            else:
                yield {
                    'is_task_complete': False,
                    'updates': "Host agent is routing your request..."
                }


def print_json_response(response: Any, title: str) -> None:
    """
    Displays a formatted and color-highlighted view of the response
    
    Args:
        response: Response object to display
        title: Section title for the output
    """
    print(f"\n=== {title} ===")  # Section title for clarity
    try:
        if hasattr(response, "root"):  # Check if response is wrapped by SDK
            data = response.root.model_dump(mode="json", exclude_none=True)
        else:
            data = response.model_dump(mode="json", exclude_none=True)

        json_str = json.dumps(data, indent=2, ensure_ascii=False)  # Convert dict to pretty JSON string
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)  # Apply syntax highlighting
        rprint(syntax)  # Print it with color
    except Exception as e:
        # Print fallback text if something fails
        rprint(f"[red bold]Error printing JSON:[/red bold] {e}")
        rprint(repr(response))