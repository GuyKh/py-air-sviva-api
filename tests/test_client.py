"""Tests for SvivaAirClient using mocked HTTP responses."""

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientSession

from air_sviva_api.client import SvivaAirClient
from air_sviva_api.const import GENERATE_TOKEN_URL, GET_API_TOKEN_URL
from air_sviva_api.models.pollutant import Pollutant
from air_sviva_api.models.reading import RegionStationData, StationIndexResponse
from air_sviva_api.models.region import Region, Station
from air_sviva_api.models.station_images import StationImage


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=ClientSession)
    return session


@pytest.fixture
def client(mock_session):
    return SvivaAirClient(mock_session, request_verification_token="test-verif-token")


class TestClientInitialization:
    def test_client_init(self, mock_session):
        client = SvivaAirClient(mock_session)
        assert client._session is mock_session
        assert client._request_verification_token is None
        assert client._auth_token is None

    def test_client_init_with_token(self, mock_session):
        client = SvivaAirClient(mock_session, request_verification_token="abc-123")
        assert client._request_verification_token == "abc-123"

    def test_get_base_headers(self, client):
        headers = client._get_base_headers()
        assert headers["x-requestverificationtoken"] == "test-verif-token"
        assert headers["domainname"] == "sviva"
        assert "Authorization" not in headers


class TestClientGenerateToken:
    @patch("air_sviva_api.commons.send_post_request")
    @patch("air_sviva_api.commons.send_text_post_request")
    async def test_generate_token_success(
        self, mock_send_text_post, mock_send_post, client
    ):
        mock_send_post.return_value = '"42"'  # API token with quotes
        mock_send_text_post.return_value = "99"  # auth token
        token = await client.generate_token()
        assert token == "99"
        assert client._auth_token == "99"

    @patch("air_sviva_api.commons.send_post_request")
    @patch("air_sviva_api.commons.send_text_post_request")
    async def test_generate_token_auto_verif_token(
        self, mock_send_text_post, mock_send_post, mock_session
    ):
        mock_send_post.return_value = '"99"'  # API token with quotes
        mock_send_text_post.return_value = "123"  # auth token
        client = SvivaAirClient(mock_session)
        token = await client.generate_token()
        assert token == "123"
        assert client._request_verification_token is not None

    @patch("air_sviva_api.commons.send_post_request")
    @patch("air_sviva_api.commons.send_text_post_request")
    async def test_refresh_token_success(
        self, mock_send_text_post, mock_send_post, client
    ):
        # Set up an initial token
        client._auth_token = "current_token_123"
        client._request_verification_token = "test-verif-token"

        # Mock the API responses
        mock_send_post.return_value = '"api_token_456"'  # API token with quotes
        mock_send_text_post.return_value = "refreshed_token_789"  # new auth token

        # Call refresh_token
        token = await client.refresh_token()

        # Verify the result
        assert token == "refreshed_token_789"
        assert client._auth_token == "refreshed_token_789"

        # Verify that send_post was called for GetApiToken
        mock_send_post.assert_called_once()
        kwargs = mock_send_post.call_args.kwargs
        assert kwargs["session"] == client._session  # session
        assert kwargs["url"] == GET_API_TOKEN_URL  # URL
        assert kwargs["headers"]["content-type"] == "application/json; charset=UTF-8"
        assert kwargs["headers"]["accept"] == "application/json, text/javascript, */*; q=0.01"
        assert kwargs["headers"]["origin"] == "https://air.sviva.gov.il"
        assert kwargs["headers"]["referer"] == "https://air.sviva.gov.il/"
        assert kwargs["json_data"] == {"userName": "Guest"}

        # Verify that send_text_post was called for GenerateToken with cookie
        mock_send_text_post.assert_called_once()
        kwargs = mock_send_text_post.call_args.kwargs
        assert kwargs["session"] == client._session  # session
        assert kwargs["url"] == GENERATE_TOKEN_URL  # URL
        assert kwargs["headers"]["accept"] == "application/json"
        assert kwargs["headers"]["authorization"] == "ApiToken api_token_456"
        assert kwargs["headers"]["origin"] == "https://air.sviva.gov.il"
        assert kwargs["headers"]["referer"] == "https://air.sviva.gov.il/"
        # Most importantly, check that the cookie header was set
        assert kwargs["headers"]["cookie"] == "X-Access-Token=current_token_123"
        assert kwargs["json_data"] == {}


