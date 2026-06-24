from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig


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
    pollutant_id: Optional[int] = field(default=None, metadata={"alias": "pollutantId"})
    datetime: Optional[str] = None

    class Config(BaseConfig):
        serialize_by_alias = True


@dataclass
class RegionData(DataClassDictMixin):
    datetime: Optional[str] = None
    channels: Optional[list[ChannelReading]] = None


@dataclass
class RegionStationData(DataClassDictMixin):
    station_id: int = field(metadata={"alias": "stationId"})
    region_data: Optional[RegionData] = field(default=None, metadata={"alias": "regionData"})

    class Config(BaseConfig):
        serialize_by_alias = True


@dataclass
class IndexDetail(DataClassDictMixin):
    index_id: int = field(metadata={"alias": "indexId"})
    pollutant: Optional[str] = None
    index: Optional[float] = None
    value: Optional[float] = None
    color: Optional[str] = None
    description: Optional[str] = None
    pollutant_id: Optional[int] = field(default=None, metadata={"alias": "pollutantId"})
    pollutant_time_base: Optional[int] = field(default=None, metadata={"alias": "PollutantTimeBase"})

    class Config(BaseConfig):
        serialize_by_alias = True
        extra = "ignore"


@dataclass
class StationIndexData(DataClassDictMixin):
    station_id: int = field(metadata={"alias": "stationId"})
    index_id: Optional[int] = field(default=None, metadata={"alias": "indexId"})
    datetime: Optional[str] = None
    index: Optional[float] = None
    value: Optional[float] = None
    color: Optional[str] = None
    description: Optional[str] = None
    pollutant: Optional[str] = None
    pollutant_id: Optional[int] = field(default=None, metadata={"alias": "pollutantId"})
    indexes: Optional[list[IndexDetail]] = None
    pollutant_time_base: Optional[int] = field(default=None, metadata={"alias": "PollutantTimeBase"})

    class Config(BaseConfig):
        serialize_by_alias = True
        extra = "ignore"


@dataclass
class StationIndexResponse(DataClassDictMixin):
    datetime: Optional[str] = None
    index_type: Optional[int] = field(default=None, metadata={"alias": "indexType"})
    pollutant_id: Optional[int] = field(default=None, metadata={"alias": "pollutantId"})
    pollutant: Optional[str] = None
    index: Optional[float] = None
    value: Optional[float] = None
    color: Optional[str] = None
    station_id: Optional[int] = field(default=None, metadata={"alias": "stationId"})
    description: Optional[str] = None
    data: Optional[list[StationIndexData]] = None

    class Config(BaseConfig):
        serialize_by_alias = True
        extra = "ignore"
