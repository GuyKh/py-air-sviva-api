"""API call functions for the Sviva Air API.

Each function takes an aiohttp ClientSession and headers dict,
and returns typed model objects or raw dicts for less structured endpoints.
"""

import logging
from typing import Any, Optional

from aiohttp import ClientSession

from air_sviva_api import commons
from air_sviva_api.const import (
    BASE_URL,
    DEFAULT_HOURS_BACK,
    DEFAULT_MISSING_DAYS_BACK,
    DEFAULT_REGION_HOURS_BACK,
    GENERATE_TOKEN_URL,
    GET_ADVISORIES_URL,
    GET_API_TOKEN_URL,
    GET_CONFIG_INDEX_URL,
    GET_DATA_STATUS_URL,
    GET_DATA_UNITS_URL,
    GET_GUEST_MAP_VIEW_URL,
    GET_INDEX_CONFIGURATION_URL,
    GET_INDEX_POLLUTANTS_URL,
    GET_INTERPOLATION_MNG_URL,
    GET_LAYER_FILTERED_STATIONS_URL,
    GET_LAYER_MNG_URL,
    GET_LAYER_QUERIES_URL,
    GET_LUT_MNG_URL,
    GET_MANUAL_POLLUTANTS_URL,
    GET_MANUAL_STATIONS_URL,
    GET_POLLUTANTS_URL,
    GET_REGIONS_LATEST_DATA_URL,
    GET_REGIONS_URL,
    GET_SERVER_TIME_URL,
    GET_STATION_AVERAGE_URL,
    GET_STATION_DATA_AVERAGE_URL,
    GET_STATION_IMAGES_URL,
    GET_STATION_INDEX_FAST_URL,
    GET_STATION_MISSING_DAYS_URL,
    GET_STATION_TERMINOLOGY_URL,
    GET_STATIONS_LATEST_INDEX_URL,
    GET_THRESHOLDS_URL,
    GET_VINEYARD_LOCATION_URL,
    GET_WIDGET_URL,
    HEADERS,
)
from air_sviva_api.models.average import AverageDataPoint, AverageResponse
from air_sviva_api.models.lut import LookUpTable, parse_lut_management_response
from air_sviva_api.models.pollutant import DataStatus, Pollutant, Unit
from air_sviva_api.models.reading import RegionStationData, StationIndexResponse
from air_sviva_api.models.region import Region
from air_sviva_api.models.station_images import StationImagesResponse

logger = logging.getLogger(__name__)


async def generate_token(
    session: ClientSession,
    headers: dict[str, str],
    existing_jwt_token: Optional[str] = None,
) -> str:
    """Generate an auth token from the public Sviva Air API.

    This is a two-step process:
    1. POST to /Account/GetApiToken with {"userName": "Guest"} to get an API token
    2. POST to /v1/GenerateToken with the API token in the Authorization header
       Optionally include an existing JWT token as a cookie for refresh scenarios.
    """
    # Step 1: Get API token from the main domain
    api_token_headers = headers.copy()
    api_token_headers["content-type"] = "application/json; charset=UTF-8"
    api_token_headers["accept"] = "application/json, text/javascript, */*; q=0.01"
    # Ensure origin and referer are set to the main domain for this request
    api_token_headers["origin"] = "https://air.sviva.gov.il"
    api_token_headers["referer"] = "https://air.sviva.gov.il/"

    api_token_resp = await commons.send_post_request(
        session=session,
        url=GET_API_TOKEN_URL,
        headers=api_token_headers,
        json_data={"userName": "Guest"},
    )

    # Extract the API token from the response (remove quotes if present)
    api_token = api_token_resp.strip().replace('"', "")

    # Step 2: Generate the actual token using the API token
    generate_token_headers = headers.copy()
    generate_token_headers["accept"] = "application/json"
    generate_token_headers["authorization"] = f"ApiToken {api_token}"
    # For the GenerateToken endpoint, use the API domain
    generate_token_headers["origin"] = "https://air.sviva.gov.il"
    generate_token_headers["referer"] = "https://air.sviva.gov.il/"

    # If we have an existing JWT token, include it as a cookie for refresh
    if existing_jwt_token:
        generate_token_headers["cookie"] = f"X-Access-Token={existing_jwt_token}"

    token_resp = await commons.send_text_post_request(
        session=session,
        url=GENERATE_TOKEN_URL,
        headers=generate_token_headers,
        json_data={},
    )

    return token_resp.strip()


