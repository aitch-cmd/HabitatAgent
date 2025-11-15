from collections.abc import AsyncIterable
import json
from typing import Any

from utilities.common.file_loader import load_instructions_file
from google.adk.agents import LlmAgent
from google.adk import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.genai import types
from rich import print as rprint
from rich.syntax import Syntax
from utilities.mcp.mcp_connect import MCPConnector

from dotenv import load_dotenv
load_dotenv()

class ListingsAgent:
    """
    Listing Creation Agent for creating rental property listings.
    
    This agent:
    - Uses MCP tools for parsing, validating, and saving listings
    - Accepts unstructured property information
    - Guides users through confirmation and editing
    - Saves validated listings to MongoDB
    """

    def __init__(self):
        """
        Initialize the listing creation agent with instructions and MCP connector.
        """
        self.system_instruction = load_instructions_file("agents/listing/instructions.txt")
        self.description = load_instructions_file("agents/listing/descriptions.txt")
        
        # IMPORTANT: Only load the listings_mongodb MCP server
        self.MCPConnector = MCPConnector(server_names=["listings_mongodb"])
        
        self._agent = None
        self._user_id = "listings_agent_user"
        self._runner = None

    async def create(self):
        """
        Asynchronously create and initialize the agent with MCP tools.
        
        This method:
        1. Loads MCP tools (parse, update, save from listings_mongodb only)
        2. Builds the LLM agent with tools
        3. Creates the runner for executing agent tasks
        """
        self._agent = await self._build_agent()
        
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    async def _build_agent(self) -> LlmAgent:
        """
        Build the LLM agent with MCP listing creation tools.
        """
        mcp_toolsets = await self.MCPConnector.get_tools()

        return LlmAgent(
            name="listings_agent",
            model="gemini-2.5-flash",  
            instruction=self.system_instruction,
            description=self.description,
            tools=mcp_toolsets  
        )
    
    async def invoke(self, query: str, session_id: str) -> AsyncIterable[dict]:
        """
        Process a user query for creating a property listing.
        
        Args:
            query: User's input (property details or commands)
            session_id: Unique identifier for this conversation session
            
        Yields:
            dict: Progress updates and final results
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
            print_json_response(event, "================ LISTING EVENT ================")
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
                    'updates': "Processing your listing..."
                }


def print_json_response(response: Any, title: str) -> None:
    """Helper function to display formatted responses."""
    print(f"\n=== {title} ===")  
    try:
        if hasattr(response, "root"):
            data = response.root.model_dump(mode="json", exclude_none=True)
        else:
            data = response.model_dump(mode="json", exclude_none=True)
        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        rprint(syntax) 
        
    except Exception as e:
        rprint(f"[red bold]Error printing JSON:[/red bold] {e}")
        rprint(repr(response))