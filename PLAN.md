# py-air-sviva-api: Python API Wrapper for air.sviva.gov.il

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python async API wrapper for the Israeli Ministry of Environmental Protection's air quality monitoring API (`air-papi.sviva.gov.il`).

**Architecture:** Async client (`aiohttp`) with dataclass models (`mashumaro`/`DataClassDictMixin`). Single public client class (`SvivaAirClient`) that manages token auth and exposes methods for regions, stations, pollutants, and air quality readings. Public endpoints (no login required) — auth is via a simple token generation endpoint.

**Tech Stack:**
- `aiohttp` — async HTTP client
- `mashumaro` — dataclass JSON deserialization
- `pytest` + `pytest-asyncio` — testing
- `ruff` — linting
- `hatchling` — build system

---

## Package Structure

```
py-air-sviva-api/
├── pyproject.toml
├── README.md
├── example.py
├── air_sviva_api/
│   ├── __init__.py
│   ├── client.py          # SvivaAirClient - main public class
│   ├── const.py           # URLs, headers, constants
│   ├── commons.py         # Shared HTTP utilities
│   ├── data.py            # API call functions (get_regions, get_pollutants, etc.)
│   └── models/
│       ├── __init__.py
│       ├── region.py      # Region, Station, Location
│       ├── pollutant.py   # Pollutant, Unit, DataStatus
│       ├── reading.py     # ChannelReading, StationData, IndexData
│       ├── average.py     # AverageData, AverageChannelReading
│       └── exceptions.py  # SvivaAirError
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_client.py
```

## API Endpoints (from HAR analysis)

Base URL: `https://air-papi.sviva.gov.il/v1/envista/`

| Endpoint | Description | Source |
|----------|-------------|--------|
| `POST /v1/GenerateToken` | Generate auth token | HAR 1-2 |
| `GET regions` | All monitoring regions + stations | HAR 1 |
| `GET regions/data/latest?unitConversion=true&regionsIds={ids}&hoursBack={n}` | Latest readings per region | HAR 1 |
| `GET stations/index/latest?hoursBack={n}` | Latest air quality index by station | HAR 1 |
| `GET stations/{id}/Average/{channelId}?from=...&to=...` | Historical average readings for a pollutant channel | HAR 2 |
| `GET stations/{id}/Average?from=...&to=...` | All-channel historical average for a station | HAR 2 |
| `GET stations/{id}/indexFastSrv?from=...&to=...` | Fast index data for a station | HAR 2 |
| `GET stations/{id}/data/missing/days` | Missing data days for a station | HAR 2 |
| `GET pollutants` | Full pollutant list | HAR 1 |
| `GET data/units` | Measurement units | HAR 1 |
| `GET data/status` | Data status codes | HAR 1 |
| `GET manual/stations` | Manual monitoring stations | HAR 1 |
| `GET manual/pollutants` | Manual measurement pollutants | HAR 1 |
| `GET config/index` | System config | HAR 1 |
| `GET index/configuration?Type=1` | Index calculation config | HAR 1 |
| `GET StationTerminology/GetStationTerminology` | Station terminology | HAR 1 |
| `GET Layer/mng/sviva?Platform=0&AccessLevel=1` | Map layer management | HAR 1 |
| `GET layer/{id}/queries` | Layer feature queries | HAR 1 |
| `GET layer/{id}/queries/filteredStations` | Filtered stations per layer | HAR 2 |
| `GET factors/indexPollutants?indexType=3` | Index pollutant factors | HAR 1 |
| `GET Pollutants/Threshold/get-all-threshold` | All pollutant thresholds | HAR 1 |
| `GET widget/sviva` | Widget configuration | HAR 1 |
| `GET user/MapView/Guest` | Guest map view config | HAR 1-2 |
| `GET interpolation/mng` | Interpolation management | HAR 1-2 |
| `GET Advisory?siteTable=sviva` | Air quality advisories | HAR 1-2 |
| `GET vineyard/location/{id}` | Vineyard/agricultural weather | HAR 1-2 |
| `GET /ajax/GetAPITime` | Server time (main domain) | HAR 1 |

