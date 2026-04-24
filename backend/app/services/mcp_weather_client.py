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


class MCPWeatherClient:
    """Connect to Smithery HTTP MCP server using official MCP client for weather services."""

    def __init__(self, smithery_config: Dict[str, Any]) -> None:
        self.smithery_config = smithery_config
        # Extract API key from args
        args = smithery_config.get("args", [])
        self.api_key = None
        for i, arg in enumerate(args):
            if arg == "--key" and i + 1 < len(args):
                self.api_key = args[i + 1]
                break

    def _parse_weather_text(self, text: str, city: str) -> Dict[str, Any]:
        """Parse weather text and convert to structured format."""
        import re
        
        # Extract temperature
        temp_match = re.search(r'temperature of ([\d.]+)°C', text)
        temperature = float(temp_match.group(1)) if temp_match else 0.0
        
        # Extract weather condition
        weather_condition = "Unknown"
        if "Overcast" in text:
            weather_condition = "Overcast"
        elif "Clear" in text:
            weather_condition = "Clear"
        elif "Cloudy" in text:
            weather_condition = "Cloudy"
        elif "Rain" in text:
            weather_condition = "Rain"
        
        # Map weather condition to weather code
        weather_codes = {
            "Clear": 0,
            "Overcast": 3,
            "Cloudy": 2,
            "Rain": 61,
            "Unknown": 0
        }
        weathercode = weather_codes.get(weather_condition, 0)
        
        # Extract humidity
        humidity_match = re.search(r'Relative humidity.*?(\d+) %', text)
        humidity = int(humidity_match.group(1)) if humidity_match else 0
        
        return {
            "location": {
                "name": city,
                "country": "Unknown",
                "latitude": 0.0,
                "longitude": 0.0
            },
            "current": {
                "temperature": temperature,
                "weathercode": weathercode,
                "time": "2025-10-01T22:15",
                "humidity": humidity,
                "condition": weather_condition
            }
        }

    async def get_current_weather(self, city: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None) -> Dict[str, Any]:
        """Get current weather by city or coordinates."""
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP client not available. Install with: pip install mcp")
        
        if not self.api_key:
            raise RuntimeError("No API key found in smithery config")
        
        if not city:
            raise ValueError("City must be provided")
        
        # Construct server URL with authentication
        base_url = "https://server.smithery.ai/@isdaniel/mcp_weather_server/mcp"
        params = {"api_key": self.api_key}
        url = f"{base_url}?{urlencode(params)}"
        
        print(f"[MCPWeatherClient] Connecting to {url}")
        
        try:
            print(f"[MCPWeatherClient] Starting connection to {url}")
            # Connect to the server using HTTP client
            async with streamablehttp_client(url) as (read, write, _):
                print(f"[MCPWeatherClient] HTTP client connected, creating session")
                async with ClientSession(read, write) as session:
                    # Initialize the connection with timeout
                    print(f"[MCPWeatherClient] Initializing session...")
                    init_start = time.time()
                    await asyncio.wait_for(session.initialize(), timeout=10.0)  # 10 second init timeout
                    init_time = time.time() - init_start
                    print(f"[MCPWeatherClient] Session initialized in {init_time:.2f}s")
                    
                    # List available tools
                    print(f"[MCPWeatherClient] Listing tools...")
                    tools_start = time.time()
                    tools_result = await asyncio.wait_for(session.list_tools(), timeout=10.0)
                    tools_time = time.time() - tools_start
                    tools = tools_result.tools
                    print(f"[MCPWeatherClient] Tools listed in {tools_time:.2f}s: {', '.join([t.name for t in tools])}")
                    
                    # Find weather tool
                    print(f"[MCPWeatherClient] Searching for weather tool...")
                    weather_tool = None
                    for i, tool in enumerate(tools):
                        name = tool.name.lower()
                        desc = tool.description.lower() if tool.description else ""
                        print(f"[MCPWeatherClient] Tool {i}: {tool.name} - {tool.description}")
                        if any(keyword in name or keyword in desc for keyword in ["weather", "current", "forecast"]):
                            weather_tool = tool
                            print(f"[MCPWeatherClient] Found weather tool: {tool.name}")
                            break
                    
                    if not weather_tool and tools:
                        weather_tool = tools[0]
                        print(f"[MCPWeatherClient] Using first available tool: {weather_tool.name}")
                    
                    if not weather_tool:
                        raise RuntimeError("No suitable weather tools found in MCP server")
                    
                    tool_name = weather_tool.name
                    print(f"[MCPWeatherClient] Selected tool: {tool_name}")
                    
                    # Call the weather tool - only pass city
                    tool_arguments = {"city": city}
                    
                    print(f"[MCPWeatherClient] Preparing to call tool '{tool_name}' with args: {tool_arguments}")
                    
                    # Add timeout for tool call
                    try:
                        print(f"[MCPWeatherClient] Calling tool (timeout: 20s)...")
                        call_start = time.time()
                        result = await asyncio.wait_for(
                            session.call_tool(tool_name, tool_arguments),
                            timeout=20.0  # 20 second timeout
                        )
                        call_time = time.time() - call_start
                        print(f"[MCPWeatherClient] Tool call completed in {call_time:.2f}s")
                        print(f"[MCPWeatherClient] Tool result type: {type(result)}")
                        print(f"[MCPWeatherClient] Tool result: {result}")
                        
                        # Print complete tool call response details
                        print(f"[MCPWeatherClient] === COMPLETE TOOL CALL RESPONSE ===")
                        print(f"[MCPWeatherClient] Result type: {type(result)}")
                        print(f"[MCPWeatherClient] Result attributes: {dir(result)}")
                        print(f"[MCPWeatherClient] Result content: {result.content}")
                        print(f"[MCPWeatherClient] Result isError: {result.isError}")
                        print(f"[MCPWeatherClient] Result metadata: {getattr(result, 'metadata', 'No metadata')}")
                        
                        if hasattr(result, 'content') and result.content:
                            print(f"[MCPWeatherClient] Content length: {len(result.content)}")
                            for i, content_item in enumerate(result.content):
                                print(f"[MCPWeatherClient] Content[{i}] type: {type(content_item)}")
                                print(f"[MCPWeatherClient] Content[{i}] attributes: {dir(content_item)}")
                                if hasattr(content_item, 'text'):
                                    print(f"[MCPWeatherClient] Content[{i}] text: {content_item.text}")
                                else:
                                    print(f"[MCPWeatherClient] Content[{i}] value: {content_item}")
                        print(f"[MCPWeatherClient] === END TOOL CALL RESPONSE ===")
                        
                        # Parse the text content and convert to structured format
                        if result.content and len(result.content) > 0:
                            text_content = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                            print(f"[MCPWeatherClient] Parsing text content: {text_content}")
                            
                            # Parse the weather text and extract structured data
                            parsed_data = self._parse_weather_text(text_content, city)
                            return parsed_data
                        else:
                            return {
                                "location": {"name": city, "country": "Unknown", "latitude": 0, "longitude": 0},
                                "current": {"temperature": 0, "weathercode": 0, "time": ""},
                                "error": "No weather data received"
                            }
                    except asyncio.TimeoutError:
                        call_time = time.time() - call_start
                        print(f"[MCPWeatherClient] Tool call timed out after {call_time:.2f}s (20s limit)")
                        raise RuntimeError("Tool call timed out")
                    except Exception as tool_error:
                        call_time = time.time() - call_start
                        print(f"[MCPWeatherClient] Tool call failed after {call_time:.2f}s: {tool_error}")
                        raise
                    
        except asyncio.TimeoutError as e:
            print(f"[MCPWeatherClient] Connection timed out: {e}")
            raise RuntimeError(f"MCP connection timed out: {str(e)}")
        except Exception as e:
            print(f"[MCPWeatherClient] Error: {e}")
            raise RuntimeError(f"MCP client error: {str(e)}")

    async def get_weather_forecast(self, city: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None, days: int = 7) -> Dict[str, Any]:
        """Get weather forecast for specified number of days."""
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP client not available. Install with: pip install mcp")
        
        if not self.api_key:
            raise RuntimeError("No API key found in smithery config")
        
        if not city:
            raise ValueError("City must be provided")
        
        # Construct server URL with authentication
        base_url = "https://server.smithery.ai/@isdaniel/mcp_weather_server/mcp"
        params = {"api_key": self.api_key}
        url = f"{base_url}?{urlencode(params)}"
        
        print(f"[MCPWeatherClient] Connecting to {url}")
        
        try:
            print(f"[MCPWeatherClient] Starting connection to {url}")
            # Connect to the server using HTTP client
            async with streamablehttp_client(url) as (read, write, _):
                print(f"[MCPWeatherClient] HTTP client connected, creating session")
                async with ClientSession(read, write) as session:
                    # Initialize the connection with timeout
                    print(f"[MCPWeatherClient] Initializing session...")
                    init_start = time.time()
                    await asyncio.wait_for(session.initialize(), timeout=10.0)  # 10 second init timeout
                    init_time = time.time() - init_start
                    print(f"[MCPWeatherClient] Session initialized in {init_time:.2f}s")
                    
                    # List available tools
                    print(f"[MCPWeatherClient] Listing tools...")
                    tools_start = time.time()
                    tools_result = await asyncio.wait_for(session.list_tools(), timeout=10.0)
                    tools_time = time.time() - tools_start
                    tools = tools_result.tools
                    print(f"[MCPWeatherClient] Tools listed in {tools_time:.2f}s: {', '.join([t.name for t in tools])}")
                    
                    # Find forecast tool
                    print(f"[MCPWeatherClient] Searching for forecast tool...")
                    forecast_tool = None
                    for i, tool in enumerate(tools):
                        name = tool.name.lower()
                        desc = tool.description.lower() if tool.description else ""
                        print(f"[MCPWeatherClient] Tool {i}: {tool.name} - {tool.description}")
                        if any(keyword in name or keyword in desc for keyword in ["forecast", "weather", "daily"]):
                            forecast_tool = tool
                            print(f"[MCPWeatherClient] Found forecast tool: {tool.name}")
                            break
                    
                    if not forecast_tool and tools:
                        forecast_tool = tools[0]
                        print(f"[MCPWeatherClient] Using first available tool: {forecast_tool.name}")
                    
                    if not forecast_tool:
                        raise RuntimeError("No suitable forecast tools found in MCP server")
                    
                    tool_name = forecast_tool.name
                    print(f"[MCPWeatherClient] Selected tool: {tool_name}")
                    
                    # Call the forecast tool - only pass city and days
                    tool_arguments = {"city": city, "days": days}
                    
                    print(f"[MCPWeatherClient] Preparing to call tool '{tool_name}' with args: {tool_arguments}")
                    
                    # Add timeout for tool call
                    try:
                        print(f"[MCPWeatherClient] Calling tool (timeout: 20s)...")
                        call_start = time.time()
                        result = await asyncio.wait_for(
                            session.call_tool(tool_name, tool_arguments),
                            timeout=20.0  # 20 second timeout
                        )
                        call_time = time.time() - call_start
                        print(f"[MCPWeatherClient] Tool call completed in {call_time:.2f}s")
                        print(f"[MCPWeatherClient] Tool result type: {type(result)}")
                        print(f"[MCPWeatherClient] Tool result: {result}")
                        
                        # Print complete tool call response details
                        print(f"[MCPWeatherClient] === COMPLETE TOOL CALL RESPONSE ===")
                        print(f"[MCPWeatherClient] Result type: {type(result)}")
                        print(f"[MCPWeatherClient] Result attributes: {dir(result)}")
                        print(f"[MCPWeatherClient] Result content: {result.content}")
                        print(f"[MCPWeatherClient] Result isError: {result.isError}")
                        print(f"[MCPWeatherClient] Result metadata: {getattr(result, 'metadata', 'No metadata')}")
                        
                        if hasattr(result, 'content') and result.content:
                            print(f"[MCPWeatherClient] Content length: {len(result.content)}")
                            for i, content_item in enumerate(result.content):
                                print(f"[MCPWeatherClient] Content[{i}] type: {type(content_item)}")
                                print(f"[MCPWeatherClient] Content[{i}] attributes: {dir(content_item)}")
                                if hasattr(content_item, 'text'):
                                    print(f"[MCPWeatherClient] Content[{i}] text: {content_item.text}")
                                else:
                                    print(f"[MCPWeatherClient] Content[{i}] value: {content_item}")
                        print(f"[MCPWeatherClient] === END TOOL CALL RESPONSE ===")
                        
                        # Parse the text content and convert to structured format
                        if result.content and len(result.content) > 0:
                            text_content = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                            print(f"[MCPWeatherClient] Parsing text content: {text_content}")
                            
                            # Parse the weather text and extract structured data
                            parsed_data = self._parse_weather_text(text_content, city)
                            return parsed_data
                        else:
                            return {
                                "location": {"name": city, "country": "Unknown", "latitude": 0, "longitude": 0},
                                "current": {"temperature": 0, "weathercode": 0, "time": ""},
                                "error": "No weather data received"
                            }
                    except asyncio.TimeoutError:
                        call_time = time.time() - call_start
                        print(f"[MCPWeatherClient] Tool call timed out after {call_time:.2f}s (20s limit)")
                        raise RuntimeError("Tool call timed out")
                    except Exception as tool_error:
                        call_time = time.time() - call_start
                        print(f"[MCPWeatherClient] Tool call failed after {call_time:.2f}s: {tool_error}")
                        raise
                    
        except asyncio.TimeoutError as e:
            print(f"[MCPWeatherClient] Connection timed out: {e}")
            raise RuntimeError(f"MCP connection timed out: {str(e)}")
        except Exception as e:
            print(f"[MCPWeatherClient] Error: {e}")
            raise RuntimeError(f"MCP client error: {str(e)}")