import json
from pathlib import Path
from typing import Dict, Any, Optional


class SmitheryServerSelector:
    def __init__(self, config_path: Optional[str] = None) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        self.config_path = (
            Path(config_path)
            if config_path
            else base_dir / "data" / "mcp_smithery_servers.json"
        )
        self.config = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {"mcpServers": {}}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_server(self, name: str) -> Optional[Dict[str, Any]]:
        return self.config.get("mcpServers", {}).get(name)

    def resolve_by_intent(self, query: str) -> Optional[Dict[str, Any]]:
        q = (query or "").lower()
        weather_keywords = ["weather", "天气", "forecast", "气温", "降雨", "风速"]
        bike_keywords = ["bike", "bicycle", "cycling", "骑行", "单车", "route", "路线"]

        if any(k in q for k in weather_keywords):
            return self.get_server("mcp_weather_server")
        if any(k in q for k in bike_keywords):
            return self.get_server("bike-planner-mcp-v2")
        return None