## Auth Flow (Public — No Login Required)

1. Generate a random `x-requestverificationtoken` (or extract from initial page load)
2. `POST /v1/GenerateToken` with empty body, headers including `x-requestverificationtoken`, `domainname: sviva`, `envi-data-source: MANA`
3. Response body is a numeric token string (e.g., `"60"`)
4. All subsequent requests use the same `x-requestverificationtoken` header
5. The token string from step 3 might be used as a `DefaultUser` header or tracking value

**Important:** This is a *public* API — the token generation does NOT require login credentials. The `x-requestverificationtoken` appears to be a session-level anti-forgery token that can be extracted or generated.

---

## Task Breakdown

### Plan 1: Project Foundation + Models

**Wave:** 1

#### Task 1.1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `air_sviva_api/__init__.py`
- Create: `air_sviva_api/const.py`
- Create: `air_sviva_api/commons.py`
- Create: `air_sviva_api/models/__init__.py`
- Create: `air_sviva_api/models/exceptions.py`

**Action:**
- Set up `pyproject.toml` with project metadata, dependencies (`aiohttp>=3.9,<4`, `mashumaro>=3.13,<4`), dev deps (`pytest>=9`, `pytest-asyncio`, `ruff`), hatchling build
- `air_sviva_api/__init__.py`: empty
- `air_sviva_api/commons.py`: HTTP utility functions `send_get_request()`, `send_post_request()` as async helpers that raise custom exceptions on non-200. No auth bearer logic needed (different auth pattern). Include JSON decode error handling and timeout support.
- `air_sviva_api/const.py`:
  - `BASE_URL = "https://air-papi.sviva.gov.il/v1/envista/"`
  - `MAIN_URL = "https://air.sviva.gov.il/"`
  - `HEADERS` — base headers (accept, accept-language, user-agent, origin, referer, domainname, envi-data-source)
  - Individual endpoint URL constants
- `air_sviva_api/models/exceptions.py`: `SvivaAirError(Exception)` with code and message

**Verify:**
- `python -c "import air_sviva_api"` succeeds
- `python -c "from air_sviva_api.models.exceptions import SvivaAirError"` succeeds
- `python -m pytest tests/` collects 0 tests (no tests written yet)

**Done:**
- Project package importable
- HTTP utility functions ready
- Error classes defined
- Constants/URLs for all endpoints defined

#### Task 1.2: Data models

**Files:**
- Create: `air_sviva_api/models/region.py`
- Create: `air_sviva_api/models/pollutant.py`
- Create: `air_sviva_api/models/reading.py`
- Create: `air_sviva_api/models/average.py`

**Action:**
Create dataclass models using `mashumaro` `DataClassDictMixin` with `field_options(alias=...)` for camelCase mapping:

**region.py:**
```python
@dataclass
class Location(DataClassDictMixin):
    latitude: float
    longitude: float

@dataclass
class Monitor(DataClassDictMixin):
    channel_id: int = field(metadata=field_options(alias="channelId"))
    name: str
    short_name: str = field(metadata=field_options(alias="shortName"))

@dataclass
class Station(DataClassDictMixin):
    station_id: int = field(metadata=field_options(alias="stationId"))
    name: str
    short_name: Optional[str] = field(default=None, metadata=field_options(alias="shortName"))
    station_tag: Optional[str] = field(default=None, metadata=field_options(alias="stationsTag"))
    location: Optional[Location] = None
    timebase: Optional[int] = None
    active: bool = False
    owner: Optional[str] = None
    owner_id: Optional[int] = field(default=None, metadata=field_options(alias="ownerId"))
    region_id: Optional[int] = field(default=None, metadata=field_options(alias="regionId"))
    monitors: Optional[list[Monitor]] = None

@dataclass
class Region(DataClassDictMixin):
    region_id: int = field(metadata=field_options(alias="regionId"))
    name: str
    stations: Optional[list[Station]] = None
```

