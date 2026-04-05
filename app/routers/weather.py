from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache

from app.core.config import Settings, get_settings
from app.schemas.weather import ErrorResponse, WeatherResponse
from app.services.weather import fetch_weather

router = APIRouter(tags=["weather"])


@router.get(
    "/weather",
    response_model=WeatherResponse,
    responses={
        404: {"model": ErrorResponse, "description": "City not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        502: {"model": ErrorResponse, "description": "Upstream service error"},
    },
)
@cache(expire=300)
async def get_weather(
    request: Request,
    city: str = Query(..., min_length=1, max_length=100, description="City name"),
    settings: Settings = Depends(get_settings),
):
    """Get current weather for a city."""
    try:
        return await fetch_weather(
            city=city,
            http_client=request.app.state.http_client,
            settings=settings,
        )
    except HTTPException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": "client_error" if exc.status_code < 500 else "server_error",
                "errors": [{"detail": exc.detail}],
            },
        )
