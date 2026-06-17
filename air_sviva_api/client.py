"""SvivaAirClient — the main public API client for air.sviva.gov.il."""

import base64
import json
import logging
import time
from datetime import date
from typing import Any, List, Optional, Tuple

from aiohttp import ClientSession

from air_sviva_api import commons, data
from air_sviva_api.const import HEADERS
from air_sviva_api.models.average import AverageResponse
from air_sviva_api.models.exceptions import SvivaAirError
from air_sviva_api.models.lut import LookUpTable
from air_sviva_api.models.pollutant import DataStatus, Pollutant, Unit
from air_sviva_api.models.reading import RegionStationData, StationIndexResponse
from air_sviva_api.models.region import Region
from air_sviva_api.models.station_images import StationImagesResponse

logger = logging.getLogger(__name__)


def is_jwt_expired(token: str, buffer_seconds: int = 60) -> bool:
    """
    Check if a JWT token is expired or about to expire.

    Args:
        token: The JWT token string.
        buffer_seconds: Number of seconds before expiry to consider as expired.
                        Default 60 seconds to allow for clock skew and network latency.

    Returns:
        True if the token is expired or will expire within buffer_seconds, False otherwise.
        Returns False for non-JWT tokens (tokens that don't have 3 parts) to avoid
        unnecessary refresh attempts for simple API tokens.
    """
    try:
        # JWT has 3 parts separated by dots: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            # Not a JWT token - don't attempt to refresh non-JWT tokens
            return False

        # Decode the payload (middle part)
        payload_encoded = parts[1]
        # Add padding if needed
        padding = 4 - len(payload_encoded) % 4
        if padding != 4:
            payload_encoded += "=" * padding

        payload_json = base64.urlsafe_b64decode(payload_encoded).decode("utf-8")
        payload = json.loads(payload_json)

        # Check expiration time (exp claim)
        exp = payload.get("exp")
        if exp is None:
            logger.warning("JWT token has no expiration claim")
            return True

        current_time = int(time.time())
        # Consider expired if exp is in the past or within buffer_seconds
        return current_time + buffer_seconds >= exp
    except Exception as e:
        logger.warning(f"Failed to parse JWT token: {e}")
        # On parse error, don't attempt to refresh
        return False


