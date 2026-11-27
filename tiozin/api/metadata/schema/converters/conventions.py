"""
Deprecated aliases of the schema conventions, kept for plugins that still
import them. Use `TiozinCustomProperty`, `TiozinTimeUnit` and `TiozinLogicalType` from the
schema model, and the defaults in `tiozin.config`.

This module will be removed in the next major version.
"""

from __future__ import annotations

import warnings

from tiozin import config

from ..model import TiozinCustomProperty, TiozinLogicalType, TiozinTimeUnit

warnings.warn(
    "`tiozin.api.metadata.schema.converters.conventions` is deprecated and will be removed "
    "in the next major version. Use `TiozinCustomProperty`, `TiozinTimeUnit` and "
    "`TiozinLogicalType` from `tiozin.api.metadata.schema.model`, and the defaults in "
    "`tiozin.config`.",
    DeprecationWarning,
    stacklevel=2,
)

BINARY_PROPERTY = TiozinCustomProperty.BINARY
PRECISION_PROPERTY = TiozinCustomProperty.PRECISION
SCALE_PROPERTY = TiozinCustomProperty.SCALE
TYPE_SIZE_PROPERTY = TiozinCustomProperty.TYPE_SIZE
TIME_UNIT_PROPERTY = TiozinCustomProperty.TIME_UNIT
TYPE_PARAMETER_PROPERTIES = {
    TiozinCustomProperty.BINARY,
    TiozinCustomProperty.PRECISION,
    TiozinCustomProperty.SCALE,
    TiozinCustomProperty.TYPE_SIZE,
    TiozinCustomProperty.TIME_UNIT,
}

MILLIS = TiozinTimeUnit.MILLIS
MICROS = TiozinTimeUnit.MICROS
NANOS = TiozinTimeUnit.NANOS
DEFAULT_TIME_UNIT = config.default_schema_time_unit

UUID_FORMAT = TiozinLogicalType.UUID
DEFAULT_INTEGER_FORMAT = config.default_schema_integer_format
DEFAULT_NUMBER_FORMAT = config.default_schema_number_format
