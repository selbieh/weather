from pydantic import BaseModel


class WeatherResponse(BaseModel):
    city: str
    country: str
    temperature: int
    feels_like: int
    humidity: int
    wind_speed: int
    wind_direction: str
    description: str
    observation_time: str


class ErrorDetail(BaseModel):
    field: str | None = None
    detail: str


class ErrorResponse(BaseModel):
    type: str
    errors: list[ErrorDetail]
