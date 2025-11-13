from utilities.mcp.mcp_discovery import MCPDiscovery
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
import asyncio
from typing import Optional, List

class MCPConnector:
    """
    Discovers MCP servers from config and loads their tools.
    Can filter to load only specific servers.
    """

    def __init__(self, config_file: str = None, server_names: Optional[List[str]] = None):
        """
        Initialize MCP Connector.
        
        Args:
            config_file: Path to mcp_config.json (optional)
            server_names: List of specific server names to load. 
                         If None, loads all servers.
                         Example: ["property_search"] or ["listings_mongodb"]
        """
        self.discovery = MCPDiscovery(config_file=config_file)
        self.server_names = server_names  
        self.tools: list[MCPToolset] = []

    async def _load_all_tools(self):
        """
        Loads tools from discovered MCP servers.
        Only loads servers specified in server_names filter (if provided).
        """
        tools = []
        all_servers = self.discovery.list_servers()

        if self.server_names:
            servers_to_load = {
                name: server 
                for name, server in all_servers.items() 
                if name in self.server_names
            }
            print(f"[cyan]Filtering to load only: {self.server_names}")
        else:
            servers_to_load = all_servers
            print(f"[cyan]Loading all available MCP servers")
        
        for name, server in servers_to_load.items():
            try:
                if server.get("command") == "streamable_http":
                    url = server["args"][0]
                    conn = StreamableHTTPServerParams(url=url)
                    
                    print(f"[cyan]Connecting to MCP server '{name}' at {url}...")
                else:
                    print(f"[yellow]⚠️  Skipping unsupported server type for '{name}': {server.get('command')}")
                    continue

                # Create the toolset instance
                mcp_toolset = MCPToolset(connection_params=conn)

                available_tools = await asyncio.wait_for(
                    mcp_toolset.get_tools(),
                    timeout=10.0
                )

                if available_tools:
                    tool_names = [tool.name for tool in available_tools]
                    print(f"[bold green] Loaded tools from server [cyan]'{name}'[/cyan]: {tool_names}")
                    tools.append(mcp_toolset)
                else:
                    print(f"[yellow]No tools found on server '{name}'")

            except asyncio.TimeoutError:
                print(f"[bold red]✗ Timeout loading tools from server '{name}'")
            except ConnectionError as e:
                print(f"[bold red]✗ Connection error loading tools from server '{name}': {e}")
            except Exception as e:
                print(f"[bold red]✗ Error loading tools from server '{name}': {e}")

        self.tools = tools
        
        if not self.tools:
            print("[bold yellow]⚠️  WARNING: No MCP tools loaded. Make sure MCP servers are running!")
        else:
            print(f"[bold green]✓ Successfully loaded {len(self.tools)} MCP toolset(s)")
    
    async def get_tools(self) -> list[MCPToolset]:
        """
        Returns the list of cached MCPToolsets.
        Loads tools on first call if not already loaded (lazy loading).
        
        Returns:
            list[MCPToolset]: List of MCPToolsets.
        """
        if not self.tools:
            await self._load_all_tools()
        
        return self.tools