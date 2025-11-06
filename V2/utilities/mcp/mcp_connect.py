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
        self._exit_stack = None 
        
    async def _load_all_tools(self):
        """
        Loads all tools from the discovered MCP servers 
        that support streamable_http connections 
        and caches them as ClientSessions.
        
        Now handles connection failures gracefully - continues even if servers are unavailable.
        """
        from contextlib import AsyncExitStack
        
        # Keep connections alive
        self._exit_stack = AsyncExitStack()

        for name, server in self.discovery.list_servers().items():
            try:
                if server.get("command") == "streamable_http":
                    url = server["args"][0]
                    
                    print(f"[cyan]Attempting to connect to MCP server '{name}' at {url}...[/cyan]")
                    
                    # Add timeout to prevent hanging
                    try:
                        read, write = await asyncio.wait_for(
                            self._exit_stack.enter_async_context(sse_client(url)),
                            timeout=5.0  # 5 second timeout for connection
                        )
                    except asyncio.TimeoutError:
                        print(f"[yellow]⚠️  Timeout connecting to MCP server '{name}' (skipping)[/yellow]")
                        continue
                    
                    session = ClientSession(read, write)

                    await asyncio.wait_for(session.initialize(), timeout=5.0)

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
                        print(f"[bold green]✅ Loaded tools from server [cyan]'{name}'[/cyan]:[/bold green] {', '.join(tool_names)}")
                    else:
                        print(f"[yellow]⚠️  No tools found on server '{name}'[/yellow]")

            except asyncio.TimeoutError:
                print(f"[yellow]⚠️  Timeout loading tools from server '{name}' (skipping)[/yellow]")
            except ConnectionError as e:
                print(f"[yellow]⚠️  Connection error loading tools from server '{name}': {e} (skipping)[/yellow]")
            except Exception as e:
                print(f"[yellow]⚠️  Error loading tools from server '{name}': {e} (skipping)[/yellow]")
        
        # Print summary
        if not self.tools_cache:
            print(f"[bold yellow]⚠️  WARNING: No MCP tools loaded. Make sure MCP servers are running![/bold yellow]")
        else:
            print(f"[bold green]✅ Successfully loaded {len(self.tools_cache)} MCP server(s)[/bold green]")

    
    async def get_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns the cached dictionary of tools by server name.
        """
        await self._load_all_tools()
        return self.tools_cache.copy()