from collections.abc import AsyncIterable
import json
from typing import Any

from V2.utilities.common.file_loader import load_instructions_file
from google.adk.agents import LlmAgent
from google.adk import Runner

from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService

from google.genai import types
from rich import print as rprint
from rich.syntax import Syntax

from V2.utilities.mcp.mcp_connect import MCPConnector

from dotenv import load_dotenv
load_dotenv()


class SearchAgent:
    """
    Search Agent for finding rental properties.
    
    This agent:
    - Uses MCP property search tool for MongoDB + hybrid reranking
    - Formats search results in a user-friendly way
    - Provides helpful suggestions when no results are found
    - Handles various search queries (location, price, amenities, etc.)
    """

    def __init__(self):
        """
        Initialize the search agent with instructions and MCP connector.
        """
        # Load the agent's system instructions (how to behave)
        self.system_instruction = load_instructions_file("V2/agentsV2/search/instructions.txt")
        
        # Load the agent's description (what it does)
        self.description = load_instructions_file("V2/agentsV2/search/descriptions.txt")
        
        # Initialize MCP connector to access property search tool
        self.MCPConnector = MCPConnector()
        
        # These will be initialized in create()
        self._agent = None
        self._user_id = "search_agent_user"
        self._runner = None

    async def create(self):
        """
        Asynchronously create and initialize the agent with MCP tools.
        
        This method:
        1. Loads MCP tools (property search)
        2. Builds the LLM agent with tools
        3. Creates the runner for executing agent tasks
        """
        # Build the agent with MCP tools
        self._agent = await self._build_agent()
        
        # Create the runner for executing agent tasks
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    async def _build_agent(self) -> LlmAgent:
        """
        Build the LLM agent with MCP property search tools.
        
        Returns:
            LlmAgent: Configured Gemini agent with property search capabilities
        """
        # Get MCP tools (property search server)
        mcp_toolsets = await self.MCPConnector.get_tools()

        return LlmAgent(
        name="search_agent",
        model="gemini-2.0-flash-exp",  
        instruction=self.system_instruction,
        description=self.description,
        tools=mcp_toolsets  
    )
    
    async def invoke(self, query: str, session_id: str) -> AsyncIterable[dict]:
        """
        Invoke the search agent to find properties.
        
        Returns a stream of updates back to the caller as the agent searches.
        
        Args:
            query: User's natural language search query
            session_id: Session ID for maintaining conversation context
            
        Yields:
            dict: Progress updates and final results
                {
                    'is_task_complete': bool,  # Indicates if the search is complete
                    'updates': str,  # Progress messages during search
                    'content': str  # Final search results if complete
                }
        
        Example Flow:
            User: "Find 2BHK apartments in Bangalore under 20k"
            
            Yield 1: {'is_task_complete': False, 'updates': 'Searching properties...'}
            Yield 2: {'is_task_complete': False, 'updates': 'Analyzing results...'}
            Yield 3: {'is_task_complete': True, 'content': 'Found 5 properties...'}
        """

        # Ensure the runner is initialized
        if not self._runner:
            raise ValueError("Runner is not initialized. Call create() first.")
    
        # Get or create a session for this conversation
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            session_id=session_id,
            user_id=self._user_id,
        )

        # If session doesn't exist, create a new one
        if not session:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                session_id=session_id,
                user_id=self._user_id,
            )
        
        # Format the user's query as a Content object for Gemini
        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )

        # Run the agent and stream back events
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session_id,
            new_message=user_content
        ):
            # Log the event for debugging (optional - remove in production)
            print_json_response(event, "================ SEARCH EVENT ================")
            
            # Check if this is the final response from the agent
            print(f"is_final_response: {event.is_final_response()}")    
            
            if event.is_final_response():
                # Extract the final search results
                final_response = ""
                if event.content and event.content.parts and event.content.parts[-1].text:
                    final_response = event.content.parts[-1].text
                
                # Yield the final results
                yield {
                    'is_task_complete': True,
                    'content': final_response
                }
            else:
                # Still processing - yield a progress update
                yield {
                    'is_task_complete': False,
                    'updates': "Searching for properties matching your criteria..."
                }


def print_json_response(response: Any, title: str) -> None:
    """
    Helper function to display formatted and color-highlighted responses.
    
    Useful for debugging - shows the full event structure from Gemini.
    
    Args:
        response: The response object from the agent
        title: Section title for clarity
    """
    print(f"\n=== {title} ===")  # Section title for clarity
    try:
        # Check if response is wrapped by SDK
        if hasattr(response, "root"):
            data = response.root.model_dump(mode="json", exclude_none=True)
        else:
            data = response.model_dump(mode="json", exclude_none=True)

        # Convert dict to pretty JSON string
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        # Apply syntax highlighting for better readability
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        rprint(syntax)  # Print with color
        
    except Exception as e:
        # Print fallback text if something fails
        rprint(f"[red bold]Error printing JSON:[/red bold] {e}")
        rprint(repr(response))