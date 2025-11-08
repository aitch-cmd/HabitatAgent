"""
Search Agent Executor
Bridges the search agent with the A2A framework's execution model.
"""

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater

from V2.agentsV2.search.agent import SearchAgent
from a2a.utils import (
    new_task,
    new_agent_text_message
)

from a2a.utils.errors import ServerError

from a2a.types import (
    Task,
    TaskState,
    UnsupportedOperationError
)

from V2.utilities.mcp.mcp_helpers import MCPHelpers
from V2.utilities.mcp.mcp_connect import MCPConnector

import asyncio
import json
import os


class SearchAgentExecutor(AgentExecutor):
    """
    Implements the AgentExecutor interface to integrate the 
    search agent with the A2A framework.
    
    This executor:
    1. Receives property search requests from users
    2. Uses MCP property search tool via MCPHelpers
    3. Manages task lifecycle (working → completed/failed)
    4. Streams progress updates back to caller
    5. Handles errors gracefully
    """

    def __init__(self):
        self.agent = SearchAgent()
        self.mcp_connector: MCPConnector = None
        self._initialized = False

    async def _initialize_mcp(self):
        """
        Initialize MCP connector once at startup (not per request).
        """
        if not self.mcp_connector:
            print("🔧 Initializing MCP property search services...")
            
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'utilities', 'mcp', 'mcp_config.json'
            )
            
            self.mcp_connector = MCPConnector(config_file=config_path)
            
            # ✅ Actually load the tools
            await self.mcp_connector.get_tools()
            
            print("✅ MCP property search tools loaded and ready")

    async def create(self):
        """
        Factory method to initialize the SearchAgentExecutor.
        Now also initializes MCP at startup.
        """
        print("🚀 Initializing Search Agent...")
        await self.agent.create()
        await self._initialize_mcp()  # Initialize MCP at startup
        self._initialized = True
        print("✅ Search Agent fully initialized and ready")

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Executes the search agent with the provided context and event queue.
        
        This is the main entry point called by the A2A framework when a 
        search request arrives.
        
        Args:
            context: Contains the user's search query and request metadata
            event_queue: Channel for sending status updates back to the caller
        """
        
        # Ensure the agent is initialized before processing requests
        if not self._initialized:
            await self.create()
        
        # Extract the user's actual search query from the request context
        query = context.get_user_input()
        
        # Get the current task from context (may be None if this is a new request)
        task = context.current_task
        
        # If no existing task, create a new one and send it to the event queue
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        
        # Get task identifiers
        task_id = task.id
        context_id = task.context_id
        
        # Create a TaskUpdater helper to easily send status updates for this task
        updater = TaskUpdater(event_queue, task_id, context_id)
        
        try:
            # Step 1: Analyze requirements
            await updater.update_status(
                TaskState.working,
                new_agent_text_message("🏠 Analyzing your requirements...", context_id, task_id)
            )
            
            # Step 2: Search properties using MCP tool
            search_result = await self._search_properties_via_mcp(
                user_query=query,
                max_results=10,
                updater=updater,
                context_id=context_id,
                task_id=task_id
            )
            
            # Step 3: Check search status
            if search_result.get("status") == "error":
                error_msg = search_result.get("message", "Unknown error occurred")
                await updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(f"❌ {error_msg}", context_id, task_id)
                )
                return
            
            # Step 4: Format results for user
            await updater.update_status(
                TaskState.working,
                new_agent_text_message("📊 Formatting results...", context_id, task_id)
            )
            
            formatted_output = await self._format_search_results(search_result)
            
            # Step 5: Send final results
            print(f"✅ Search completed: Found {search_result.get('count', 0)} properties")
            
            await updater.update_status(
                TaskState.completed,
                new_agent_text_message(formatted_output, context_id, task_id)
            )
            
            # Small delay to ensure the completion message is processed
            await asyncio.sleep(0.1)
                    
        except Exception as e:
            # Something went wrong during search execution
            error_msg = f"Search failed: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Send "failed" status with error details
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"❌ {error_msg}\nPlease try refining your search criteria.",
                    context_id,
                    task_id
                )
            )
            
            # Re-raise the exception so it can be logged/handled by the framework
            raise

    async def _search_properties_via_mcp(
        self, 
        user_query: str, 
        max_results: int,
        updater: TaskUpdater,
        context_id: str,
        task_id: str
    ) -> dict:
        """
        Search for properties using already-initialized MCP connector.
        """
        try:
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    f"🔍 Searching properties: '{user_query}'...", 
                    context_id, 
                    task_id
                )
            )
            
            result = await MCPHelpers.call_tool(
                self.mcp_connector,
                "property_search",
                "search_properties",
                {
                    "user_query": user_query,
                    "max_results": max_results
                }
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error searching properties: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "count": 0,
                "results": []
            }
        
    async def _format_search_results(self, search_result: dict) -> str:
        """
        Format search results into a human-readable message.
        
        Args:
            search_result: Raw search results from MCP tool
            
        Returns:
            str: Formatted message for the user
        """
        status = search_result.get("status", "error")
        
        if status == "error":
            return f"❌ Search failed: {search_result.get('message', 'Unknown error')}"
        
        count = search_result.get("count", 0)
        properties = search_result.get("results", [])
        
        if count == 0:
            return (
                "No properties found matching your criteria. 😔\n\n"
                "**Suggestions:**\n"
                "- Try increasing your budget\n"
                "- Expand the search location\n"
                "- Reduce the number of bedrooms\n"
                "- Remove some amenity requirements"
            )
        
        # Build formatted output
        output = f"Found **{count}** matching properties! 🏠\n\n"
        
        for idx, prop in enumerate(properties[:5], 1):  # Show top 5
            title = prop.get("title", "Untitled Property")
            price = prop.get("rent_price", "N/A")
            bedrooms = prop.get("bedroom", "N/A")
            bathrooms = prop.get("bathroom", "N/A")
            location = prop.get("location", "Location not specified")
            
            # Format price
            if isinstance(price, (int, float)):
                price_str = f"₹{price:,.0f}/month"
            else:
                price_str = str(price)
            
            # Get amenities
            amenities = prop.get("amenities", {})
            appliances = amenities.get("appliances", [])
            utilities = amenities.get("utilities_included", [])
            
            amenities_text = []
            if appliances:
                amenities_text.extend(appliances[:3])
            if utilities:
                amenities_text.extend(utilities[:2])
            
            amenities_str = ", ".join(amenities_text[:5]) if amenities_text else "Not specified"
            
            # Build property entry
            output += f"**{idx}. {title}**\n"
            output += f"   💰 Rent: {price_str}\n"
            output += f"   🛏️  Bedrooms: {bedrooms} | Bathrooms: {bathrooms}\n"
            output += f"   📍 Location: {location}\n"
            output += f"   ✨ Amenities: {amenities_str}\n\n"
        
        if count > 5:
            output += f"\n_...and {count - 5} more properties. Refine your search for specific results._"
        
        return output

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> Task | None:
        """
        Handles task cancellation requests.
        
        Currently not implemented - raises an error if someone tries to cancel.
        
        Args:
            request: The cancellation request context
            event_queue: Queue for sending events
            
        Raises:
            ServerError: Always, because cancellation is not supported
        """
        raise ServerError(error=UnsupportedOperationError())