async def get_server_time(session: ClientSession) -> str:
    """Get current server time from the main domain."""
    server_headers = {
        "accept": "*/*",
        "accept-language": "en,he;q=0.9",
        "user-agent": HEADERS["user-agent"],
    }
    return await commons.send_text_get_request(session=session, url=GET_SERVER_TIME_URL, headers=server_headers)


def _build_url(endpoint: str) -> str:
    """Build a full URL from a relative endpoint path."""
    return BASE_URL + endpoint


async def get_regions(session: ClientSession, headers: dict[str, str]) -> list[Region]:
    """Get all monitoring regions with their stations and monitors."""
    response = await commons.send_get_request(session=session, url=_build_url(GET_REGIONS_URL), headers=headers)
    return [Region.from_dict(r) for r in response]


async def get_regions_latest_data(
    session: ClientSession,
    headers: dict[str, str],
    region_ids: list[int],
    hours_back: int = DEFAULT_REGION_HOURS_BACK,
) -> list[RegionStationData]:
    """Get latest air quality data readings for specified regions."""
    ids_str = ",".join(str(rid) for rid in region_ids)
    url = _build_url(GET_REGIONS_LATEST_DATA_URL)
    url += f"?unitConversion=true&regionsIds={ids_str}&hoursBack={hours_back}"
    response = await commons.send_get_request(session=session, url=url, headers=headers)
    return [RegionStationData.from_dict(item) for item in response]


async def get_stations_latest_index(
    session: ClientSession,
    headers: dict[str, str],
    hours_back: int = DEFAULT_HOURS_BACK,
) -> StationIndexResponse:
    """Get latest air quality index for all stations."""
    url = _build_url(GET_STATIONS_LATEST_INDEX_URL)
    url += "?unitConversion=true&regionsIds=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15"
    url += f"&hoursBack={hours_back}"
    response = await commons.send_get_request(session=session, url=url, headers=headers)
    return StationIndexResponse.from_dict(response)


async def get_station_average(
    session: ClientSession,
    headers: dict[str, str],
    station_id: int,
    channel_id: Optional[int] = None,
    from_date: str = "",
    to_date: str = "",
    timebase: int = 5,
    from_timebase: int = 5,
    to_timebase: int = 5,
) -> AverageResponse:
    """Get historical average readings for a station's pollutant channel.

    Tries the /Average endpoint first (with full gist parameters), falls back to /data/average if needed.

    Args:
        session: The aiohttp ClientSession.
        headers: Request headers.
        station_id: The station ID.
        channel_id: Optional pollutant channel ID. If omitted, returns all channels.
        from_date: Start date as ISO string (e.g. "2024-01-01T00:00:00").
        to_date: End date as ISO string.
        timebase: Time base in minutes for data aggregation (default 5 min).
        from_timebase: From timebase in minutes (default 5 min).
        to_timebase: To timebase in minutes (default 5 min).

    Returns:
        AverageResponse containing time-series data points.
    """
    # Build params for /Average endpoint (gist format)
    params = []
    if from_date:
        params.append(f"from={from_date}")
    if to_date:
        params.append(f"to={to_date}")
    params.append(f"fromTimebase={from_timebase}")
    params.append(f"toTimebase={to_timebase}")
    params.append("timeBeginning=false")
    params.append("useBackWard=true")
    params.append("includeSummary=false")
    params.append("roundType=1")
    params.append("unitid=-1")
    params.append("unitConversion=true")
    param_str = "?" + "&".join(params)

    # Try /Average endpoint first (expected format: AverageResponse with data array)
    if channel_id:
        endpoint = GET_STATION_AVERAGE_URL + f"/{channel_id}"
    else:
        endpoint = GET_STATION_AVERAGE_URL
    url = _build_url(endpoint.format(station_id=station_id)) + param_str
    try:
        response = await commons.send_get_request(session=session, url=url, headers=headers)
        return AverageResponse.from_dict(response)
    except Exception:
        # Fall back to /data/average endpoint
        pass

    # Fallback to /data/average endpoint
    url = _build_url(GET_STATION_DATA_AVERAGE_URL.format(station_id=station_id))
    params_fallback = []
    if from_date:
        params_fallback.append(f"from={from_date}")
    if to_date:
        params_fallback.append(f"to={to_date}")
    params_fallback.append(f"timebase={timebase}")
    param_str_fallback = "?" + "&".join(params_fallback) if params_fallback else ""
    url = _build_url(GET_STATION_DATA_AVERAGE_URL.format(station_id=station_id)) + param_str_fallback
    try:
        response = await commons.send_get_request(session=session, url=url, headers=headers)
        # /data/average returns a single AverageDataPoint, wrap in AverageResponse
        data_point = AverageDataPoint.from_dict(response)
        return AverageResponse(data=[data_point])
    except Exception:
        # If both endpoints fail, return empty response instead of crashing
        return AverageResponse(data=[])


