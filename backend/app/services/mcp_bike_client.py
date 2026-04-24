import asyncio
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

try:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


class MCPBikePlannerClient:
    """Connect to Smithery HTTP MCP server using official MCP client."""

    def __init__(self, smithery_config: Dict[str, Any]) -> None:
        self.smithery_config = smithery_config
        # Extract API key from args
        args = smithery_config.get("args", [])
        self.api_key = None
        for i, arg in enumerate(args):
            if arg == "--key" and i + 1 < len(args):
                self.api_key = args[i + 1]
                break

    async def plan_route(self, origin: str, destination: str, city: Optional[str] = None) -> Dict[str, Any]:
        """Connect to Smithery HTTP MCP server and call bike planning tool."""
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP client not available. Install with: pip install mcp")
        
        if not self.api_key:
            raise RuntimeError("No API key found in smithery config")
        
        # Construct server URL with authentication
        base_url = "https://server.smithery.ai/@defreeze/bike-planner-mcp-v2/mcp"
        params = {"api_key": self.api_key}
        url = f"{base_url}?{urlencode(params)}"
        
        print(f"[MCPBikePlannerClient] Connecting to {url}")
        
        try:
            print(f"[MCPBikePlannerClient] Starting connection to {url}")
            # Connect to the server using HTTP client with timeout
            async with asyncio.timeout(30):  # 30 second total timeout
                async with streamablehttp_client(url) as (read, write, _):
                    print(f"[MCPBikePlannerClient] HTTP client connected, creating session")
                    async with ClientSession(read, write) as session:
                        # Initialize the connection with timeout
                        print(f"[MCPBikePlannerClient] Initializing session...")
                        init_start = time.time()
                        await asyncio.wait_for(session.initialize(), timeout=10.0)  # 10 second init timeout
                        init_time = time.time() - init_start
                        print(f"[MCPBikePlannerClient] Session initialized in {init_time:.2f}s")
                    
                        # List available tools
                        print(f"[MCPBikePlannerClient] Listing tools...")
                        tools_start = time.time()
                        tools_result = await asyncio.wait_for(session.list_tools(), timeout=10.0)
                        tools_time = time.time() - tools_start
                        tools = tools_result.tools
                        print(f"[MCPBikePlannerClient] Tools listed in {tools_time:.2f}s: {', '.join([t.name for t in tools])}")
                        
                        # Find a suitable tool
                        print(f"[MCPBikePlannerClient] Searching for suitable tool...")
                        route_tool = None
                        for i, tool in enumerate(tools):
                            name = tool.name.lower()
                            desc = tool.description.lower() if tool.description else ""
                            print(f"[MCPBikePlannerClient] Tool {i}: {tool.name} - {tool.description}")
                            if any(keyword in name or keyword in desc for keyword in ["route", "bike", "plan", "cycling"]):
                                route_tool = tool
                                print(f"[MCPBikePlannerClient] Found matching tool: {tool.name}")
                                break
                        
                        if not route_tool and tools:
                            route_tool = tools[0]
                            print(f"[MCPBikePlannerClient] Using first available tool: {route_tool.name}")
                        
                        if not route_tool:
                            raise RuntimeError("No suitable tools found in MCP server")
                        
                        tool_name = route_tool.name
                        print(f"[MCPBikePlannerClient] Selected tool: {tool_name}")
                        
                        # Call the tool
                        tool_arguments = {
                            "origin": origin,
                            "destination": destination,
                        }
                        if city:
                            tool_arguments["city"] = city
                        
                        print(f"[MCPBikePlannerClient] Preparing to call tool '{tool_name}' with args: {tool_arguments}")
                        
                        # Add timeout for tool call
                        try:
                            print(f"[MCPBikePlannerClient] Calling tool (timeout: 20s)...")
                            call_start = time.time()
                            result = await asyncio.wait_for(
                                session.call_tool(tool_name, tool_arguments),
                                timeout=20.0  # 20 second timeout
                            )
                            call_time = time.time() - call_start
                            print(f"[MCPBikePlannerClient] Tool call completed in {call_time:.2f}s")
                            print(f"[MCPBikePlannerClient] Tool result type: {type(result)}")
                            print(f"[MCPBikePlannerClient] Tool result: {result}")
                            
                            return {
                                "content": result.content,
                                "isError": result.isError,
                                "metadata": result.metadata
                            }
                        except asyncio.TimeoutError:
                            call_time = time.time() - call_start
                            print(f"[MCPBikePlannerClient] Tool call timed out after {call_time:.2f}s (20s limit)")
                            raise RuntimeError("Tool call timed out")
                        except Exception as tool_error:
                            call_time = time.time() - call_start
                            print(f"[MCPBikePlannerClient] Tool call failed after {call_time:.2f}s: {tool_error}")
                            raise
                    
        except asyncio.TimeoutError as e:
            print(f"[MCPBikePlannerClient] Connection timed out: {e}")
            raise RuntimeError(f"MCP connection timed out: {str(e)}")
        except Exception as e:
            print(f"[MCPBikePlannerClient] Error: {e}")
            import traceback
            print(f"[MCPBikePlannerClient] Traceback: {traceback.format_exc()}")
            raise RuntimeError(f"MCP client error: {str(e)}")


