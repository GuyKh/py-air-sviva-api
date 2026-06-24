"""LUT (Look-Up Table) models for the Sviva Air API."""

from dataclasses import dataclass, field
from typing import Optional, Union

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig


@dataclass
class LutDataItem(DataClassDictMixin):
    """A single item within a LUT's Data array."""

    id: int = field(metadata={"alias": "ID"})
    name: str = field(metadata={"alias": "Name"})
    value: Optional[Union[float, int]] = field(default=None, metadata={"alias": "Value"})

    class Config(BaseConfig):
        serialize_by_alias = True


@dataclass
class LookUpTable(DataClassDictMixin):
    """A single lookup table entry from the LUT management endpoint."""

    id: int = field(metadata={"alias": "ID"})
    name: str = field(metadata={"alias": "Name"})
    table_name: str = field(metadata={"alias": "TableName"})
    edit: int = field(metadata={"alias": "Edit"})
    description: int = field(metadata={"alias": "Description"})
    value: int = field(metadata={"alias": "Value"})
    data: list[LutDataItem] = field(default_factory=list, metadata={"alias": "Data"})

    class Config(BaseConfig):
        serialize_by_alias = True


def parse_lut_management_response(data: list[dict]) -> list[LookUpTable]:
    """Parse the LUT management API response (which returns a list directly)."""
    return [LookUpTable.from_dict(item) for item in data]
