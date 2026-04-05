import httpx
import respx

WEATHERSTACK_URL = "http://api.weatherstack.com/current"

VALID_RESPONSE = {
    "request": {"type": "City", "query": "London, United Kingdom", "language": "en", "unit": "m"},
    "location": {
        "name": "London",
        "country": "United Kingdom",
        "region": "City of London, Greater London",
        "lat": "51.517",
        "lon": "-0.106",
        "timezone_id": "Europe/London",
        "localtime": "2026-04-05 12:00",
        "localtime_epoch": 1775304000,
        "utc_offset": "1.0",
    },
    "current": {
        "observation_time": "11:00 AM",
        "temperature": 15,
        "weather_code": 116,
        "weather_icons": ["https://example.com/icon.png"],
        "weather_descriptions": ["Partly cloudy"],
        "wind_speed": 13,
        "wind_degree": 210,
        "wind_dir": "SSW",
        "pressure": 1012,
        "precip": 0,
        "humidity": 72,
        "cloudcover": 50,
        "feelslike": 14,
        "uv_index": 4,
        "visibility": 10,
    },
}

CITY_NOT_FOUND_RESPONSE = {
    "success": False,
    "error": {
        "code": 615,
        "type": "request_failed",
        "info": "Your API request failed. Please try again or contact support.",
    },
}

INVALID_KEY_RESPONSE = {
    "success": False,
    "error": {
        "code": 101,
        "type": "invalid_access_key",
        "info": "You have not supplied a valid API Access Key.",
    },
}


async def test_get_weather_success(client: httpx.AsyncClient, respx_mock: respx.MockRouter):
    respx_mock.get(WEATHERSTACK_URL).mock(return_value=httpx.Response(200, json=VALID_RESPONSE))

    resp = await client.get("/weather", params={"city": "London"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["city"] == "London"
    assert data["country"] == "United Kingdom"
    assert data["temperature"] == 15
    assert data["feels_like"] == 14
    assert data["humidity"] == 72
    assert data["wind_speed"] == 13
    assert data["wind_direction"] == "SSW"
    assert data["description"] == "Partly cloudy"
    assert data["observation_time"] == "11:00 AM"


async def test_city_not_found(client: httpx.AsyncClient, respx_mock: respx.MockRouter):
    respx_mock.get(WEATHERSTACK_URL).mock(return_value=httpx.Response(200, json=CITY_NOT_FOUND_RESPONSE))

    resp = await client.get("/weather", params={"city": "FakeCity"})

    assert resp.status_code == 404
    assert "City not found" in resp.json()["detail"]


async def test_upstream_api_error(client: httpx.AsyncClient, respx_mock: respx.MockRouter):
    respx_mock.get(WEATHERSTACK_URL).mock(return_value=httpx.Response(200, json=INVALID_KEY_RESPONSE))

    resp = await client.get("/weather", params={"city": "Paris"})

    assert resp.status_code == 502


async def test_upstream_connection_error(client: httpx.AsyncClient, respx_mock: respx.MockRouter):
    respx_mock.get(WEATHERSTACK_URL).mock(side_effect=httpx.ConnectError("Connection refused"))

    resp = await client.get("/weather", params={"city": "Berlin"})

    assert resp.status_code == 502
    assert "Failed to reach weather service" in resp.json()["detail"]


async def test_missing_city_param(client: httpx.AsyncClient):
    resp = await client.get("/weather")

    assert resp.status_code == 422


async def test_empty_city_param(client: httpx.AsyncClient):
    resp = await client.get("/weather", params={"city": ""})

    assert resp.status_code == 422
