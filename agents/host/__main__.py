from a2a.types import AgentSkill, AgentCard, AgentCapabilities
import click
from a2a.server.request_handlers import DefaultRequestHandler
from agents.host.agent_executor import HostAgentExecutor 
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
import uvicorn
import asyncio


async def initialize_and_run(host: str, port: int):
    """
    Initialize the Search Agent and start the server.
    """
    
    # Define what this agent can do
    skill = AgentSkill(
        id="host_agent_skill",
        name="host_agent_skill",
        description="A simple orchestrator for orchestration with A2A agents and MCP tools",
        tags=["host", "orchestrator"],
        examples=[
            "Find 2BHK apartments in Bangalore under 20000",
            "Show me furnished flats near MIT with parking",
            "Post my listings and upload to your database"
        ]
    )
    
    # Create the agent's business card
    agent_card = AgentCard(
        name="host_agent",
        description="A simple orchestrator for orchestrating tasks",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[skill],
        capabilities=AgentCapabilities(streaming=True),
    )

    print("Pre-initializing Search Agent...")
    executor = HostAgentExecutor() 
    await executor.create()
    print("Search Agent ready to accept requests")

   
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore()
    )

    # Create the A2A server application
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

    print(f"🔍 Starting Search Agent on http://{host}:{port}")
    print(f"📋 Agent Card available at: http://{host}:{port}/.well-known/agent.json")
    
    # Run the server
    config = uvicorn.Config(server.build(), host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


@click.command()
@click.option("--host", default="localhost", help="Host for the agent server.")
@click.option("--port", default=8001, help="Port for the agent server.")
def main(host: str, port: int):
    """
    Start the Search Agent server.
    """
    # Run the async initialization and server
    asyncio.run(initialize_and_run(host, port))


if __name__ == "__main__":
    main()