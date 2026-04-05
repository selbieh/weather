# Weather API

A minimal FastAPI service that returns current weather for a city using the [Weatherstack API](https://weatherstack.com/).

## Quick Start

```bash
# Install dependencies
uv sync

# Configure your API key
cp .env.example .env
# Edit .env and add your Weatherstack API key (free tier: https://weatherstack.com/signup/free)

# Run the server
uv run uvicorn app.main:app --reload
```

## Docker

```bash
docker build -t weather-api .
docker run -p 8000:8000 --env-file .env weather-api
```

## API Usage

### `GET /weather?city={city_name}`

Returns current weather conditions for the given city.

**Example:**

```bash
curl "http://localhost:8000/weather?city=London"
```

**Response:**

```json
{
  "city": "London",
  "country": "United Kingdom",
  "temperature": 15,
  "feels_like": 14,
  "humidity": 72,
  "wind_speed": 13,
  "wind_direction": "SSW",
  "description": "Partly cloudy",
  "observation_time": "11:00 AM"
}
```

**Error responses:**

| Status | Meaning |
|--------|---------|
| 404 | City not found |
| 422 | Invalid or missing `city` parameter |
| 429 | Rate limit exceeded (10 requests/minute per IP) |
| 502 | Upstream Weatherstack API error |

Interactive API docs are available at [`/docs`](http://localhost:8000/docs).

## MCP Server

The project also exposes a [Model Context Protocol](https://modelcontextprotocol.io/) server via [FastMCP](https://github.com/jlowin/FastMCP), allowing LLMs (e.g. Claude) to call the weather tool directly.

```bash
# Run the MCP server (stdio transport, for Claude Desktop / Claude Code)
uv run python mcp_server.py

# Or via the fastmcp CLI
uv run fastmcp run mcp_server.py
```

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": ["run", "python", "/path/to/weather/mcp_server.py"],
      "env": {
        "WEATHERSTACK_API_KEY": "your_key_here"
      }
    }
  }
}
```

## Running Tests

```bash
uv run pytest
```

## Assumptions & Trade-offs

- **Weatherstack free tier** uses HTTP only (not HTTPS). The default base URL reflects this.
- **In-memory cache** (5-minute TTL) — appropriate for single-process deployments. No external dependencies needed.
- **Rate limiting** is per-IP at 10 requests/minute using slowapi. Cached responses do not consume rate-limit tokens.
- The API returns a **curated subset** of Weatherstack fields, decoupling the public contract from the upstream provider.
- City names are **normalised** (lowercased, trimmed) before calling Weatherstack to improve cache hit rates.

## Production Improvements

Given more time, I would add:

- **Redis cache backend** for multi-worker / multi-instance deployments
- **Structured logging** (e.g. structlog) with request correlation IDs
- **Health check endpoint** (`/health`) for container orchestration readiness/liveness probes
- **API key authentication** for consumers of this service
- **HTTPS** via a reverse proxy (nginx / Traefik) in front of Uvicorn
- **CI/CD pipeline** with linting (ruff), type checking (mypy), and automated tests
- **OpenTelemetry tracing** for observability across service boundaries
- **Graceful degradation** — serve stale cache if Weatherstack is down
