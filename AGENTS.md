# py-air-sviva-api Agent Guidelines

## Project Structure

```
py-air-sviva-api/
├── air_sviva_api/                 # Main package
│   ├── __init__.py               # Package initializer
│   ├── client.py                 # Main SvivaAirClient class (auth & API interface)
│   ├── data.py                   # API call functions
│   ├── commons.py                # HTTP utilities and error handling
│   ├── const.py                  # Constants (URLs, headers, defaults)
│   └── models/                   # Dataclass models for API responses
│       ├── __init__.py
│       ├── average.py            # Average response models
│       ├── exceptions.py         # Custom exceptions
│       ├── pollutant.py          # Pollutant models
│       ├── reading.py            # Reading/channel models
│       └── region.py             # Region/station/monitor models
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── test_client.py           # Client tests
│   └── test_models.py           # Model tests
├── example.py                   # Usage example
├── README.md                    # Project documentation
└── pyproject.toml               # Project configuration
```

## Key Components

### SvivaAirClient (`client.py`)
- Main public interface for users
- Handles authentication flow (two-step token generation)
- Provides methods for all API endpoints
- Manages aiohttp ClientSession lifecycle
- Handles request verification tokens and auth tokens

### Data Functions (`data.py`)
- Low-level API call functions
- Each function corresponds to an API endpoint
- Takes session and headers, returns typed models or raw dicts
- Uses mashumaro for deserialization into dataclasses

### HTTP Utilities (`commons.py`)
- GET/POST request handling with proper error handling
- JSON and plain text response handling
- Custom SvivaAirError exception for API errors
- Helper functions (e.g., haversine distance)

### Constants (`const.py`)
- API base URLs and endpoints
- Default HTTP headers
- Timeout values and other constants

### Models (`models/`)
- Dataclass models using mashumaro for serialization
- Field aliases to match API JSON field names
- Optional fields for nullable API values
- Proper type annotations throughout

## Best Practices

### 1. Authentication Flow
The API uses a two-step authentication process:
1. POST to `/Account/GetApiToken` with `{"userName": "Guest"}` to get API token
2. POST to `/v1/GenerateToken` with `Authorization: ApiToken {token}` to get auth token
- Store and reuse auth tokens for subsequent requests
- Include `authorization: JwtToken {token}` header for authenticated requests
- Include `x-requestverificationtoken` header for some endpoints

### 2. Error Handling
- All HTTP requests wrap aiohttp exceptions in custom `SvivaAirError`
- Handle HTTP status codes appropriately (especially 204 No Content)
- Parse JSON responses safely with fallback for non-JSON responses
- Include response details in error messages for debugging

### 3. Dataclass Models
- Use `@dataclass` with `mashumaro.DataClassDictMixin`
- Use `field(metadata={"alias": "FIELD_NAME"})` for JSON field mapping
- Mark fields as `Optional[T]` when API can return null/None
- Provide sensible defaults for optional fields
- Use `serialize_by_alias = True` in Config class

### 4. HTTP Client Usage
- Reuse a single `aiohttp.ClientSession` for multiple requests
- Properly manage session lifecycle with async context managers
- Set appropriate timeouts for requests
- Copy and modify headers per request type (auth vs regular)

### 5. Type Safety
- Use type annotations for all function parameters and return values
- Leverage Python's typing system (Optional, List, etc.)
- Use dataclasses as DTOs for API responses
- Import typing constructs properly

### 6. Testing
- Use pytest as the testing framework
- Use pytest-asyncio for async tests
- Mock HTTP responses when testing client logic
- Test both success and error cases
- Keep tests focused and isolated

### 7. Code Style
- Follow PEP 8 formatting guidelines
- Use black for code formatting
- Use isort for import sorting
- Use ruff for linting
- Line length: 120 characters
- Target Python version: 3.11

## Common Patterns

### Making API Requests
```python
# In data.py functions
async def get_regions(session: ClientSession, headers: dict[str, str]) -> list[Region]:
    response = await commons.send_get_request(
        session=session, 
        url=_build_url(GET_REGIONS_URL), 
        headers=headers
    )
    return [Region.from_dict(r) for r in response]
```

### Handling Authentication
```python
# In client.py
def _ensure_auth_headers(self) -> dict[str, str]:
    headers = self._get_base_headers()
    if self._request_verification_token:
        headers["x-requestverificationtoken"] = self._request_verification_token
    if self._auth_token:
        headers["authorization"] = f"JwtToken {self._auth_token}"
    return headers
```

### Error Handling
```python
# In commons.py
async def send_get_request(...) -> Any:
    try:
        resp = await session.get(...)
        # Handle special status codes like 204 No Content
        if resp.status == http.HTTPStatus.NO_CONTENT:
            return None
        json_resp = await resp.json()
    except exceptions as ex:
        raise SvivaAirError(...)
    
    if resp.status != http.HTTPStatus.OK:
        raise SvivaAirError(resp.status, f"API returned status {resp.status}")
    
    return json_resp
```

## Development Setup

### Dependencies
- Runtime: aiohttp, mashumaro, orjson
- Development: pytest, pytest-asyncio, ruff

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Lint
ruff check .
```

### Code Change Verification
For each code change, ensure to run the following checks to maintain code quality:
- Run `ruff check .` to catch linting errors
- Run `mypy .` to catch type errors
- Run `pytest tests/ -v` to ensure all tests pass

### Installation
```bash
# Development install
pip install -e ".[dev]"
```

## API Coverage

The wrapper provides access to all major API endpoints:

### Core Data
- Regions and stations with monitoring data
- Real-time air quality index
- Historical averages and fast index data
- Missing data dates

### Reference Data
- Pollutants, units, data status codes
- Manual stations and pollutants
- Index pollutant factors
- Thresholds and advisories

### Configuration
- System configuration and index calculation settings
- Station terminology and classifications
- Widget and guest map view configuration

### Map Layers
- Layer management, queries, and filtered stations

### Additional Features
- Server time, interpolation data, vineyard/agricultural data
- Nearest station finding via Haversine distance calculation

This structure provides a clean, maintainable, and type-safe interface to the Israeli Ministry of Environmental Protection air quality monitoring system.