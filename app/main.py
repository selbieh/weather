from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["5/5minutes"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    FastAPICache.init(InMemoryBackend())
    # single shared client — avoids opening a new connection per request
    app.state.http_client = httpx.AsyncClient(timeout=10.0)
    yield
    await app.state.http_client.aclose()


app = FastAPI(
    title="Weather API",
    version="0.1.0",
    description="A minimal API that returns current weather for a city via Weatherstack.",
    lifespan=lifespan,
)

app.state.limiter = limiter


# --- Standardized error handlers ---
# Every error response follows the same shape: {type, errors[{field?, detail}]}
# so consumers only need to handle one format.


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "client_error" if exc.status_code < 500 else "server_error",
            "errors": [{"detail": exc.detail}],
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # flatten pydantic's loc tuples into dotted paths (e.g. "query.city")
    return JSONResponse(
        status_code=422,
        content={
            "type": "validation_error",
            "errors": [
                {
                    "field": ".".join(str(loc) for loc in e["loc"]),
                    "detail": e["msg"],
                }
                for e in exc.errors()
            ],
        },
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "type": "client_error",
            "errors": [{"detail": f"Rate limit exceeded: {exc.detail}"}],
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # the @cache decorator swallows HTTPException and re-raises as plain Exception,
    # so we need to catch it here and route it back to the right handler
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)
    # don't leak internals — just return a generic message
    return JSONResponse(
        status_code=500,
        content={
            "type": "server_error",
            "errors": [{"detail": "Internal server error"}],
        },
    )


# import after app is created to avoid circular imports
from app.routers.weather import router as weather_router  # noqa: E402

app.include_router(weather_router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}
