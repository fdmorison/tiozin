from __future__ import annotations

import re

from ...model import LogicalType
from .. import conventions as conv

AVRO_TO_LOGICAL = {
    "string": LogicalType.STRING,
    "bytes": LogicalType.STRING,
    "uuid": LogicalType.STRING,
    "boolean": LogicalType.BOOLEAN,
    "int": LogicalType.INTEGER,
    "long": LogicalType.INTEGER,
    "float": LogicalType.NUMBER,
    "double": LogicalType.NUMBER,
    "date": LogicalType.DATE,
    "time-millis": LogicalType.TIME,
    "time-micros": LogicalType.TIME,
    "timestamp-millis": LogicalType.TIMESTAMP,
    "timestamp-micros": LogicalType.TIMESTAMP,
    "local-timestamp-millis": LogicalType.TIMESTAMP,
    "local-timestamp-micros": LogicalType.TIMESTAMP,
    "timestamp-nanos": LogicalType.TIMESTAMP,
    "local-timestamp-nanos": LogicalType.TIMESTAMP,
}

AVRO_LOGICAL_TO_PRIMITIVE = {
    "uuid": "string",
    "decimal": "bytes",
    "date": "int",
    "time-millis": "int",
    "time-micros": "long",
    "timestamp-millis": "long",
    "timestamp-micros": "long",
    "local-timestamp-millis": "long",
    "local-timestamp-micros": "long",
    "timestamp-nanos": "long",
    "local-timestamp-nanos": "long",
}

AVRO_FORMATS = {"int": "i32", "long": "i64", "float": "f32", "double": "f64"}
AVRO_INTEGER_BY_FORMAT = {
    "i8": "int",
    "i16": "int",
    "i32": "int",
    "u8": "int",
    "u16": "int",
    "i64": "long",
    "u32": "long",
}
AVRO_NUMBER_BY_FORMAT = {"f32": "float", "f64": "double"}
BYTES_TYPE = "bytes"
AVRO_STRUCTURAL_TYPES = {"record", "array", "map"}
UUID_LOGICAL_TYPE = "uuid"

AVRO_TEMPORAL_TYPES = {
    "time-millis": (LogicalType.TIME, None, conv.MILLIS),
    "time-micros": (LogicalType.TIME, None, conv.MICROS),
    "timestamp-millis": (LogicalType.TIMESTAMP, True, conv.MILLIS),
    "timestamp-micros": (LogicalType.TIMESTAMP, True, conv.MICROS),
    "timestamp-nanos": (LogicalType.TIMESTAMP, True, conv.NANOS),
    "local-timestamp-millis": (LogicalType.TIMESTAMP, False, conv.MILLIS),
    "local-timestamp-micros": (LogicalType.TIMESTAMP, False, conv.MICROS),
    "local-timestamp-nanos": (LogicalType.TIMESTAMP, False, conv.NANOS),
}

AVRO_COMPLEX_TO_LOGICAL = {
    "record": LogicalType.OBJECT,
    "array": LogicalType.ARRAY,
    "map": LogicalType.MAP,
    "enum": LogicalType.STRING,
    "fixed": LogicalType.STRING,
}

LOGICAL_TO_AVRO = {
    LogicalType.STRING: "string",
    LogicalType.BOOLEAN: "boolean",
    LogicalType.DATE: "date",
}

NULL_TYPE = "null"
MAP_KEY_TYPE = "string"
DECIMAL_LOGICAL_TYPE = "decimal"
ODCS_KEY = "odcs"

FIXED_TYPE = "fixed"
AVRO_NAMED_TYPES = {"record", "enum", FIXED_TYPE}
AVRO_KNOWN_TYPES = {NULL_TYPE, *AVRO_TO_LOGICAL, *AVRO_COMPLEX_TO_LOGICAL}

DEFAULT_PROPERTY = "default"
ORDER_PROPERTY = "order"
TYPE_NAME_PROPERTY = "typeName"
NAMESPACE_PROPERTY = "namespace"
FIELD_PROPERTIES = {DEFAULT_PROPERTY, ORDER_PROPERTY}
NAMED_TYPE_PROPERTIES = {TYPE_NAME_PROPERTY, NAMESPACE_PROPERTY}
RECORD_PROPERTIES = {NAMESPACE_PROPERTY}
ALIAS_SOURCE = "avro"

AVRO_VENDOR = "avro"
FIELD_KEYS = {"name", "type", "doc", "aliases", DEFAULT_PROPERTY, ORDER_PROPERTY, ODCS_KEY}
RECORD_KEYS = {"type", "name", "doc", "aliases", "fields", NAMESPACE_PROPERTY, ODCS_KEY}
TYPE_KEYS = {
    "type",
    "name",
    "fields",
    "symbols",
    "size",
    "items",
    "values",
    "precision",
    "scale",
    NAMESPACE_PROPERTY,
    ODCS_KEY,
}
LOGICAL_TYPE_KEY = "logicalType"
UNDERSTOOD_LOGICAL_TYPES = {DECIMAL_LOGICAL_TYPE, *AVRO_LOGICAL_TO_PRIMITIVE}

DEFAULT_RECORD_NAME = "root"
AVRO_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
MAP_KEY_LOGICAL_TYPES = {LogicalType.STRING, None}
SCHEMA_NATIVE_ATTRIBUTES = {"description", "properties"}
PROPERTY_NATIVE_ATTRIBUTES = {"name", "physicalType", "properties", "items", "map"}
SCHEMA_RESERVED_KEYS = RECORD_KEYS | FIELD_PROPERTIES | NAMED_TYPE_PROPERTIES
FIELD_RESERVED_KEYS = FIELD_KEYS | NAMED_TYPE_PROPERTIES | conv.TYPE_PARAMETER_PROPERTIES
