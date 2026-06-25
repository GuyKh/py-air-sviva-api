"""Test fixtures and sample data for PyAirSvivaApi tests."""

from typing import Any

import pytest


@pytest.fixture
def sample_region() -> list[dict[str, Any]]:
    return [
        {
            "regionId": 1,
            "name": "צפון",
            "stations": [
                {
                    "stationId": 82,
                    "name": "חיפה",
                    "shortName": "Haifa",
                    "stationsTag": "haifa",
                    "location": {"latitude": 32.794, "longitude": 34.989},
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
                        {
                            "channelId": 1,
                            "name": "SO2",
                            "shortName": "SO2",
                        },
                    ],
                },
            ],
        },
    ]


@pytest.fixture
def sample_pollutant() -> list[dict[str, Any]]:
    return [
        {"Id": 1, "Name": "SO2", "Description": "גופרית דו-חמצנית"},
        {"Id": 5, "Name": "O3", "Description": "אוזון"},
    ]


@pytest.fixture
def sample_unit() -> list[dict[str, Any]]:
    return [
        {"Id": 1, "Name": "PPB", "Description": "Parts per billion"},
        {"Id": 2, "Name": "UG/M3", "Description": "Micrograms per cubic meter"},
    ]


@pytest.fixture
def sample_data_status() -> list[dict[str, Any]]:
    return [
        {"Id": 0, "Name": "Valid"},
        {"Id": 1, "Name": "Invalid"},
    ]


@pytest.fixture
def sample_channel_reading() -> dict[str, Any]:
    return {
        "id": 5,
        "name": "O3",
        "alias": None,
        "value": 42.5,
        "status": 0,
        "valid": True,
        "description": "Ozone",
        "units": "PPB",
        "active": True,
        "pollutantId": 5,
        "datetime": "2024-01-15T10:00:00",
    }


@pytest.fixture
def sample_region_data() -> list[dict[str, Any]]:
    return [
        {
            "stationId": 82,
            "regionData": {
                "datetime": "2024-01-15T10:00:00",
                "channels": [
                    {
                        "id": 5,
                        "name": "O3",
                        "alias": None,
                        "value": 42.5,
                        "status": 0,
                        "valid": True,
                        "description": "Ozone",
                        "units": "PPB",
                        "active": True,
                        "pollutantId": 5,
                        "datetime": "2024-01-15T10:00:00",
                    },
                ],
            },
        },
    ]


@pytest.fixture
def sample_station_index() -> dict[str, Any]:
    return {
        "datetime": "2024-01-15T10:00:00",
        "indexType": 3,
        "pollutantId": 5,
        "pollutant": "O3",
        "index": 3.5,
        "value": 42.5,
        "color": "#00FF00",
        "stationId": 82,
        "description": "טוב",
        "data": [
            {
                "stationId": 82,
                "datetime": "2024-01-15T10:00:00",
                "indexType": 3,
                "index": 3.5,
                "value": 42.5,
                "color": "#00FF00",
                "description": "טוב",
                "pollutant": "O3",
                "pollutantId": 5,
            },
        ],
    }


@pytest.fixture
def sample_average() -> dict[str, Any]:
    return {
        "data": [
            {
                "datetime": "2024-01-15T10:00:00",
                "channels": [
                    {
                        "id": 5,
                        "name": "O3",
                        "value": 42.5,
                        "status": 0,
                        "valid": True,
                        "value_date": "2024-01-15",
                        "units": "PPB",
                        "PollutantId": 5,
                    },
                ],
            },
        ],
    }


@pytest.fixture
def sample_station_image() -> list[dict[str, Any]]:
    return [
        {
            "Id": 217,
            "StationID": 124,
            "extension": "",
            "DocTitle": "קרית גת.jpg",
            "DocData": [255, 216],  # Simplified binary data for testing
            "name": "קרית גת.jpg",
        }
    ]
