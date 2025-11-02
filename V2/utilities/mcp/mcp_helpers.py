from utilities.mcp.mcp_connect import MCPConnector
from typing import Optional, Dict, Any
import json


class MCPHelpers:
    """
    Simplified utility class for MCP operations.
    Only provides tool calling - no context store operations.
    """
    
    @staticmethod
    async def initialize_mcp(connector: Optional[MCPConnector] = None) -> MCPConnector:
        """
        Initialize MCP connector and load all available tools.
        
        Args:
            connector: Existing connector instance (optional)
            
        Returns:
            MCPConnector instance ready to use
        """
        if connector is None:
            connector = MCPConnector()
            await connector.get_tools()
        return connector
    
    @staticmethod
    async def call_tool(
        connector: MCPConnector,
        server_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generic method to call any MCP tool from any server.
        
        Args:
            connector: MCPConnector instance
            server_name: Name of MCP server (e.g., "PDF_Extractor")
            tool_name: Name of the tool to invoke
            arguments: Dict of arguments to pass to the tool
            
        Returns:
            Dict with tool response
        """
        try:
            session = connector.sessions.get(server_name)
            if not session:
                raise Exception(f"MCP server '{server_name}' not available")
            
            result = await session.call_tool(tool_name, arguments=arguments)
            
            if hasattr(result, 'content') and result.content:
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        return json.loads(content_item.text)
            
            return {"error": "No content in tool response", "status": "failed"}
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}