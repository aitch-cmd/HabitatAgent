import asyncio
import logging
import signal
import sys
from typing import List, Dict, Any
from mcp import ClientSession
from mcp.client.sse import sse_client
from rich import print
from V2.utilities.mcp.mcp_discovery import MCPDiscovery

logging.getLogger("mcp").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


class MCPConnector:
    """
    Discovers the MCP servers from the config.
    Config will be loaded by the MCP discovery class
    Then it lists each server's tools
    and caches them as ClientSessions that are compatible with MCP SDK
    """
    
    def __init__(self, config_file: str = None):
        self.discovery = MCPDiscovery(config_file=config_file)
        self.sessions: Dict[str, ClientSession] = {}
        self.tools_cache: Dict[str, List[Dict[str, Any]]] = {}
        
    async def _load_all_tools(self):
        """
        Loads all tools from the discovered MCP servers 
        that support streamable_http connections 
        and caches them as ClientSessions.
        """

        for name, server in self.discovery.list_servers().items():
            try:
                if server.get("command") == "streamable_http":
                    url = server["args"][0]
                    read, write = await sse_client(url)
                    session = ClientSession(read, write)

                    # Initialize session with timeout
                    await asyncio.wait_for(session.initialize(), timeout=10.0)

                    # List available tools
                    tools_response = await session.list_tools()
                    tools = tools_response.tools if hasattr(tools_response, 'tools') else []

                    if tools:
                        self.sessions[name] = session
                        self.tools_cache[name] = [
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "input_schema": tool.inputSchema
                            }
                            for tool in tools
                        ]

                        tool_names = [tool.name for tool in tools]
                        print(f"[bold green]Loaded tools from server [cyan]'{name}'[/cyan]:[/bold green] {', '.join(tool_names)}")

            except asyncio.TimeoutError:
                print(f"[bold red]Timeout loading tools from server '{name}' (skipping)[/bold red]")
            except ConnectionError as e:
                print(f"[bold red]Connection error loading tools from server '{name}': {e} (skipping)[/bold red]")
            except Exception as e:
                print(f"[bold red]Error loading tools from server '{name}': {e} (skipping)[/bold red]")

    
    async def get_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns the cached dictionary of tools by server name.
        """
        await self._load_all_tools()
        return self.tools_cache.copy()