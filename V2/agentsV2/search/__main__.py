"""
Search Agent Server
Helps students find rental accommodations using natural language queries.
"""

from a2a.types import AgentSkill, AgentCard, AgentCapabilities
import click
from a2a.server.request_handlers import DefaultRequestHandler
from V2.agentsV2.search.agent_executor import SearchAgentExecutor 
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
import uvicorn
import asyncio


async def initialize_and_run(host: str, port: int):
    """
    Initialize the Search Agent and start the server.
    """
    
    skill = AgentSkill(
        id="property_search_skill",
        name="property_search_skill",
        description="Search for rental properties using natural language queries with filters for location, price, bedrooms, and amenities.",
        tags=["search", "rental", "accommodation", "student", "property"],
        examples=[
            "Find 2BHK apartments in Bangalore under 20000",
            "Show me furnished flats near MIT with parking",
            "3BHK pet-friendly apartment under 30k",
            "Studio apartment in Koramangala with gym",
            "Looking for 1BHK near MG Road under 15000"
        ]
    )
    
    agent_card = AgentCard(
        name="search_agent",
        description="Student accommodation search agent that finds rental properties based on natural language queries, preferences, and budget constraints.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[skill],
        capabilities=AgentCapabilities(streaming=True),
    )

    # Pre-initialize the executor
    print("🔄 Pre-initializing Search Agent...")
    executor = SearchAgentExecutor()
    await executor.create()
    print("✅ Search Agent ready to accept requests")

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore()
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

    print(f"🚀 Starting Search Agent on http://{host}:{port}")
    print(f"📋 Agent Card available at: http://{host}:{port}/.well-known/agent.json")
    
    # Run the server
    config = uvicorn.Config(server.build(), host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


@click.command()
@click.option("--host", default="localhost", help="Host for the agent server.")
@click.option("--port", default=8003, help="Port for the agent server.")
def main(host: str, port: int):
    """
    Start the Search Agent server.
    
    This agent helps students find rental accommodations based on natural language queries.
    It uses MongoDB filtering and hybrid reranking to find the best matches.
    """
    # Run the async initialization and server
    asyncio.run(initialize_and_run(host, port))


if __name__ == "__main__":
    main()