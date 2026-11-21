"""
Custom properties that every converter reads and writes with the same meaning,
so a schema keeps its type parameters when it goes from one format to another.

- `binary`: true for a string of raw bytes, which the standard has no logical
  type for.
- `precision` and `scale`: the digits of a decimal number.
- `typeSize`: the size in bytes of a fixed-size binary type.
- `timeUnit`: the unit of a timestamp or a time, one of millis, micros or nanos.

They have no vendor. What the Open Data Contract Standard already covers stays
in `logicalTypeOptions`: `format` for the size of an integer ("i32", "i64") or
a number ("f32", "f64") and for a UUID ("uuid"), `minLength` and `maxLength`
for the length of a string, and `timezone` for whether a timestamp carries its
timezone.

A converter picks the type it writes only from the logical type, the logical
type options and these custom properties. It never reads the physical type to
pick it: the physical type only says what the source stores.
"""

from __future__ import annotations

BINARY_PROPERTY = "binary"
PRECISION_PROPERTY = "precision"
SCALE_PROPERTY = "scale"
TYPE_SIZE_PROPERTY = "typeSize"
TIME_UNIT_PROPERTY = "timeUnit"
TYPE_PARAMETER_PROPERTIES = {
    BINARY_PROPERTY,
    PRECISION_PROPERTY,
    SCALE_PROPERTY,
    TYPE_SIZE_PROPERTY,
    TIME_UNIT_PROPERTY,
}

MILLIS = "millis"
MICROS = "micros"
NANOS = "nanos"
DEFAULT_TIME_UNIT = MICROS

UUID_FORMAT = "uuid"
DEFAULT_INTEGER_FORMAT = "i64"
DEFAULT_NUMBER_FORMAT = "f64"