class SvivaAirClient:
    """Async client for the Israeli Ministry of Environmental Protection air quality API.

    Requires an aiohttp.ClientSession to be provided by the caller.
    No login required — auth is handled via a public token generation endpoint.

    Basic usage::

        import aiohttp
        from air_sviva_api.client import SvivaAirClient

        async def main():
            async with aiohttp.ClientSession() as session:
                client = SvivaAirClient(session)
                await client.generate_token()
                regions = await client.get_regions()
                print(regions)
    """

    def __init__(
        self,
        session: ClientSession,
        request_verification_token: Optional[str] = None,
    ):
        """Initialize the SvivaAirClient.

        Args:
            session: An aiohttp ClientSession (provided by caller).
            request_verification_token: Optional x-requestverificationtoken value.
                If not provided, one will be auto-generated from the session headers.
        """
        self._session = session
        self._request_verification_token: Optional[str] = request_verification_token
        self._auth_token: Optional[str] = None

    def _get_base_headers(self) -> dict[str, str]:
        """Get headers with the request verification token set."""
        headers = HEADERS.copy()
        if self._request_verification_token:
            headers["x-requestverificationtoken"] = self._request_verification_token
        else:
            headers.pop("x-requestverificationtoken", None)
        return headers

    async def generate_token(self) -> str:
        """Generate and store an API auth token.

        Calls the public POST /v1/GenerateToken endpoint.
        Stores the returned token internally for future requests.
        """
        headers = self._get_base_headers()
        if not self._request_verification_token:
            import uuid

            self._request_verification_token = str(uuid.uuid4())
            headers["x-requestverificationtoken"] = self._request_verification_token

        self._auth_token = await data.generate_token(self._session, headers)
        logger.info("Auth token generated successfully")
        return self._auth_token

    async def get_server_time(self) -> str:
        """Get the current server time from air.sviva.gov.il."""
        return await data.get_server_time(self._session)

    async def refresh_token(self) -> str:
        """Refresh the auth token using the current token as a cookie.

        This calls GenerateToken with the current auth token as a cookie,
        useful for token renewal before expiration.

        Returns:
            The new auth token.

        Raises:
            SvivaAirError: If the request fails or returns an error.
        """
        if not self._auth_token:
            raise SvivaAirError(-1, "No auth token available to refresh")

        headers = self._get_base_headers()
        self._auth_token = await data.generate_token(
            self._session,
            headers,
            existing_jwt_token=self._auth_token
        )
        logger.info("Auth token refreshed successfully")
        return self._auth_token

    async def _ensure_auth_headers(self) -> dict[str, str]:
        """Get headers with auth token configured, refreshing token if expired."""
        # Check if token exists and is not expired
        if self._auth_token and is_jwt_expired(self._auth_token):
            logger.info("Auth token expired, refreshing...")
            await self.refresh_token()

        headers = self._get_base_headers()
        if self._request_verification_token:
            headers["x-requestverificationtoken"] = self._request_verification_token
        if self._auth_token:
            headers["authorization"] = f"JwtToken {self._auth_token}"
        return headers

    # --- Regions ---

    async def get_regions(self) -> list[Region]:
        """Get all monitoring regions with their stations and monitors."""
        return await data.get_regions(self._session, await self._ensure_auth_headers())

    async def get_regions_latest_data(
        self,
        region_ids: list[int],
        hours_back: int = 4,
    ) -> list[RegionStationData]:
        """Get latest air quality data readings for specified regions."""
        return await data.get_regions_latest_data(
            self._session, await self._ensure_auth_headers(), region_ids, hours_back
        )

    # --- Stations ---

    async def get_stations_latest_index(
        self,
        hours_back: int = 24,
    ) -> StationIndexResponse:
        """Get latest air quality index for all stations.

        Args:
            hours_back: How many hours back to look for data.

        Returns:
            StationIndexResponse with per-station index data.
        """
        return await data.get_stations_latest_index(
            self._session, await self._ensure_auth_headers(), hours_back
        )

    async def get_station_average(
        self,
        station_id: int,
        channel_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        timebase: int = 5,
        from_timebase: int = 5,
        to_timebase: int = 5,
    ) -> AverageResponse:
        """Get historical average readings for a station's pollutant channel.

        Args:
            station_id: The station ID.
            channel_id: Optional pollutant channel ID. If omitted, returns all channels.
            from_date: Start date. Defaults to today.
            to_date: End date. Defaults to today.
            timebase: Time base in minutes for data aggregation (default 5 min).
            from_timebase: From timebase in minutes (default 5 min).
            to_timebase: To timebase in minutes (default 5 min).

        Returns:
            AverageResponse containing time-series data points.
        """
        today = date.today()
        from_str = (from_date or today).strftime("%Y-%m-%dT00:00:00")
        to_str = (to_date or today).strftime("%Y-%m-%dT23:59:59")
        return await data.get_station_average(
            self._session,
            await self._ensure_auth_headers(),
            station_id,
            channel_id,
            from_str,
            to_str,
            timebase,
            5,  # from_timebase
            5,  # to_timebase
        )

    async def get_station_index_fast(
        self,
        station_id: int,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> dict[str, Any]:
        """Get fast air quality index data for a station.

        Args:
            station_id: The station ID.
            from_date: Start date. Defaults to today.
            to_date: End date. Defaults to today.

        Returns:
            Dict with index data.
        """
        today = date.today()
        from_str = (from_date or today).strftime("%Y-%m-%dT00:00:00")
        to_str = (to_date or today).strftime("%Y-%m-%dT23:59:59")
        return await data.get_station_index_fast(
            self._session,
            await self._ensure_auth_headers(),
            station_id,
            from_str,
            to_str,
        )

    async def get_station_missing_days(
        self,
        station_id: int,
        days_back: int = 180,
    ) -> list[str]:
        """Get list of dates with missing data for a station.

        Args:
            station_id: The station ID.
            days_back: How many days back to check. Default 180.

        Returns:
            List of date strings with missing data.
        """
        return await data.get_station_missing_days(
            self._session, await self._ensure_auth_headers(), station_id, days_back
        )

    async def get_station_images(
        self,
        station_id: int,
    ) -> StationImagesResponse:
        """Get images for a station.

        Args:
            station_id: The station ID.

        Returns:
            StationImagesResponse containing station images.
        """
        return await data.get_station_images(
            self._session, await self._ensure_auth_headers(), station_id
        )

    # --- Reference Data ---

    async def get_pollutants(self) -> list[Pollutant]:
        """Get list of all tracked pollutants."""
        return await data.get_pollutants(self._session, await self._ensure_auth_headers())

    async def get_units(self) -> list[Unit]:
        """Get list of measurement units."""
        return await data.get_units(self._session, await self._ensure_auth_headers())

    async def get_data_statuses(self) -> list[DataStatus]:
        """Get list of data status codes."""
        return await data.get_data_statuses(self._session, await self._ensure_auth_headers())

    async def get_manual_stations(self) -> list[dict[str, Any]]:
        """Get list of manual monitoring stations."""
        return await data.get_manual_stations(
            self._session, await self._ensure_auth_headers()
        )

    async def get_manual_pollutants(self) -> list[dict[str, Any]]:
        """Get list of manual measurement pollutants."""
        return await data.get_manual_pollutants(
            self._session, await self._ensure_auth_headers()
        )

    async def get_index_pollutants(
        self,
        index_type: int = 3,
    ) -> list[dict[str, Any]]:
        """Get index pollutant factors.

        Args:
            index_type: Index type. Default 3.
        """
        return await data.get_index_pollutants(
            self._session, await self._ensure_auth_headers(), index_type
        )

    async def get_thresholds(self) -> list[dict[str, Any]]:
        """Get all pollutant threshold values."""
        return await data.get_thresholds(self._session, await self._ensure_auth_headers())

    async def get_advisories(self) -> list[dict[str, Any]]:
        """Get air quality advisories."""
        return await data.get_advisories(self._session, await self._ensure_auth_headers())

    # --- Config & Metadata ---

    async def get_config_index(self) -> dict[str, Any]:
        """Get system configuration."""
        return await data.get_config_index(self._session, await self._ensure_auth_headers())

    async def get_index_configuration(
        self,
        index_type: int = 1,
    ) -> dict[str, Any]:
        """Get index calculation configuration."""
        return await data.get_index_configuration(
            self._session, await self._ensure_auth_headers(), index_type
        )

    async def get_station_terminology(self) -> list[dict[str, Any]]:
        """Get station terminology/classifications."""
        return await data.get_station_terminology(
            self._session, await self._ensure_auth_headers()
        )

    async def get_lut_mng(self) -> list[LookUpTable]:
        """Get all lookup tables (LUT) management data."""
        return await data.get_lut_mng(self._session, await self._ensure_auth_headers())

    # --- Map Layers ---

    async def get_layer_mng(
        self,
        platform: int = 0,
        access_level: int = 1,
    ) -> list[dict[str, Any]]:
        """Get map layer management data."""
        return await data.get_layer_mng(
            self._session, await self._ensure_auth_headers(), platform, access_level
        )

    async def get_layer_queries(
        self,
        layer_id: int,
    ) -> list[dict[str, Any]]:
        """Get feature queries for a map layer."""
        return await data.get_layer_queries(
            self._session, await self._ensure_auth_headers(), layer_id
        )

    async def get_layer_filtered_stations(
        self,
        layer_id: int,
    ) -> list[dict[str, Any]]:
        """Get filtered stations for a map layer."""
        return await data.get_layer_filtered_stations(
            self._session, await self._ensure_auth_headers(), layer_id
        )

    # --- Other ---

    async def get_widget_config(self) -> dict[str, Any]:
        """Get widget configuration."""
        return await data.get_widget_config(self._session, await self._ensure_auth_headers())

    async def get_guest_map_view(self) -> dict[str, Any]:
        """Get guest map view configuration."""
        return await data.get_guest_map_view(self._session, await self._ensure_auth_headers())

    async def get_interpolation_mng(self) -> list[dict[str, Any]]:
        """Get interpolation management data."""
        return await data.get_interpolation_mng(
            self._session, await self._ensure_auth_headers()
        )

    async def get_vineyard_location(
        self,
        location_id: int,
    ) -> dict[str, Any]:
        """Get vineyard/agricultural weather data for a location."""
        return await data.get_vineyard_location(
            self._session, await self._ensure_auth_headers(), location_id
        )

    async def find_nearest_stations(
        self,
        latitude: float,
        longitude: float,
        limit: int = 5,
    ) -> List[Tuple[Any, float]]:
        """Find the nearest air quality monitoring stations to given coordinates.

        Uses Haversine distance calculation to find stations closest to the
        provided latitude/longitude point.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            limit: Maximum number of stations to return (default: 5)

        Returns:
            List of tuples containing (Station object, distance in kilometers),
            sorted by distance (closest first)
        """
        # Get all regions with their stations
        regions = await self.get_regions()

        # Flatten all stations from all regions
        all_stations = []
        for region in regions:
            if region.stations:
                all_stations.extend(region.stations)

        # Filter stations that have location data and calculate distances
        stations_with_distance = []
        for station in all_stations:
            if (
                station.location
                and station.location.latitude is not None
                and station.location.longitude is not None
            ):
                distance = commons.haversine_distance(
                    latitude,
                    longitude,
                    station.location.latitude,
                    station.location.longitude,
                )
                stations_with_distance.append((station, distance))

        # Sort by distance (closest first)
        stations_with_distance.sort(key=lambda x: x[1])

        # Return top N stations
        return stations_with_distance[:limit]
