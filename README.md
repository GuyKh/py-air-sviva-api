# py-air-sviva-api

[![GitHub Release](https://img.shields.io/github/release/GuyKh/py-air-sviva-api.svg?style=for-the-badge)](https://github.com/GuyKh/py-air-sviva-api/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/GuyKh/py-air-sviva-api?style=for-the-badge)](https://github.com/GuyKh/py-air-sviva-api/commits/main)
[![License](https://img.shields.io/github/license/GuyKh/py-air-sviva-api?style=for-the-badge)](https://github.com/GuyKh/py-air-sviva-api/blob/main/LICENSE)
[![Project Maintenance](https://img.shields.io/badge/maintainer-Guy%20Kh-blue.svg?style=for-the-badge)](https://github.com/GuyKh)
[![BuyMeCoffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge)](https://www.buymeacoffee.com/guykh)

Python async API wrapper for the Israeli Ministry of Environmental Protection air quality monitoring system (`air.sviva.gov.il`).

This library provides a clean, type-safe interface to the Envista air quality API.

## Features

- **Async-first** — built on `aiohttp` for non-blocking HTTP
- **Fully typed** — all API responses deserialized into dataclass models via `mashumaro`
- **No login required** — the API uses a public token generation endpoint
- **Comprehensive endpoint coverage** — regions, stations, pollutants, air quality index, historical averages, and more

## Installation

```bash
pip install air-sviva-api
```

Or install directly from the repository:

```bash
pip install git+https://github.com/GuyKh/py-air-sviva-api.git
```

## Quick Start (5 lines)

```python
import asyncio, aiohttp
from air_sviva_api.client import SvivaAirClient

async def main():
    async with aiohttp.ClientSession() as s:
        c = SvivaAirClient(s)
        await c.generate_token()
        print(await c.get_stations_latest_index())
asyncio.run(main())
```

## API Methods

### Regions & Stations
| Method | Parameters | Description |
|--------|------------|-------------|
| `get_regions()` | — | All monitoring regions with stations |
| `get_regions_latest_data(region_ids, hours_back=4)` | `region_ids: list[int]`, `hours_back: int` | Latest readings per region |
| `get_stations_latest_index(hours_back=24)` | `hours_back: int` | Latest air quality index |
| `get_station_average(station_id, channel_id=None, from_date=None, to_date=None, timebase=5, from_timebase=5, to_timebase=5)` | `station_id: int`, `channel_id: int?`, `from_date: date?`, `to_date: date?`, `timebase: int`, `from_timebase: int`, `to_timebase: int` | Historical averages (5-min intervals by default) |
| `get_station_index_fast(station_id, from_date=None, to_date=None)` | `station_id: int`, `from_date: date?`, `to_date: date?` | Fast index data |
| `get_station_missing_days(station_id, days_back=180)` | `station_id: int`, `days_back: int` | Missing data dates |
| `get_station_images(station_id)` | `station_id: int` | Station images |
| `find_nearest_stations(lat, lon, limit=10)` | `lat: float`, `lon: float`, `limit: int` | Nearest stations to coordinates |

### Reference Data
| Method | Parameters | Description |
|--------|------------|-------------|
| `get_pollutants()` | — | All tracked pollutants |
| `get_units()` | — | Measurement units |
| `get_data_statuses()` | — | Data status codes |
| `get_manual_stations()` | — | Manual monitoring stations |
| `get_manual_pollutants()` | — | Manual measurement pollutants |
| `get_index_pollutants(index_type)` | `index_type: int` | Index pollutant factors |
| `get_thresholds()` | — | Pollutant thresholds |
| `get_advisories()` | — | Active advisories |

### Config & Metadata
| Method | Parameters | Description |
|--------|------------|-------------|
| `get_config_index()` | — | System config |
| `get_index_configuration(index_type)` | `index_type: int` | Index calculation config |
| `get_station_terminology()` | — | Station classifications |
| `get_widget_config()` | — | Widget config |
| `get_guest_map_view()` | — | Guest map view |

### Map Layers
| Method | Parameters | Description |
|--------|--|
| `get_layer_mng(platform, access_level)` | Map layer management |
| `get_layer_queries(layer_id)` | Layer feature queries |
| `get_layer_filtered_stations(layer_id)` | Filtered stations |

### Other
| Method | Parameters | Description |
|--------|------------|-------------|
| `get_server_time()` | — | Server time |
| `get_interpolation_mng()` | — | Interpolation data |
| `get_vineyard_location(location_id)` | `location_id: int` | Agricultural weather data |

## Development

```bash
git clone https://github.com/GuyKh/py-air-sviva-api.git
cd py-air-sviva-api
pip install -e ".[dev]"
pytest tests/ -v
```

## Code Quality

```bash
ruff check .      # Linting
mypy .            # Type checking
pytest tests/ -v  # Tests
```

## Support

If you find this library useful, consider [buying me a coffee](https://www.buymeacoffee.com/guykh) ☕

## License

[MIT License](LICENSE) - see LICENSE file for details.

---

Built with ❤️ for the Israeli air quality monitoring community.