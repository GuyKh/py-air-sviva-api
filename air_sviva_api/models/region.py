from dataclasses import dataclass, field
from typing import Optional

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig


@dataclass
class Location(DataClassDictMixin):
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class Monitor(DataClassDictMixin):
    channel_id: int = field(metadata={"alias": "channelId"})
    name: str
    monitor_serial_number: Optional[str] = field(
        default=None, metadata={"alias": "monitorSerialNumber"}
    )
    instrument_name: Optional[str] = field(
        default=None, metadata={"alias": "instrumentName"}
    )
    alias: Optional[str] = None
    active: bool = False
    type_id: Optional[int] = field(default=None, metadata={"alias": "typeId"})
    pollutant_id: Optional[int] = field(default=None, metadata={"alias": "pollutantId"})
    units: Optional[str] = None
    unit_id: Optional[int] = field(default=None, metadata={"alias": "unitID"})
    description: Optional[str] = None
    map_view: bool = field(default=False, metadata={"alias": "mapView"})
    is_index: bool = field(default=False, metadata={"alias": "isIndex"})
    pollutant_category: Optional[int] = field(
        default=None, metadata={"alias": "PollutantCategory"}
    )
    numeric_format: Optional[str] = field(
        default=None, metadata={"alias": "NumericFormat"}
    )
    low_range: Optional[float] = field(default=None, metadata={"alias": "LowRange"})
    high_range: Optional[float] = field(default=None, metadata={"alias": "HighRange"})
    state: Optional[int] = None
    pct_valid: Optional[float] = field(default=None, metadata={"alias": "PctValid"})
    monitor_title: Optional[str] = field(
        default=None, metadata={"alias": "MonitorTitle"}
    )
    mon_start_date: Optional[str] = field(
        default=None, metadata={"alias": "MON_StartDate"}
    )
    mon_end_date: Optional[str] = field(default=None, metadata={"alias": "MON_EndDate"})

    class Config(BaseConfig):
        serialize_by_alias = True


@dataclass
class Station(DataClassDictMixin):
    station_id: int = field(metadata={"alias": "stationId"})
    name: str
    short_name: Optional[str] = field(default=None, metadata={"alias": "shortName"})
    station_tag: Optional[str] = field(default=None, metadata={"alias": "stationsTag"})
    station_target: Optional[str] = field(
        default=None, metadata={"alias": "StationTarget"}
    )
    target_id: Optional[int] = field(default=None, metadata={"alias": "TargetId"})
    county: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    height: Optional[str] = None
    time_bases: Optional[list[int]] = field(
        default=None, metadata={"alias": "timeBases"}
    )
    additional_timebases: Optional[str] = field(
        default=None, metadata={"alias": "additionalTimebases"}
    )
    is_non_continuous: Optional[str] = field(
        default=None, metadata={"alias": "isNonContinuous"}
    )
    map_view: bool = field(default=False, metadata={"alias": "mapView"})
    aqi_view: bool = field(default=False, metadata={"alias": "aqiView"})
    mobile: bool = False
    aqscode: Optional[str] = field(default=None, metadata={"alias": "AQSCODE"})
    station_code_id: Optional[str] = field(
        default=None, metadata={"alias": "StationCodeID"}
    )
    station_start_date: Optional[str] = field(
        default=None, metadata={"alias": "StationStartDate"}
    )
    station_notes: Optional[str] = field(
        default=None, metadata={"alias": "StationNotes"}
    )
    station_description: Optional[str] = field(
        default=None, metadata={"alias": "StationDescription"}
    )
    location: Optional[Location] = None
    timebase: Optional[int] = None
    active: bool = False
    owner: Optional[str] = None
    owner_id: Optional[int] = field(default=None, metadata={"alias": "ownerId"})
    region_id: Optional[int] = field(default=None, metadata={"alias": "regionId"})
    monitors: Optional[list[Monitor]] = None

    class Config(BaseConfig):
        serialize_by_alias = True


@dataclass
class Region(DataClassDictMixin):
    region_id: int = field(metadata={"alias": "regionId"})
    name: str
    stations: Optional[list[Station]] = None

    class Config(BaseConfig):
        serialize_by_alias = True
