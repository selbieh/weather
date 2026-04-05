from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    weatherstack_api_key: str
    weatherstack_base_url: str = "http://api.weatherstack.com"
    cache_ttl_seconds: int = 300
    rate_limit: str = "10/minute"

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
