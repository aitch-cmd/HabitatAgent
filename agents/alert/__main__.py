from a2a.types import AgentSkill, AgentCard, AgentCapabilities
import click
from a2a.server.request_handlers import DefaultRequestHandler
from agents.alert.agent_executor import AlertAgentExecutor 
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
import uvicorn
import asyncio


async def initialize_and_run(host: str, port: int):
    """
    Initialize the Property Alert Agent and start the server.
    """
    
    skill = AgentSkill(
        id="property_alert_skill",
        name="property_alert_skill",
        description="Create and manage property alerts for rental listings. Set up custom alerts based on location and price, receive instant email notifications when matching properties are listed, view and delete existing alerts, and search current property listings.",
        tags=["alert", "notification", "property", "rental", "search", "email", "tracking", "real-time"],
        examples=[
            "Alert me for properties in Jersey City under $3000 at john@example.com",
            "I want to get notified about apartments in Brooklyn around $2500, email: sarah@email.com",
            "Set up an alert for me: Manhattan apartments under 4k, contact mike@mail.com",
            "Show my alerts for john@example.com",
            "Search for properties in Jersey City under $3000",
            "Delete my alert",
            "What apartments are available in Brooklyn?",
            "I'm looking for a place in New York under $2800, notify me at user@email.com"
        ]
    )
    
    agent_card = AgentCard(
        name="alert_agent",
        description="Property alert agent that helps users create and manage real-time property alerts. Accepts natural language alert preferences (location, price, email), saves alerts to database, and triggers instant email notifications when matching properties are listed. Users can view, manage, and delete alerts, as well as search current property listings.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[skill],
        capabilities=AgentCapabilities(streaming=True),
    )

    # Pre-initialize the executor
    print("🔔 Pre-initializing Property Alert Agent...")
    executor = AlertAgentExecutor()
    await executor.create()
    print("✅ Property Alert Agent ready to accept requests")

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore()
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

    print(f"Starting Property Alert Agent on http://{host}:{port}")
    print(f"Agent Card available at: http://{host}:{port}/.well-known/agent.json")
    print(f"Agent accepts natural language alert preferences and sends email notifications")
    print(f"Users can create alerts, view existing alerts, and search properties")
    
    # Run the server
    config = uvicorn.Config(server.build(), host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


@click.command()
@click.option("--host", default="localhost", help="Host for the agent server.")
@click.option("--port", default=8005, help="Port for the agent server.")
def main(host: str, port: int):
    """
    Start the Property Alert Agent server.
    
    This agent helps users:
    - Create property alerts from natural language (e.g., "Alert me for Brooklyn apartments under $2500")
    - Receive instant email notifications when matching properties are listed
    - View their existing alerts
    - Delete alerts they no longer need
    - Search current property listings by location and price
    """
    asyncio.run(initialize_and_run(host, port))


if __name__ == "__main__":
    main()