class TestClientRegions:
    @patch("air_sviva_api.commons.send_get_request")
    async def test_get_regions(self, mock_get, client, sample_region):
        mock_get.return_value = sample_region
        regions = await client.get_regions()
        assert len(regions) == 1
        assert isinstance(regions[0], Region)
        assert regions[0].region_id == 1

    @patch("air_sviva_api.commons.send_get_request")
    async def test_get_regions_latest_data(self, mock_get, client, sample_region_data):
        mock_get.return_value = sample_region_data
        data = await client.get_regions_latest_data([1, 2])
        assert len(data) == 1
        assert isinstance(data[0], RegionStationData)
        assert data[0].station_id == 82


class TestClientStations:
    @patch("air_sviva_api.commons.send_get_request")
    async def test_get_stations_latest_index(
        self, mock_get, client, sample_station_index
    ):
        mock_get.return_value = sample_station_index
        result = await client.get_stations_latest_index()
        assert isinstance(result, StationIndexResponse)
        assert result.index_type == 3

    @patch("air_sviva_api.commons.send_get_request")
    async def test_get_station_average(self, mock_get, client, sample_average):
        mock_get.return_value = sample_average
        result = await client.get_station_average(station_id=82, channel_id=5)
        assert result.data is not None
        assert len(result.data) == 1

    @patch("air_sviva_api.commons.send_get_request")
    async def test_get_station_missing_days(self, mock_get, client):
        mock_get.return_value = ["2024-01-01", "2024-01-02"]
        result = await client.get_station_missing_days(station_id=82)
        assert len(result) == 2
        assert "2024-01-01" in result

    @patch("air_sviva_api.commons.send_post_request")
    async def test_get_station_images(self, mock_post, client, sample_station_image):
        mock_post.return_value = sample_station_image
        result = await client.get_station_images(station_id=124)
        assert result.images is not None
        assert len(result.images) == 1
        assert isinstance(result.images[0], StationImage)
        assert result.images[0].id == 217
        assert result.images[0].station_id == 124
        assert result.images[0].name == "קרית גת.jpg"


class TestClientReferenceData:
    @patch("air_sviva_api.commons.send_get_request")
    async def test_get_pollutants(self, mock_get, client, sample_pollutant):
        mock_get.return_value = sample_pollutant
        result = await client.get_pollutants()
        assert len(result) == 2
        assert isinstance(result[0], Pollutant)

    @patch("air_sviva_api.commons.send_get_request")
    async def test_get_units(self, mock_get, client, sample_unit):
        mock_get.return_value = sample_unit
        result = await client.get_units()
        assert len(result) == 2

    @patch("air_sviva_api.commons.send_get_request")
    async def test_get_advisories(self, mock_get, client):
        mock_get.return_value = [{"id": 1, "text": "Test advisory"}]
        result = await client.get_advisories()
        assert len(result) == 1