**pollutant.py:**
```python
@dataclass
class Pollutant(DataClassDictMixin):
    id: int = field(metadata=field_options(alias="Id"))
    name: str = field(metadata=field_options(alias="Name"))
    description: str = field(metadata=field_options(alias="Description"))

@dataclass
class Unit(DataClassDictMixin):
    id: int = field(metadata=field_options(alias="Id"))
    name: str = field(metadata=field_options(alias="Name"))
    description: str = field(metadata=field_options(alias="Description"))

@dataclass
class DataStatus(DataClassDictMixin):
    id: int = field(metadata=field_options(alias="Id"))
    name: str = field(metadata=field_options(alias="Name"))
```

**reading.py:**
```python
@dataclass
class ChannelReading(DataClassDictMixin):
    id: int
    name: str
    alias: Optional[str] = None
    value: float = 0.0
    status: int = 0
    valid: bool = False
    description: Optional[str] = None
    units: Optional[str] = None
    active: bool = False
    pollutant_id: Optional[int] = field(default=None, metadata=field_options(alias="pollutantId"))
    datetime: Optional[str] = None

@dataclass
class RegionData(DataClassDictMixin):
    datetime: Optional[str] = None
    channels: Optional[list[ChannelReading]] = None

@dataclass
class RegionStationData(DataClassDictMixin):
    station_id: int = field(metadata=field_options(alias="stationId"))
    region_data: Optional[RegionData] = field(default=None, metadata=field_options(alias="regionData"))

@dataclass
class StationIndex(DataClassDictMixin):
    station_id: int = field(metadata=field_options(alias="stationId"))
    datetime: Optional[str] = None
    index_type: Optional[int] = field(default=None, metadata=field_options(alias="indexType"))
    index: Optional[float] = None
    value: Optional[float] = None
    color: Optional[str] = None
    description: Optional[str] = None
    pollutant: Optional[str] = None
    pollutant_id: Optional[int] = field(default=None, metadata=field_options(alias="pollutantId"))
    indexes: Optional[list["StationIndex"]] = None

@dataclass
class StationIndexResponse(DataClassDictMixin):
    datetime: Optional[str] = None
    index_type: Optional[int] = field(default=None, metadata=field_options(alias="indexType"))
    pollutant_id: Optional[int] = field(default=None, metadata=field_options(alias="pollutantId"))
    pollutant: Optional[str] = None
    index: Optional[float] = None
    value: Optional[float] = None
    color: Optional[str] = None
    station_id: Optional[int] = field(default=None, metadata=field_options(alias="stationId"))
    description: Optional[str] = None
    data: Optional[list[StationIndex]] = None
```

**average.py:**
```python
@dataclass
class AverageChannelReading(DataClassDictMixin):
    id: int
    name: str
    value: float = 0.0
    status: int = 0
    valid: bool = False
    value_date: Optional[str] = field(default=None, metadata=field_options(alias="value_date"))
    units: Optional[str] = None
    pollutant_id: Optional[int] = field(default=None, metadata=field_options(alias="PollutantId"))

@dataclass
class AverageDataPoint(DataClassDictMixin):
    datetime: Optional[str] = None
    channels: Optional[list[AverageChannelReading]] = None

@dataclass
class AverageResponse(DataClassDictMixin):
    data: Optional[list[AverageDataPoint]] = None
```

**Verify:**
- `python -c "from air_sviva_api.models.region import Region, Station; from air_sviva_api.models.reading import ChannelReading, StationIndexResponse; from air_sviva_api.models.average import AverageResponse"`
- All models importable

**Done:**
- All data models defined with proper JSON field aliases
- Models handle optional fields with defaults
- Response wrapper models (StationIndexResponse, AverageResponse) for top-level API responses

### Plan 2: Client + Auth + Core API

**Wave:** 1 (no model dependency for auth, but would be cleaner after models)

**Depends on:** Plan 1

#### Task 2.1: Auth and client core

**Files:**
- Create: `air_sviva_api/data.py`
- Create: `air_sviva_api/client.py`

**Action:**
**data.py:**
- Implement `async def generate_token(session: ClientSession) -> str`:
  - POST to `/v1/GenerateToken` with empty body and headers: `x-requestverificationtoken` (random/auto-generated), `domainname: sviva`, `envi-data-source: MANA`
  - Return response text (the numeric token)
