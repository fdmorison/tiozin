from __future__ import annotations

import re

from ...model import IntegerFormat, LogicalType, NumberFormat, Property, TiozinTimeUnit
from .enums import SparkTimeType

COMMENT_KEY = "comment"
CUSTOM_PROPERTIES_KEY = "customProperties"
PROPERTY_ATTRIBUTE_KEYS = (
    set(Property.model_fields)
    - {
        "name",
        "description",
        "properties",
    }
    - set(Property.custom_fields)
)

SPARK_TO_LOGICAL = {
    "string": LogicalType.STRING,
    "char": LogicalType.STRING,
    "varchar": LogicalType.STRING,
    "binary": LogicalType.STRING,
    "boolean": LogicalType.BOOLEAN,
    "date": LogicalType.DATE,
    "timestamp": LogicalType.TIMESTAMP,
    "timestamp_ntz": LogicalType.TIMESTAMP,
    "time": LogicalType.TIME,
    "byte": LogicalType.INTEGER,
    "short": LogicalType.INTEGER,
    "integer": LogicalType.INTEGER,
    "long": LogicalType.INTEGER,
    "float": LogicalType.NUMBER,
    "double": LogicalType.NUMBER,
    "decimal": LogicalType.NUMBER,
}
SPARK_TYPES_REQUIRING_LENGTH = {"char", "varchar"}
SPARK_TYPE_ARGUMENT_PATTERN = re.compile(r"\d+")
SPARK_DEFAULT_DECIMAL = (10, 0)
SPARK_DECIMAL_TYPE = "decimal"
SPARK_TIME_TYPE = "time"
SPARK_DEFAULT_TIME_PRECISION = 6
SPARK_MILLIS_PRECISION = 3
SPARK_TIMEZONE_BY_TYPE = {"timestamp": True, "timestamp_ntz": False}
SPARK_FORMATS = {
    "byte": IntegerFormat.INT8,
    "short": IntegerFormat.INT16,
    "integer": IntegerFormat.INT32,
    "long": IntegerFormat.INT64,
    "float": NumberFormat.FLOAT32,
    "double": NumberFormat.FLOAT64,
}
SPARK_BINARY_TYPE = "binary"
SPARK_FIXED_LENGTH_TYPE = "char"
SPARK_COMPLEX_TO_LOGICAL = {
    "struct": LogicalType.OBJECT,
    "array": LogicalType.ARRAY,
    "map": LogicalType.MAP,
}

LOGICAL_TO_SPARK = {
    LogicalType.STRING: "string",
    LogicalType.BOOLEAN: "boolean",
    LogicalType.DATE: "date",
    LogicalType.TIMESTAMP: "timestamp",
}
SPARK_INTEGER_BY_FORMAT = {
    IntegerFormat.INT8: "byte",
    IntegerFormat.INT16: "short",
    IntegerFormat.INT32: "integer",
    IntegerFormat.UINT8: "short",
    IntegerFormat.UINT16: "integer",
    IntegerFormat.INT64: "long",
    IntegerFormat.UINT32: "long",
}
SPARK_NUMBER_BY_FORMAT = {NumberFormat.FLOAT32: "float", NumberFormat.FLOAT64: "double"}
STRUCTURAL_ATTRIBUTES = {"required", "properties", "items", "map"}
DEFAULT_DECIMAL_SCALE = 0
SPARK_TIMESTAMP_WITHOUT_TIMEZONE = "timestamp_ntz"
SPARK_VARIABLE_LENGTH_TYPE = "varchar"
MICROS_TIME_TYPES = {SparkTimeType.TIME, SparkTimeType.TIMESTAMP_NTZ}
DEFAULT_TIME_TYPE = SparkTimeType.TIMESTAMP_NTZ
SPARK_TIME_PRECISION_BY_UNIT = {TiozinTimeUnit.MILLIS: 3, TiozinTimeUnit.MICROS: 6}
SPARK_MAX_TIME_PRECISION = 6