class TestClientNearestStations:
    @patch("air_sviva_api.commons.send_get_request")
    async def test_find_nearest_stations_basic(self, mock_get, client, sample_region):
        # Mock the low-level HTTP request to return raw region data
        mock_get.return_value = sample_region

        # Test finding nearest station to Haifa coordinates (should be the Haifa station itself)
        # Haifa coordinates from sample: latitude: 32.794, longitude: 34.989
        result = await client.find_nearest_stations(
            latitude=32.794, longitude=34.989, limit=1
        )

        # Should return exactly one station
        assert len(result) == 1
        station, distance = result[0]

        # Should be a Station instance
        assert isinstance(station, Station)
        assert station.name == "חיפה"
        assert station.station_id == 82

        # Distance should be very close to 0 (same coordinates)
        assert distance < 0.1  # Less than 100 meters

    @patch("air_sviva_api.commons.send_get_request")
    async def test_find_nearest_stations_multiple(
        self, mock_get, client, sample_region
    ):
        # Mock the low-level HTTP request to return raw region data
        mock_get.return_value = sample_region

        # Test finding 2 nearest stations (though we only have 1 in sample)
        result = await client.find_nearest_stations(
            latitude=32.794, longitude=34.989, limit=2
        )

        # Should return exactly one station (since sample only has 1 station with location)
        assert len(result) == 1
        station, distance = result[0]
        assert isinstance(station, Station)
        assert station.name == "חיפה"

    @patch("air_sviva_api.commons.send_get_request")
    async def test_find_nearest_stations_no_location(self, mock_get, client):
        # Create a sample region with a station that has no location
        sample_region_no_location = [
            {
                "regionId": 1,
                "name": "צפון",
                "stations": [
                    {
                        "stationId": 82,
                        "name": "חיפה",
                        "shortName": "Haifa",
                        "stationsTag": "haifa",
                        # No location field
                        "timebase": 10,
                        "active": True,
                        "owner": "משרד הבריאות",
                        "ownerId": 1,
                        "regionId": 1,
                        "monitors": [
                            {
                                "channelId": 5,
                                "name": "O3",
                                "shortName": "O3",
                            },
                        ],
                    },
                ],
            }
        ]

        # Mock the low-level HTTP request to return raw region data
        mock_get.return_value = sample_region_no_location

        # Should return empty list since no stations have location data
        result = await client.find_nearest_stations(
            latitude=32.0, longitude=35.0, limit=5
        )

        assert len(result) == 0

    @patch("air_sviva_api.commons.send_get_request")
    async def test_find_nearest_stations_sorting(self, mock_get, client):
        # Create sample data with two stations at different distances
        sample_region_two_stations = [
            {
                "regionId": 1,
                "name": "צפון",
                "stations": [
                    {
                        "stationId": 82,
                        "name": "חיפה",
                        "shortName": "Haifa",
                        "stationsTag": "haifa",
                        "location": {"latitude": 32.794, "longitude": 34.989},  # Haifa
                        "timebase": 10,
                        "active": True,
                        "owner": "משרד הבריאות",
                        "ownerId": 1,
                        "regionId": 1,
                        "monitors": [],
                    },
                    {
                        "stationId": 83,
                        "name": "תל אביב",
                        "shortName": "Tel Aviv",
                        "stationsTag": "telaviv",
                        "location": {
                            "latitude": 32.085,
                            "longitude": 34.781,
                        },  # Tel Aviv (~80km from Haifa)
                        "timebase": 10,
                        "active": True,
                        "owner": "משרד הבריאות",
                        "ownerId": 1,
                        "regionId": 1,
                        "monitors": [],
                    },
                ],
            }
        ]

        # Mock the low-level HTTP request to return raw region data
        mock_get.return_value = sample_region_two_stations

        # Test from Haifa coordinates - Haifa should be first, Tel Aviv second
        result = await client.find_nearest_stations(
            latitude=32.794, longitude=34.989, limit=2
        )

        assert len(result) == 2

        # First should be Haifa (distance ~0)
        haifa_station, haifa_distance = result[0]
        assert haifa_station.name == "חיפה"
        assert haifa_station.station_id == 82
        assert haifa_distance < 1  # Less than 1km

        # Second should be Tel Aviv (distance ~80km)
        telaviv_station, telaviv_distance = result[1]
        assert telaviv_station.name == "תל אביב"
        assert telaviv_station.station_id == 83
        assert 70 < telaviv_distance < 90  # Between 70-90km
