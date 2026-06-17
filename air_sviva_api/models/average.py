from dataclasses import dataclass, field
from typing import Optional

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig


@dataclass
class AverageChannelReading(DataClassDictMixin):
    id: int
    name: str
    value: float = 0.0
    status: int = 0
    valid: bool = False
    value_date: Optional[str] = field(default=None, metadata={"alias": "value_date"})
    units: Optional[str] = None
    pollutant_id: Optional[int] = field(default=None, metadata={"alias": "PollutantId"})

    class Config(BaseConfig):
        serialize_by_alias = True


@dataclass
class AverageDataPoint(DataClassDictMixin):
    datetime: Optional[str] = None
    channels: Optional[list[AverageChannelReading]] = None


@dataclass
class AverageResponse(DataClassDictMixin):
    data: Optional[list[AverageDataPoint]] = None
