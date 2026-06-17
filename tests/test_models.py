"""Tests for data model deserialization from sample API responses."""

from air_sviva_api.models.average import (
    AverageChannelReading,
    AverageDataPoint,
    AverageResponse,
)
from air_sviva_api.models.lut import LookUpTable, LutDataItem, parse_lut_management_response
from air_sviva_api.models.pollutant import DataStatus, Pollutant, Unit
from air_sviva_api.models.reading import (
    ChannelReading,
    RegionStationData,
    StationIndexData,
    StationIndexResponse,
)
from air_sviva_api.models.region import Region, Station


class TestRegionModel:
    def test_region_from_dict(self, sample_region):
        regions = [Region.from_dict(r) for r in sample_region]
        assert len(regions) == 1
        region = regions[0]
        assert region.region_id == 1
        assert region.name == "צפון"

    def test_region_stations(self, sample_region):
        region = Region.from_dict(sample_region[0])
        assert region.stations is not None
        assert len(region.stations) == 1
        station = region.stations[0]
        assert station.station_id == 82
        assert station.name == "חיפה"

    def test_station_location(self, sample_region):
        region = Region.from_dict(sample_region[0])
        assert region.stations is not None
        station = region.stations[0]
        assert station.location is not None
        assert station.location.latitude == 32.794
        assert station.location.longitude == 34.989

    def test_station_monitors(self, sample_region):
        region = Region.from_dict(sample_region[0])
        assert region.stations is not None
        station = region.stations[0]
        assert station.monitors is not None
        assert len(station.monitors) == 2
        assert station.monitors[0].channel_id == 5
        assert station.monitors[0].name == "O3"
        assert station.monitors[1].channel_id == 1
        assert station.monitors[1].name == "SO2"
    def test_station_defaults(self):
        station = Station.from_dict({"stationId": 99, "name": "Test"})
        assert station.active is False
        assert station.location is None
        assert station.monitors is None


class TestPollutantModel:
    def test_pollutant_from_dict(self, sample_pollutant):
        pollutants = [Pollutant.from_dict(p) for p in sample_pollutant]
        assert len(pollutants) == 2
        assert pollutants[0].id == 1
        assert pollutants[0].name == "SO2"
        assert pollutants[1].id == 5

    def test_unit_from_dict(self, sample_unit):
        units = [Unit.from_dict(u) for u in sample_unit]
        assert len(units) == 2
        assert units[0].id == 1
        assert units[0].name == "PPB"

    def test_data_status_from_dict(self, sample_data_status):
        statuses = [DataStatus.from_dict(s) for s in sample_data_status]
        assert len(statuses) == 2
        assert statuses[0].id == 0
        assert statuses[0].name == "Valid"


class TestReadingModel:
    def test_channel_reading_from_dict(self, sample_channel_reading):
        reading = ChannelReading.from_dict(sample_channel_reading)
        assert reading.id == 5
        assert reading.name == "O3"
        assert reading.value == 42.5
        assert reading.valid is True
        assert reading.units == "PPB"

    def test_region_data_from_dict(self, sample_region_data):
        items = [RegionStationData.from_dict(d) for d in sample_region_data]
        assert len(items) == 1
        item = items[0]
        assert item.station_id == 82
        assert item.region_data is not None
        assert item.region_data.channels is not None
        assert len(item.region_data.channels) == 1
        assert item.region_data.channels[0].name == "O3"

    def test_station_index_response_from_dict(self, sample_station_index):
        response = StationIndexResponse.from_dict(sample_station_index)
        assert response.index_type == 3
        assert response.pollutant == "O3"
        assert response.index == 3.5
        assert response.color == "#00FF00"
        assert response.data is not None
        assert len(response.data) == 1
        idx = response.data[0]
        assert isinstance(idx, StationIndexData)
        assert idx.station_id == 82
        assert idx.description == "טוב"

    def test_station_index_response_defaults(self):
        response = StationIndexResponse.from_dict({})
        assert response.datetime is None
        assert response.data is None


class TestAverageModel:
    def test_average_response_from_dict(self, sample_average):
        response = AverageResponse.from_dict(sample_average)
        assert response.data is not None
        assert len(response.data) == 1
        dp = response.data[0]
        assert isinstance(dp, AverageDataPoint)
        assert dp.datetime == "2024-01-15T10:00:00"
        assert dp.channels is not None
        assert len(dp.channels) == 1
        ch = dp.channels[0]
        assert isinstance(ch, AverageChannelReading)
        assert ch.id == 5
        assert ch.name == "O3"
        assert ch.value == 42.5
        assert ch.units == "PPB"
        assert ch.pollutant_id == 5

    def test_average_response_empty(self):
        response = AverageResponse.from_dict({})
        assert response.data is None


class TestLutModel:
    def test_lut_data_item_from_dict(self):
        item = LutDataItem.from_dict({"ID": 1, "Name": "Test", "Value": 1.5})
        assert item.id == 1
        assert item.name == "Test"
        assert item.value == 1.5

    def test_lut_data_item_from_dict_no_value(self):
        item = LutDataItem.from_dict({"ID": 2, "Name": "Test2"})
        assert item.id == 2
        assert item.name == "Test2"
        assert item.value is None

    def test_lookup_table_from_dict(self):
        table = LookUpTable.from_dict({
            "ID": 1,
            "Name": "LAYER_TYPE",
            "TableName": "LUT_LAYER_TYPE",
            "Edit": 0,
            "Description": 0,
            "Value": 0,
            "Data": [
                {"ID": 0, "Name": "Image"},
                {"ID": 1, "Name": "Feature"},
            ],
        })
        assert table.id == 1
        assert table.name == "LAYER_TYPE"
        assert table.table_name == "LUT_LAYER_TYPE"
        assert table.edit == 0
        assert table.description == 0
        assert table.value == 0
        assert len(table.data) == 2
        assert table.data[0].id == 0
        assert table.data[0].name == "Image"
        assert table.data[1].id == 1
        assert table.data[1].name == "Feature"

    def test_parse_lut_management_response(self):
        data = [
            {
                "ID": 1,
                "Name": "LAYER_TYPE",
                "TableName": "LUT_LAYER_TYPE",
                "Edit": 0,
                "Description": 0,
                "Value": 0,
                "Data": [{"ID": 0, "Name": "Image"}],
            },
            {
                "ID": 2,
                "Name": "TIME_BASE",
                "TableName": "LUT_TIME_BASE",
                "Edit": 0,
                "Description": 1,
                "Value": 1,
                "Data": [{"ID": 1, "Name": "1 Minute", "Value": 1.0}],
            },
        ]
        tables = parse_lut_management_response(data)
        assert len(tables) == 2
        assert tables[0].name == "LAYER_TYPE"
        assert tables[1].name == "TIME_BASE"
        assert len(tables[0].data) == 1
        assert len(tables[1].data) == 1
        assert tables[1].data[0].value == 1.0