async def get_station_data_average(
    session: ClientSession,
    headers: dict[str, str],
    station_id: int,
    timebase: int = 60,
    from_date: str = "",
    to_date: str = "",
) -> AverageDataPoint:
    """Get average data for a station using the /data/average endpoint.

    This endpoint returns a single AverageDataPoint (not wrapped in a data array).

    Args:
        session: The aiohttp ClientSession.
        headers: Request headers.
        station_id: The station ID.
        timebase: Time base in minutes (default 60).
        from_date: Start date as ISO string.
        to_date: End date as ISO string.

    Returns:
        AverageDataPoint containing the average readings.
    """
    url = _build_url(GET_STATION_DATA_AVERAGE_URL.format(station_id=station_id))
    params = []
    if timebase:
        params.append(f"timebase={timebase}")
    if from_date:
        params.append(f"from={from_date}")
    if to_date:
        params.append(f"to={to_date}")
    if params:
        url += "?" + "&".join(params)
    response = await commons.send_get_request(session=session, url=url, headers=headers)
    # The /data/average endpoint returns a single AverageDataPoint, not wrapped in "data"
    return AverageDataPoint.from_dict(response)


async def get_station_index_fast(
    session: ClientSession,
    headers: dict[str, str],
    station_id: int,
    from_date: str = "",
    to_date: str = "",
) -> dict[str, Any]:
    """Get fast air quality index data for a station."""
    url = _build_url(GET_STATION_INDEX_FAST_URL.format(station_id=station_id))
    params = []
    if from_date:
        params.append(f"from={from_date}")
    if to_date:
        params.append(f"to={to_date}")
    if params:
        url += "?" + "&".join(params)
    return await commons.send_get_request(session=session, url=url, headers=headers)


async def get_station_missing_days(
    session: ClientSession,
    headers: dict[str, str],
    station_id: int,
    days_back: int = DEFAULT_MISSING_DAYS_BACK,
) -> list[str]:
    """Get list of dates with missing data for a station."""
    url = _build_url(GET_STATION_MISSING_DAYS_URL.format(station_id=station_id))
    url += f"?daysBack={days_back}"
    response = await commons.send_get_request(session=session, url=url, headers=headers)
    return list(response) if isinstance(response, list) else []


async def get_station_images(
    session: ClientSession,
    headers: dict[str, str],
    station_id: int,
) -> StationImagesResponse:
    """Get images for a station.

    Note: The API may return an empty response or non-JSON response if no images
    are available for the station. This function handles such cases gracefully.
    """
    url = GET_STATION_IMAGES_URL
    data = {"stationId": str(station_id)}
    try:
        response = await commons.send_post_request(session=session, url=url, headers=headers, data=data)
        # If response is a list, wrap it in "images" key
        if isinstance(response, list):
            return StationImagesResponse.from_dict({"images": response})
        # If response is already a dict with "images" key, use it directly
        if isinstance(response, dict) and "images" in response:
            return StationImagesResponse.from_dict(response)
        # Otherwise, return empty response
        return StationImagesResponse(images=[])
    except Exception:
        # If the response is not valid JSON (e.g., empty or binary image data),
        # return empty response
        return StationImagesResponse(images=[])


async def get_pollutants(session: ClientSession, headers: dict[str, str]) -> list[Pollutant]:
    """Get list of all tracked pollutants."""
    response = await commons.send_get_request(session=session, url=_build_url(GET_POLLUTANTS_URL), headers=headers)
    return [Pollutant.from_dict(p) for p in response]


async def get_units(session: ClientSession, headers: dict[str, str]) -> list[Unit]:
    """Get list of measurement units."""
    response = await commons.send_get_request(session=session, url=_build_url(GET_DATA_UNITS_URL), headers=headers)
    return [Unit.from_dict(u) for u in response]


async def get_data_statuses(session: ClientSession, headers: dict[str, str]) -> list[DataStatus]:
    """Get list of data status codes."""
    response = await commons.send_get_request(session=session, url=_build_url(GET_DATA_STATUS_URL), headers=headers)
    return [DataStatus.from_dict(s) for s in response]


async def get_manual_stations(session: ClientSession, headers: dict[str, str]) -> list[dict[str, Any]]:
    """Get list of manual monitoring stations."""
    return await commons.send_get_request(session=session, url=_build_url(GET_MANUAL_STATIONS_URL), headers=headers)


