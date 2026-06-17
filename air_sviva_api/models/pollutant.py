from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig


@dataclass
class Pollutant(DataClassDictMixin):
    id: int = field(metadata={"alias": "Id"})
    name: str = field(metadata={"alias": "Name"})
    description: str = field(metadata={"alias": "Description"})

    class Config(BaseConfig):
        serialize_by_alias = True


@dataclass
class Unit(DataClassDictMixin):
    id: int = field(metadata={"alias": "Id"})
    name: str = field(metadata={"alias": "Name"})
    description: str = field(metadata={"alias": "Description"})

    class Config(BaseConfig):
        serialize_by_alias = True


@dataclass
class DataStatus(DataClassDictMixin):
    id: int = field(metadata={"alias": "Id"})
    name: str = field(metadata={"alias": "Name"})

    class Config(BaseConfig):
        serialize_by_alias = True
