from typing import Optional
from fastmcp import FastMCP, tool
from .weather_mcp import WeatherMCP


app = FastMCP(app_name="weather-mcp", app_version="0.1.0")
weather = WeatherMCP()


@tool()
def current_weather(city: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None):
    """Get current weather by city name or coordinates."""
    return weather.get_current_weather(city=city, latitude=latitude, longitude=longitude)


@tool()
def weather_forecast(city: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None, days: int = 7):
    """Get daily forecast (max 16 days) by city name or coordinates."""
    return weather.get_daily_forecast(city=city, latitude=latitude, longitude=longitude, days=days)


if __name__ == "__main__":
    # Run MCP server (stdio by default)
    app.run()