- Implement `async def get_server_time(session: ClientSession) -> str`:
  - GET `https://air.sviva.gov.il/ajax/GetAPITime`
  - Return text
- Use the HTTP helpers from commons.py

**client.py:**
- `SvivaAirClient` class:
  - Constructor takes optional `aiohttp.ClientSession`
  - Manages `_token` (the verification token string) and `_session`
  - Context manager support (`__aenter__`/`__aexit__`)
  - `async def generate_token()` — calls data.py's generate_token, stores internally
  - `_get_headers()` — returns base headers dict with `x-requestverificationtoken` set
  - Internal `_get()` / `_post()` helpers that use `send_get_request`/`send_post_request` with headers from `_get_headers()`
  - Token is auto-generated on first call if not set

**Verify:**
- `python -c "from air_sviva_api.client import SvivaAirClient"`
- Basic import test

**Done:**
- Client can generate and store auth token
- HTTP helpers use the token in subsequent requests

#### Task 2.2: Core read API methods

**Files:**
- Modify: `air_sviva_api/data.py` (add all get_* functions)
- Modify: `air_sviva_api/client.py` (add public methods)

**Action:**
Add to **data.py** — each function takes `session`, `headers`, and optional params:

1. `async def get_regions(session, headers) -> list[Region]`
2. `async def get_regions_latest_data(session, headers, region_ids: list[int], hours_back: int = 4) -> list[RegionStationData]`
3. `async def get_stations_latest_index(session, headers, hours_back: int = 24) -> StationIndexResponse`
4. `async def get_station_average(session, headers, station_id: int, channel_id: Optional[int] = None, from_date: str = "", to_date: str = "") -> AverageResponse`
5. `async def get_station_index_fast(session, headers, station_id: int, from_date: str = "", to_date: str = "") -> dict`
6. `async def get_station_missing_days(session, headers, station_id: int, days_back: int = 180) -> list[str]`
7. `async def get_pollutants(session, headers) -> list[Pollutant]`
8. `async def get_units(session, headers) -> list[Unit]`
9. `async def get_data_statuses(session, headers) -> list[DataStatus]`
10. `async def get_manual_stations(session, headers) -> list[dict]`
11. `async def get_index_pollutants(session, headers, index_type: int = 3) -> list[dict]`
12. `async def get_thresholds(session, headers) -> list[dict]`
13. `async def get_advisories(session, headers) -> list[dict]`

Add to **client.py** — public methods mirroring data.py functions:
```python
async def get_regions(self) -> list[Region]
async def get_regions_latest_data(self, region_ids: list[int], hours_back: int = 4) -> list[RegionStationData]
async def get_stations_latest_index(self, hours_back: int = 24) -> StationIndexResponse
async def get_station_average(self, station_id: int, channel_id: Optional[int] = None, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> AverageResponse
async def get_station_index_fast(self, station_id: int, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> dict
async def get_station_missing_days(self, station_id: int, days_back: int = 180) -> list[str]
async def get_pollutants(self) -> list[Pollutant]
async def get_units(self) -> list[Unit]
async def get_data_statuses(self) -> list[DataStatus]
async def get_manual_stations(self) -> list[dict]
async def get_index_pollutants(self, index_type: int = 3) -> list[dict]
async def get_thresholds(self) -> list[dict]
async def get_advisories(self) -> list[dict]
```

For `get_station_average` date params — format them as ISO 8601 strings. Default to today if not provided.

For `get_regions_latest_data` — accept `region_ids` as list of ints, join with commas for URL.

**Verify:**
- `python -c "from air_sviva_api.client import SvivaAirClient; from air_sviva_api.data import get_pollutants, get_regions"`
- All imports work

**Done:**
- All public API endpoints accessible via client methods
- Functions handle parameter formatting (dates, list joining)
- Error handling via existing exception infrastructure

### Plan 3: Tests + Example

**Wave:** 2 (needs client + models)

**Depends on:** Plan 2

