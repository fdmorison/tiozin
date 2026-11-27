from __future__ import annotations

import re

from ...model import IntegerFormat, LogicalType, NumberFormat, Property, TimeUnit

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
TIME_AS_TIME = "time"
TIME_AS_TIMESTAMP_NTZ = "timestamp_ntz"
TIME_AS_LONG = "long"
TIME_AS_STRING = "string"
TIME_TYPES = {TIME_AS_TIME, TIME_AS_TIMESTAMP_NTZ, TIME_AS_LONG, TIME_AS_STRING}
MICROS_TIME_TYPES = {TIME_AS_TIME, TIME_AS_TIMESTAMP_NTZ}
DEFAULT_TIME_TYPE = TIME_AS_TIMESTAMP_NTZ
SPARK_TIME_PRECISION_BY_UNIT = {TimeUnit.MILLIS: 3, TimeUnit.MICROS: 6}
SPARK_MAX_TIME_PRECISION = 6
