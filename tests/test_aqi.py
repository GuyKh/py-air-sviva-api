"""Tests for AQI calculation against HAR-verified values from air.sviva.gov.il."""

import pytest

from air_sviva_api.aqi import (
    AirQualityResult,
    AQIClassification,
    Pollutant,
    _normalize_pollutant_name,
    calc_station_air_quality,
    calc_sub_index,
)


class TestNormalizePollutantName:
    def test_canonical_names(self):
        assert _normalize_pollutant_name("PM2.5") == Pollutant.PM25
        assert _normalize_pollutant_name("PM10") == Pollutant.PM10
        assert _normalize_pollutant_name("NO2") == Pollutant.NO2
        assert _normalize_pollutant_name("O3") == Pollutant.O3
        assert _normalize_pollutant_name("SO2") == Pollutant.SO2
        assert _normalize_pollutant_name("CO") == Pollutant.CO
        assert _normalize_pollutant_name("NOx") == Pollutant.NOX

    def test_aliases(self):
        assert _normalize_pollutant_name("PM25") == Pollutant.PM25
        assert _normalize_pollutant_name("pm25") == Pollutant.PM25
        assert _normalize_pollutant_name("NOX") == Pollutant.NOX
        assert _normalize_pollutant_name("nox") == Pollutant.NOX

    def test_unknown(self):
        assert _normalize_pollutant_name("BENZENE") is None
        assert _normalize_pollutant_name("") is None


class TestSubIndex:
    @pytest.mark.parametrize(
        "conc, expected",
        [
            (4.6, 88),
            (10.7, 72),
            (18.4, 51),
            (19.1, 49),
        ],
    )
    def test_pm25(self, conc, expected):
        sub_idx = calc_sub_index(conc, Pollutant.PM25)
        assert sub_idx is not None
        aqi = 100 - sub_idx
        assert round(aqi) == expected

    @pytest.mark.parametrize(
        "conc, expected",
        [
            (12.3, 91),
            (26.0, 80),
            (45.0, 66),
            (85.1, 35),
        ],
    )
    def test_pm10(self, conc, expected):
        sub_idx = calc_sub_index(conc, Pollutant.PM10)
        assert sub_idx is not None
        aqi = 100 - sub_idx
        assert round(aqi) == expected

    @pytest.mark.parametrize(
        "conc, expected",
        [
            (0.0, 100),
            (49.3, 54),
            (66.6, 38),
        ],
    )
    def test_no2(self, conc, expected):
        sub_idx = calc_sub_index(conc, Pollutant.NO2)
        assert sub_idx is not None
        aqi = 100 - sub_idx
        assert round(aqi) == expected

    @pytest.mark.parametrize(
        "conc, expected",
        [
            (33.9, 53),
            (61.1, 13),
        ],
    )
    def test_o3(self, conc, expected):
        sub_idx = calc_sub_index(conc, Pollutant.O3)
        assert sub_idx is not None
        aqi = 100 - sub_idx
        assert round(aqi) == expected

    def test_unknown_pollutant(self):
        assert calc_sub_index(10.0, "BENZENE") is None

    def test_zero_concentration(self):
        for pollutant in Pollutant:
            sub_idx = calc_sub_index(0.0, pollutant)
            assert sub_idx == 0.0, f"{pollutant} at 0 conc should have sub-index 0"

    def test_negative_concentration(self):
        sub_idx = calc_sub_index(-5.0, Pollutant.PM25)
        assert sub_idx == 0.0

    def test_max_breakpoint_clamps_at_500(self):
        sub_idx = calc_sub_index(200.0, Pollutant.PM25)
        assert sub_idx == 500.0

    def test_extrapolation_capped_at_500(self):
        sub_idx = calc_sub_index(500.0, Pollutant.PM25)
        assert sub_idx == 500.0

    def test_accepts_strings_too(self):
        """Backward compat: plain strings still work in calc_sub_index."""
        assert calc_sub_index(10.7, "PM2.5") == calc_sub_index(10.7, Pollutant.PM25)


class TestStationAirQuality:
    def test_single_pollutant(self):
        result = calc_station_air_quality({Pollutant.PM25: 10.7})
        assert result.aqi_rounded == 72
        assert result.worst_pollutant == Pollutant.PM25
        assert result.classification == AQIClassification.GOOD

    def test_multiple_pollutants_worst_wins(self):
        result = calc_station_air_quality(
            {
                Pollutant.O3: 48.5,
                Pollutant.NO2: 4.6,
                Pollutant.PM10: 26.0,
            }
        )
        assert result.worst_pollutant == Pollutant.O3
        assert result.aqi_rounded == 32

    def test_no_readings(self):
        result = calc_station_air_quality({})
        assert result.classification == AQIClassification.UNKNOWN
        assert result.worst_pollutant is None
        assert result.sub_indices == {}

    def test_unknown_pollutants_only(self):
        result = calc_station_air_quality({"BENZENE": 10.0})
        assert result.classification == AQIClassification.UNKNOWN
        assert result.worst_pollutant is None

    @pytest.mark.parametrize(
        "readings, expected_aqi, expected_class",
        [
            ({Pollutant.PM25: 10.7}, 72, AQIClassification.GOOD),
            ({Pollutant.PM25: 19.1, Pollutant.O3: 61.1}, 13, AQIClassification.MEDIUM),
            ({Pollutant.PM25: 200.0}, -400, AQIClassification.VERY_LOW),
        ],
    )
    def test_classifications(self, readings, expected_aqi, expected_class):
        result = calc_station_air_quality(readings)
        assert result.aqi_rounded == expected_aqi
        assert result.classification == expected_class

    def test_air_quality_result_properties(self):
        result = calc_station_air_quality({Pollutant.PM25: 10.7})
        assert isinstance(result, AirQualityResult)
        assert isinstance(result.aqi, float)
        assert isinstance(result.aqi_rounded, int)
        assert isinstance(result.sub_indices, dict)
        assert Pollutant.PM25 in result.sub_indices
        # String lookup also works (StrEnum)
        assert "PM2.5" in result.sub_indices

    def test_reads_pollutant_aliases(self):
        result = calc_station_air_quality({"PM25": 10.7})
        assert result.aqi_rounded == 72
        assert result.worst_pollutant == Pollutant.PM25

    def test_accepts_string_input(self):
        """Backward compat: plain string keys still work."""
        result = calc_station_air_quality({"PM2.5": 10.7, "NO2": 49.3})
        assert result.aqi_rounded == 54
        assert result.classification == AQIClassification.GOOD
