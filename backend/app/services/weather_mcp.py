import requests
from typing import Optional, Dict, Any, List


class WeatherMCP:
    """
    Minimal Capability Protocol (MCP)-style weather service for the travel app.
    Uses Open-Meteo (no API key) for current weather and daily forecast.
    """

    GEO_BASE = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_BASE = "https://api.open-meteo.com/v1/forecast"

    def resolve_location(self, query: Optional[str], latitude: Optional[float], longitude: Optional[float]) -> Dict[str, Any]:
        """
        Resolve location to latitude/longitude. Prefer explicit coordinates; otherwise geocode by name.
        Returns dict with keys: latitude, longitude, name (optional), country (optional)
        """
        if latitude is not None and longitude is not None:
            return {"latitude": float(latitude), "longitude": float(longitude)}

        if not query:
            raise ValueError("必须提供城市名(city)或经纬度(latitude/longitude)")

        resp = requests.get(self.GEO_BASE, params={"name": query, "count": 1, "language": "zh", "format": "json"}, timeout=10)
        resp.raise_for_status()
        data = resp.json() or {}
        results: List[Dict[str, Any]] = data.get("results", [])
        if not results:
            raise ValueError(f"找不到地点: {query}")
        top = results[0]
        return {
            "latitude": top["latitude"],
            "longitude": top["longitude"],
            "name": top.get("name"),
            "country": top.get("country")
        }

    def get_current_weather(self, city: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None) -> Dict[str, Any]:
        loc = self.resolve_location(city, latitude, longitude)
        params = {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "current_weather": True,
            "timezone": "auto"
        }
        resp = requests.get(self.WEATHER_BASE, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json() or {}
        current = data.get("current_weather", {})
        return {
            "location": {"name": loc.get("name"), "country": loc.get("country"), "latitude": loc["latitude"], "longitude": loc["longitude"]},
            "current": current
        }

    def get_daily_forecast(self, city: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None, days: int = 7) -> Dict[str, Any]:
        loc = self.resolve_location(city, latitude, longitude)
        # Open-Meteo supports selecting daily variables
        params = {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "timezone": "auto",
            "forecast_days": max(1, min(int(days), 16))  # cap at 16
        }
        resp = requests.get(self.WEATHER_BASE, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json() or {}
        daily = data.get("daily", {})
        return {
            "location": {"name": loc.get("name"), "country": loc.get("country"), "latitude": loc["latitude"], "longitude": loc["longitude"]},
            "daily": daily
        }


