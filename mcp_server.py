"""
MCP server that exposes a weather tool powered by the Weatherstack API.

Run with:
    uv run fastmcp run mcp_server.py
    uv run python mcp_server.py          # stdio transport (for Claude Desktop)
"""

from typing import Annotated

import httpx
from fastmcp import FastMCP
from pydantic import Field

from app.core.config import get_settings

mcp = FastMCP(
    name="Weather MCP",
    instructions="Provides current weather data for any city via the Weatherstack API.",
)


@mcp.tool
async def get_weather(
    city: Annotated[str, Field(description="City name, ZIP code, or coordinates", min_length=1)],
) -> dict:
    """Get current weather conditions for a city.

    Returns temperature, humidity, wind, and a short description.
    Accepts city names (e.g. "London"), ZIP codes, or lat,lon coordinates.
    """
    settings = get_settings()
    normalised_city = city.strip().lower()

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.weatherstack_base_url}/current",
            params={"access_key": settings.weatherstack_api_key, "query": normalised_city},
        )
        response.raise_for_status()

    data = response.json()

    if not data.get("success", True):
        error_info = data.get("error", {})
        error_code = error_info.get("code")
        error_msg = error_info.get("info", "Unknown error")

        if error_code == 615:
            return {"error": f"City not found: {city}"}
        return {"error": error_msg}

    location = data["location"]
    current = data["current"]

    return {
        "city": location["name"],
        "country": location["country"],
        "temperature": current["temperature"],
        "feels_like": current["feelslike"],
        "humidity": current["humidity"],
        "wind_speed": current["wind_speed"],
        "wind_direction": current["wind_dir"],
        "description": current["weather_descriptions"][0],
        "observation_time": current["observation_time"],
    }


if __name__ == "__main__":
    mcp.run()