#### Task 3.1: Tests and documentation

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_models.py`
- Create: `tests/test_client.py`
- Create: `README.md`
- Create: `example.py`

**Action:**
**conftest.py:**
- Fixtures for sample JSON responses (extracted from HAR file data)
- Provide sample region, pollutant, station index, and average response JSON
- Mock aiohttp.ClientSession for unit tests

**test_models.py:**
- Test each model can deserialize from sample JSON
- `test_region_from_dict` — load sample region JSON, verify fields
- `test_pollutant_from_dict` — load sample pollutant JSON
- `test_channel_reading_from_dict` — load sample channel reading
- `test_station_index_response_from_dict` — load sample index JSON
- `test_average_response_from_dict` — load sample average JSON
- Test optional/missing fields
- Test alias mapping (camelCase <-> snake_case)

**test_client.py:**
- Mock `send_get_request` to return sample data
- Test `get_pollutants()` returns list of Pollutant objects
- Test `get_regions()` returns list of Region objects
- Test `get_regions_latest_data()` with mock response
- Test `get_stations_latest_index()` returns StationIndexResponse
- Test `get_station_average()` constructs correct URL with params
- Test auth token handling

**README.md:**
- Project description
- Installation: `pip install py-air-sviva-api` or `pip install git+...`
- Quick start example code
- API methods overview
- Development setup (clone, install dev deps, run tests)

**example.py:**
```python
"""Example usage of py-air-sviva-api."""

import asyncio
import aiohttp

from air_sviva_api.client import SvivaAirClient


async def main():
    async with aiohttp.ClientSession() as session:
        client = SvivaAirClient(session)
        await client.generate_token()

        # Get all regions and their stations
        regions = await client.get_regions()
        for region in regions[:3]:
            print(f"{region.name}: {len(region.stations or [])} stations")

        # Get latest air quality index
        index = await client.get_stations_latest_index()
        print(f"\nLatest index: {index.description} (value: {index.value})")

        # Get all pollutants
        pollutants = await client.get_pollutants()
        print(f"\n{len(pollutants)} pollutants tracked")

        # Get latest data for all regions
        region_data = await client.get_regions_latest_data([1, 2, 3])
        for rd in region_data[:5]:
            if rd.region_data and rd.region_data.channels:
                channel = rd.region_data.channels[0]
                print(f"Station {rd.station_id}: {channel.name} = {channel.value} {channel.units}")

        # Get historical data for a specific station and pollutant
        avg = await client.get_station_average(station_id=82, channel_id=5)  # O3 at station 82
        if avg and avg.data:
            print(f"\nGot {len(avg.data)} data points for station 82 O3")


if __name__ == "__main__":
    asyncio.run(main())
```

**Verify:**
- `python -m pytest tests/ -v` — all tests pass
- `python example.py` — runs without import errors (will fail on network, which is expected without token)

**Done:**
- All models tested with real data from HAR files
- Client methods tested with mocked responses
- README with usage documentation
- Example script showing common use cases
- Code coverage >90% on models

---

## Success Criteria

- [ ] `SvivaAirClient` can generate a token via `POST /v1/GenerateToken`
- [ ] All regions and their stations can be retrieved via `get_regions()`
- [ ] Latest air quality data can be fetched per region via `get_regions_latest_data()`
- [ ] Latest station index data available via `get_stations_latest_index()`
- [ ] Historical average data retrievable per station+channel via `get_station_average()`
- [ ] All reference data (pollutants, units, statuses) accessible
- [ ] Tests pass with real HAR data as mocks
- [ ] Example script demonstrates all major features
- [ ] Package installable via `pip install .`

## Key Design Decisions

1. **Async-first** — using `aiohttp` for async HTTP
2. **mashumaro models** — `DataClassDictMixin` with `field_options(alias=...)` for serialization
3. **Public API** — no login/password needed; auth is a simple token generation
4. **Flat URL structure** — all envista endpoints under `/v1/envista/` base path
5. **Model aliases** — all JSON fields use camelCase, Python uses snake_case via mashumaro aliases
6. **No default session** — caller provides `aiohttp.ClientSession`
