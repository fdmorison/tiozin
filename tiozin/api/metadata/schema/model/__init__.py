"""
The schema domain model.

The models follow the schema section of the Open Data Contract Standard
v3.2.0: same attributes, same names and same defaults. `Schema` is also a
Tiozin `Metadata`, so it reads and writes files.

Examples:

    ```python
    from tiozin import Property, Schema

    schema = Schema(
        name="users",
        properties=[
            Property(name="id", logicalType="integer", primaryKey=True),
            Property(name="email", logicalType="string", classification="pii"),
        ],
    )
    ```
"""

from .authoritative_definition import AuthoritativeDefinition
from .constraint import Constraint
from .context import Context
from .custom_property import CustomProperty
from .element import Element
from .enum_value import EnumValue
from .enums import Case, LogicalType
from .map import Map
from .model import Model
from .options import (
    ArrayOptions,
    DateOptions,
    IntegerOptions,
    LogicalTypeOptions,
    NumberOptions,
    ObjectOptions,
    StringOptions,
    TimestampOptions,
    VectorOptions,
)
from .path import PropertyPath
from .property import Property
from .quality import Quality
from .relationship import Relationship
from .schema import Schema
from .synonym import Synonym
from .verified_statement import VerifiedStatement

Map.model_rebuild(_types_namespace={"Property": Property})
Property.model_rebuild()
Schema.model_rebuild()

__all__ = [
    "ArrayOptions",
    "AuthoritativeDefinition",
    "Case",
    "Constraint",
    "Context",
    "CustomProperty",
    "DateOptions",
    "Element",
    "EnumValue",
    "IntegerOptions",
    "LogicalType",
    "LogicalTypeOptions",
    "Map",
    "Model",
    "NumberOptions",
    "ObjectOptions",
    "Property",
    "PropertyPath",
    "Quality",
    "Relationship",
    "Schema",
    "StringOptions",
    "Synonym",
    "TimestampOptions",
    "VectorOptions",
    "VerifiedStatement",
]
