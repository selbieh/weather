import httpx
from fastapi import HTTPException

from app.core.config import Settings
from app.schemas.weather import WeatherResponse


async def fetch_weather(
    city: str,
    http_client: httpx.AsyncClient,
    settings: Settings,
) -> WeatherResponse:
    """Fetch current weather from Weatherstack for the given city."""
    normalised_city = city.strip().lower()

    try:
        response = await http_client.get(
            f"{settings.weatherstack_base_url}/current",
            params={"access_key": settings.weatherstack_api_key, "query": normalised_city},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail="Upstream weather service error") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Failed to reach weather service") from exc

    data = response.json()

    # Weatherstack returns 200 even on errors — inspect body
    if not data.get("success", True):
        error_info = data.get("error", {})
        error_code = error_info.get("code")
        error_msg = error_info.get("info", "Unknown upstream error")

        if error_code == 615:
            raise HTTPException(status_code=404, detail=f"City not found: {city}")

        raise HTTPException(status_code=502, detail=error_msg)

    try:
        location = data["location"]
        current = data["current"]
        return WeatherResponse(
            city=location["name"],
            country=location["country"],
            temperature=current["temperature"],
            feels_like=current["feelslike"],
            humidity=current["humidity"],
            wind_speed=current["wind_speed"],
            wind_direction=current["wind_dir"],
            description=current["weather_descriptions"][0],
            observation_time=current["observation_time"],
        )
    except (KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unexpected response format from weather service",
        ) from exc
