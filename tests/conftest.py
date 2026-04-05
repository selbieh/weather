import httpx
import pytest
import pytest_asyncio
import respx as respx_lib
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from app.core.config import Settings, get_settings
from app.main import app


def _test_settings() -> Settings:
    return Settings(
        weatherstack_api_key="test-key",
        weatherstack_base_url="http://api.weatherstack.com",
        cache_ttl_seconds=0,
        rate_limit="100/minute",
    )


app.dependency_overrides[get_settings] = _test_settings


@pytest.fixture(autouse=True)
def _clear_cache():
    """Re-initialise the in-memory cache before every test."""
    FastAPICache.init(InMemoryBackend())


@pytest_asyncio.fixture()
async def client(respx_mock: respx_lib.MockRouter):
    app.state.http_client = httpx.AsyncClient()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    await app.state.http_client.aclose()
