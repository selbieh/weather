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
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Failed to reach weather service") from exc

    data = response.json()

    # Weatherstack returns non-200 or success:false on errors — parse body first
    if not data.get("success", True) or response.status_code != 200:
        error_info = data.get("error", {})
        error_code = error_info.get("code")
        error_msg = error_info.get("info", "Unknown upstream error")

        # Map Weatherstack error codes to HTTP statuses
        status_map = {
            101: (401, "Invalid or missing API key"),
            103: (403, "API endpoint not available on current plan"),
            104: (429, "API rate limit reached"),
            105: (403, "API plan does not support this endpoint"),
            601: (404, f"City not found: {city}"),
            602: (404, f"City not found: {city}"),
            615: (404, f"City not found: {city}"),
        }

        if error_code in status_map:
            status, detail = status_map[error_code]
            raise HTTPException(status_code=status, detail=detail)

        raise HTTPException(
            status_code=502,
            detail=f"Upstream weather service error: {error_msg}",
        )

    # Weatherstack may return 200 with no location/current data for unknown cities
    location = data.get("location")
    current = data.get("current")

    if not location or not current:
        raise HTTPException(status_code=404, detail=f"City not found: {city}")

    try:
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
