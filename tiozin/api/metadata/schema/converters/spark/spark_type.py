from __future__ import annotations

import json
from typing import Any

from ...exceptions import SchemaError
from ...model import LogicalType
from .. import conventions as conv
from . import constants as const


class SparkType:
    """
    A Spark data type in JSON, already parsed: a name such as "long" or
    "decimal(10,2)" for simple types, or a dict for struct, array and map
    types. A string is a type name, never JSON text.

    Examples:

        ```python
        SparkType("long")
        SparkType("decimal(10,2)")
        SparkType({"type": "array", "elementType": "string", "containsNull": True})
        SparkType(
            {
                "type": "map",
                "keyType": "string",
                "valueType": "long",
                "valueContainsNull": True,
            }
        )
        SparkType(
            {
                "type": "struct",
                "fields": [{"name": "id", "type": "long", "nullable": False, "metadata": {}}],
            }
        )
        ```
    """

    def __init__(self, json_value: str | dict[str, Any]) -> None:
        self.json_value = json_value

    @property
    def is_primitive(self) -> bool:
        """
        Whether the type is a simple type, given by its name.

        Examples:

            ```python
            SparkType("long").is_primitive  # True
            SparkType({"type": "array", "elementType": "string"}).is_primitive  # False
            ```
        """
        return isinstance(self.json_value, str)

    @property
    def type_name(self) -> str:
        """
        The name of the type without parameters, such as "decimal", "struct"
        or "map".

        Examples:

            ```python
            SparkType("decimal(10,2)").type_name  # "decimal"
            SparkType({"type": "map", "keyType": "string", "valueType": "long"}).type_name  # "map"
            ```
        """
        match self.json_value:
            case str() as type_name:
                return type_name.split("(", 1)[0].strip().lower()
            case {"type": kind}:
                return kind

    @property
    def logical_type(self) -> LogicalType | None:
        """
        The logical type the Spark type stands for. None for a simple type
        with no logical type.

        Raises SchemaError when a complex type is not struct, array or map.

        Examples:

            ```python
            SparkType("decimal(10,2)").logical_type  # LogicalType.NUMBER
            SparkType({"type": "array", "elementType": "string"}).logical_type  # LogicalType.ARRAY
            ```
        """
        if self.is_primitive:
            return const.SPARK_TO_LOGICAL.get(self.type_name)

        SchemaError.raise_if(
            self.type_name not in const.SPARK_COMPLEX_TO_LOGICAL,
            f"Unsupported Spark type `{self.type_name}`",
        )

        return const.SPARK_COMPLEX_TO_LOGICAL[self.type_name]

    @property
    def physical_type(self) -> str:
        """
        The type exactly as the Spark schema writes it: a simple type as is,
        and a complex type as its JSON.

        Examples:

            ```python
            SparkType("decimal(10,2)").physical_type  # "decimal(10,2)"
            tags = SparkType({"type": "array", "elementType": "string", "containsNull": True})
            tags.physical_type
            # '{"type": "array", "elementType": "string", "containsNull": true}'
            ```
        """
        return self.json_value if self.is_primitive else json.dumps(self.json_value)

    @property
    def type_parameters(self) -> list[dict[str, Any]]:
        """
        The parameters of the type, as the custom properties every converter
        shares: `binary` of a binary, the precision and the scale of a decimal,
        the unit of a timestamp, which is always micros in Spark, and the unit
        of a time, millis up to precision 3 and micros above it. Empty for other types. A
        decimal without arguments is decimal(10,0), as in Spark.

        Examples:

            ```python
            SparkType("decimal(10,2)").type_parameters
            # [{"property": "precision", "value": 10}, {"property": "scale", "value": 2}]

            SparkType("timestamp").type_parameters
            # [{"property": "timeUnit", "value": "micros"}]

            SparkType("long").type_parameters  # []
            ```
        """
        match self.type_name:
            case name if name == const.SPARK_DECIMAL_TYPE:
                arguments = self.type_arguments
                precision, scale = arguments + const.SPARK_DEFAULT_DECIMAL[len(arguments) :]
                return [
                    {"property": conv.PRECISION_PROPERTY, "value": precision},
                    {"property": conv.SCALE_PROPERTY, "value": scale},
                ]
            case name if name in const.SPARK_TIMEZONE_BY_TYPE:
                return [{"property": conv.TIME_UNIT_PROPERTY, "value": conv.MICROS}]
            case name if name == const.SPARK_TIME_TYPE:
                (precision,) = self.type_arguments or (const.SPARK_DEFAULT_TIME_PRECISION,)
                time_unit = (
                    conv.MILLIS if precision <= const.SPARK_MILLIS_PRECISION else conv.MICROS
                )
                return [{"property": conv.TIME_UNIT_PROPERTY, "value": time_unit}]
            case name if name == const.SPARK_BINARY_TYPE:
                return [{"property": conv.BINARY_PROPERTY, "value": True}]
            case _:
                return []

    @property
    def logical_type_options(self) -> dict[str, Any] | None:
        """
        The logical type options the type implies: the size of an integer or a
        number, the length of a char, which is fixed, or of a varchar, and
        whether a timestamp carries its timezone. None for other types.

        Examples:

            ```python
            SparkType("integer").logical_type_options  # {"format": "i32"}
            SparkType("char(3)").logical_type_options  # {"minLength": 3, "maxLength": 3}
            SparkType("varchar(10)").logical_type_options  # {"maxLength": 10}
            SparkType("timestamp_ntz").logical_type_options  # {"timezone": False}
            SparkType("long").logical_type_options  # None
            ```
        """
        match self.type_name:
            case name if name == const.SPARK_FIXED_LENGTH_TYPE and self.type_arguments:
                return {"minLength": self.type_arguments[0], "maxLength": self.type_arguments[0]}
            case name if name in const.SPARK_TYPES_REQUIRING_LENGTH and self.type_arguments:
                return {"maxLength": self.type_arguments[0]}
            case name if name in const.SPARK_FORMATS:
                return {"format": const.SPARK_FORMATS[name]}
            case name if name in const.SPARK_TIMEZONE_BY_TYPE:
                return {"timezone": const.SPARK_TIMEZONE_BY_TYPE[name]}
            case _:
                return None

    @property
    def type_arguments(self) -> tuple[int, ...]:
        """
        The numbers between the parentheses of a simple type, such as (10, 2)
        for "decimal(10,2)". Empty when it has none.
        """
        if not self.is_primitive:
            return ()

        return tuple(
            int(argument) for argument in const.SPARK_TYPE_ARGUMENT_PATTERN.findall(self.json_value)
        )

    @property
    def fields(self) -> list[dict[str, Any]]:
        """
        The fields of a struct type, as Spark struct fields in JSON.
        """
        return self.json_value["fields"]

    @property
    def element_type(self) -> SparkType:
        """
        The type of the elements of an array type.

        Examples:

            ```python
            SparkType({"type": "array", "elementType": "string"}).element_type.json_value
            # "string"
            ```
        """
        return SparkType(self.json_value["elementType"])

    @property
    def key_type(self) -> SparkType:
        """
        The type of the keys of a map type.
        """
        return SparkType(self.json_value["keyType"])

    @property
    def value_type(self) -> SparkType:
        """
        The type of the values of a map type.
        """
        return SparkType(self.json_value["valueType"])

    @property
    def contains_null(self) -> bool:
        """
        Whether an array type allows null elements. True when not given.
        """
        return self.json_value.get("containsNull", True)

    @property
    def value_contains_null(self) -> bool:
        """
        Whether a map type allows null values. True when not given.
        """
        return self.json_value.get("valueContainsNull", True)
