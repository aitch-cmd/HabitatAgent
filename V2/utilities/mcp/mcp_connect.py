from V2.utilities.mcp.mcp_discovery import MCPDiscovery
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
import asyncio

class MCPConnector:
    """
    Discovers the MCP servers from the config.
    Config will be loaded by the MCP Discovery class. 
    Then it will list each server's tools
    and then caches them as MCPToolsets that are compatible 
    with Google's Agent Development Kit (ADK).
    """

    def __init__(self, config_file: str = None):
        self.discovery = MCPDiscovery(config_file=config_file)
        self.tools: list[MCPToolset] = []

    async def _load_all_tools(self):
        """
        Loads all tools from the discovered MCP servers
        and caches them as MCPToolsets.
        This version ONLY supports streamable HTTP MCP server types.
        """
        tools = []
        for name, server in self.discovery.list_servers().items():
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
                
                # Get tools to verify connection works
                available_tools = await asyncio.wait_for(
                    mcp_toolset.get_tools(),
                    timeout=10.0
                )

                if available_tools:
                    tool_names = [tool.name for tool in available_tools]
                    print(f"[bold green]✅ Loaded tools from server [cyan]'{name}'[/cyan]: {tool_names}")
                    tools.append(mcp_toolset)
                else:
                    print(f"[yellow]⚠️  No tools found on server '{name}'")

            except asyncio.TimeoutError:
                print(f"[bold red]⚠️  Timeout loading tools from server '{name}'")
            except ConnectionError as e:
                print(f"[bold red]⚠️  Connection error loading tools from server '{name}': {e}")
            except Exception as e:
                print(f"[bold red]⚠️  Error loading tools from server '{name}': {e}")

        self.tools = tools
        
        if not self.tools:
            print("[bold yellow]⚠️  WARNING: No MCP tools loaded. Make sure MCP servers are running!")
        else:
            print(f"[bold green]✅ Successfully loaded {len(self.tools)} MCP toolset(s)")
    
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