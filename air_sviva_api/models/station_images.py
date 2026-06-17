from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig


@dataclass
class StationImage(DataClassDictMixin):
    id: int = field(metadata={"alias": "Id"})
    station_id: int = field(metadata={"alias": "StationID"})
    extension: str
    doc_title: str = field(metadata={"alias": "DocTitle"})
    doc_data: List[int] = field(metadata={"alias": "DocData"})
    name: str

    class Config(BaseConfig):
        serialize_by_alias = True


@dataclass
class StationImagesResponse(DataClassDictMixin):
    images: Optional[List[StationImage]] = None

    class Config(BaseConfig):
        serialize_by_alias = True
