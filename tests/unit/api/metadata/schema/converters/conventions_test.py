import importlib
import sys

import pytest

from tiozin.api.metadata.schema.converters import conventions


def test_property_aliases_should_keep_old_values():
    # Act
    result = (
        conventions.BINARY_PROPERTY,
        conventions.PRECISION_PROPERTY,
        conventions.SCALE_PROPERTY,
        conventions.TYPE_SIZE_PROPERTY,
        conventions.TIME_UNIT_PROPERTY,
    )

    # Assert
    actual = result
    expected = (
        "binary",
        "precision",
        "scale",
        "typeSize",
        "timeUnit",
    )
    assert actual == expected


def test_type_parameter_properties_should_keep_old_values():
    # Act
    result = conventions.TYPE_PARAMETER_PROPERTIES

    # Assert
    actual = result
    expected = {"binary", "precision", "scale", "typeSize", "timeUnit"}
    assert actual == expected


def test_time_unit_aliases_should_keep_old_values():
    # Act
    result = (
        conventions.MILLIS,
        conventions.MICROS,
        conventions.NANOS,
        conventions.DEFAULT_TIME_UNIT,
    )

    # Assert
    actual = result
    expected = (
        "millis",
        "micros",
        "nanos",
        "micros",
    )
    assert actual == expected


def test_format_aliases_should_keep_old_values():
    # Act
    result = (
        conventions.UUID_FORMAT,
        conventions.DEFAULT_INTEGER_FORMAT,
        conventions.DEFAULT_NUMBER_FORMAT,
    )

    # Assert
    actual = result
    expected = (
        "uuid",
        "i64",
        "f64",
    )
    assert actual == expected


def test_import_should_warn_deprecation(monkeypatch):
    # Arrange
    monkeypatch.delitem(sys.modules, "tiozin.api.metadata.schema.converters.conventions")

    # Act / Assert
    with pytest.warns(DeprecationWarning, match="conventions` is deprecated"):
        importlib.import_module("tiozin.api.metadata.schema.converters.conventions")
