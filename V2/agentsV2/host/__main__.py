from a2a.types import AgentSkill, AgentCard, AgentCapabilities
import click
from a2a.server.request_handlers import DefaultRequestHandler
from agents.host_agent.agent_executor import HostAgentExecutor 
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
import uvicorn

@click.command()
@click.option("--host", default="localhost", help="Host for the agent server.")
@click.option("--port", default=8001, help="Port for the agent server.")
def main(host: str, port: int):
    skill = AgentSkill(
        id="host_agent_skill",
        name="host_agent_skill",
        description="Orchestrator for property management - routes requests for listing creation, property search, and alert management.",
        tags=["host", "orchestrator", "property", "accommodation"],
        examples=[
            "I want to list my property for rent",
            "Help me find accommodations near my university",
            "Create an alert for 2BHK apartments under $1000"
        ]
    )
    agent_card = AgentCard(
        name="host_agent",
        description="Property management orchestrator that routes requests to specialized agents for listings, search, and alerts",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[skill],
        capabilities=AgentCapabilities(streaming=True),
    )

    request_handler=DefaultRequestHandler(
        agent_executor=HostAgentExecutor(),
        task_store=InMemoryTaskStore()
    )

    server=A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

    uvicorn.run(server.build(), host=host, port=port)

if __name__=="__main__":
    main()