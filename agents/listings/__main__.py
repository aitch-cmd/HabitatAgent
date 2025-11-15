from a2a.types import AgentSkill, AgentCard, AgentCapabilities
import click
from a2a.server.request_handlers import DefaultRequestHandler
from agents.listings.agent_executor import ListingAgentExecutor 
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
import uvicorn
import asyncio


async def initialize_and_run(host: str, port: int):
    """
    Initialize the Property Listing Creation Agent and start the server.
    """
    
    skill = AgentSkill(
        id="property_listing_creation_skill",
        name="property_listing_creation_skill",
        description="Create rental property listings from unstructured text. Accepts property details in any format, parses them using AI, validates data, shows formatted summary for confirmation, and saves to MongoDB database.",
        tags=["listing", "rental", "property", "create", "publish", "landlord", "accommodation"],
        examples=[
            "I want to list my 2BHK apartment in Koramangala for 30000 per month",
            "Create listing: 3BR house in Whitefield, ₹50k rent, garden, pets allowed, available Jan 1",
            "List my studio apartment near MG Road, rent 15k, fully furnished with AC and wifi",
            "I have a property for rent: 2 bedroom flat in Indiranagar, 35000/month, parking available",
            "Help me list my apartment: HSR Layout, 2BHK, 28k per month, semi-furnished, available December"
        ]
    )
    
    agent_card = AgentCard(
        name="listing_agent",
        description="Property listing creation agent that helps landlords and property owners create rental listings through conversational interface. Accepts unstructured property information, parses it intelligently, validates required fields, allows edits, and stores listings in MongoDB after user confirmation.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[skill],
        capabilities=AgentCapabilities(streaming=True),
    )

    # Pre-initialize the executor
    print("🔄 Pre-initializing Listing Creation Agent...")
    executor = ListingAgentExecutor()
    await executor.create()
    print("✅ Listing Creation Agent ready to accept requests")

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore()
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

    print(f"Starting Listing Creation Agent on http://{host}:{port}")
    print(f"Agent Card available at: http://{host}:{port}/.well-known/agent.json")
    print(f"Agent accepts natural language property descriptions and creates structured listings")
    
    # Run the server
    config = uvicorn.Config(server.build(), host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


@click.command()
@click.option("--host", default="localhost", help="Host for the agent server.")
@click.option("--port", default=8004, help="Port for the agent server.")
def main(host: str, port: int):
    """
    Start the Property Listing Creation Agent server.
    
    This agent helps users create property listings by:
    - Accepting unstructured property information in any format
    - Showing formatted summaries for confirmation
    - Allowing natural language edits
    - Saving validated listings to MongoDB
    """
    asyncio.run(initialize_and_run(host, port))


if __name__ == "__main__":
    main()