async def get_manual_pollutants(session: ClientSession, headers: dict[str, str]) -> list[dict[str, Any]]:
    """Get list of manual measurement pollutants."""
    return await commons.send_get_request(session=session, url=_build_url(GET_MANUAL_POLLUTANTS_URL), headers=headers)


async def get_index_pollutants(
    session: ClientSession,
    headers: dict[str, str],
    index_type: int = 3,
) -> list[dict[str, Any]]:
    """Get index pollutant factors."""
    url = _build_url(GET_INDEX_POLLUTANTS_URL)
    url += f"?indexType={index_type}"
    return await commons.send_get_request(session=session, url=url, headers=headers)


async def get_thresholds(session: ClientSession, headers: dict[str, str]) -> list[dict[str, Any]]:
    """Get all pollutant threshold values."""
    return await commons.send_get_request(session=session, url=_build_url(GET_THRESHOLDS_URL), headers=headers)


async def get_advisories(session: ClientSession, headers: dict[str, str]) -> list[dict[str, Any]]:
    """Get air quality advisories."""
    url = _build_url(GET_ADVISORIES_URL) + "?siteTable=sviva"
    return await commons.send_get_request(session=session, url=url, headers=headers)


async def get_config_index(session: ClientSession, headers: dict[str, str]) -> dict[str, Any]:
    """Get system configuration."""
    return await commons.send_get_request(session=session, url=_build_url(GET_CONFIG_INDEX_URL), headers=headers)


async def get_index_configuration(
    session: ClientSession,
    headers: dict[str, str],
    index_type: int = 1,
) -> dict[str, Any]:
    """Get index calculation configuration."""
    url = _build_url(GET_INDEX_CONFIGURATION_URL)
    url += f"?Type={index_type}"
    return await commons.send_get_request(session=session, url=url, headers=headers)


async def get_station_terminology(session: ClientSession, headers: dict[str, str]) -> list[dict[str, Any]]:
    """Get station terminology/classifications."""
    return await commons.send_get_request(session=session, url=_build_url(GET_STATION_TERMINOLOGY_URL), headers=headers)


async def get_layer_mng(
    session: ClientSession,
    headers: dict[str, str],
    platform: int = 0,
    access_level: int = 1,
) -> list[dict[str, Any]]:
    """Get map layer management data."""
    url = _build_url(GET_LAYER_MNG_URL)
    url += f"?Platform={platform}&AccessLevel={access_level}"
    return await commons.send_get_request(session=session, url=url, headers=headers)


async def get_layer_queries(
    session: ClientSession,
    headers: dict[str, str],
    layer_id: int,
) -> list[dict[str, Any]]:
    """Get feature queries for a map layer."""
    url = _build_url(GET_LAYER_QUERIES_URL.format(layer_id=layer_id))
    return await commons.send_get_request(session=session, url=url, headers=headers)


async def get_layer_filtered_stations(
    session: ClientSession,
    headers: dict[str, str],
    layer_id: int,
) -> list[dict[str, Any]]:
    """Get filtered stations for a map layer."""
    url = _build_url(GET_LAYER_FILTERED_STATIONS_URL.format(layer_id=layer_id))
    return await commons.send_get_request(session=session, url=url, headers=headers)


async def get_widget_config(session: ClientSession, headers: dict[str, str]) -> dict[str, Any]:
    """Get widget configuration."""
    return await commons.send_get_request(session=session, url=_build_url(GET_WIDGET_URL), headers=headers)


async def get_guest_map_view(session: ClientSession, headers: dict[str, str]) -> dict[str, Any]:
    """Get guest map view configuration."""
    return await commons.send_get_request(session=session, url=_build_url(GET_GUEST_MAP_VIEW_URL), headers=headers)


async def get_interpolation_mng(session: ClientSession, headers: dict[str, str]) -> list[dict[str, Any]]:
    """Get interpolation management data."""
    return await commons.send_get_request(session=session, url=_build_url(GET_INTERPOLATION_MNG_URL), headers=headers)


async def get_vineyard_location(
    session: ClientSession,
    headers: dict[str, str],
    location_id: int,
) -> dict[str, Any]:
    """Get vineyard/agricultural weather data for a location."""
    url = _build_url(GET_VINEYARD_LOCATION_URL.format(location_id=location_id))
    return await commons.send_get_request(session=session, url=url, headers=headers)


async def get_lut_mng(session: ClientSession, headers: dict[str, str]) -> list[LookUpTable]:
    """Get all lookup tables (LUT) management data."""
    response = await commons.send_get_request(session=session, url=_build_url(GET_LUT_MNG_URL), headers=headers)
    return parse_lut_management_response(response)
