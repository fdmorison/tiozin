from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import Any

import pytest

from tiozin.utils.helpers import as_list, default, utcnow


# ============================================================================
# Testing default()
# ============================================================================
def test_default_should_return_default_value_when_input_is_none():
    # Arrange
    value = None
    default_value = "default"

    # Act
    result = default(value, default_value)

    # Assert
    actual = result
    expected = "default"
    assert actual == expected


def test_default_should_return_original_value_when_input_is_set():
    # Arrange
    value = "actual"
    default_value = "default"

    # Act
    result = default(value, default_value)

    # Assert
    actual = result
    expected = "actual"
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        0,
        -1,
        42,
        0.0,
        -1.5,
        42.7,
        Decimal("0.0"),
        Decimal("999.9"),
        Fraction(0, 1),
        Fraction(1, 2),
    ],
)
def test_default_should_return_scalar_value_regardless_of_truthiness(value: Any):
    # Act
    result = default(value, "default")

    # Assert
    actual = result
    expected = value
    assert actual == expected


def test_default_should_return_enum_value_regardless_of_truthiness():
    # Arrange
    class Status(Enum):
        INACTIVE = 0
        ACTIVE = 1

    value = Status.INACTIVE
    default_value = Status.ACTIVE

    # Act
    result = default(value, default_value)

    # Assert
    actual = result
    expected = Status.INACTIVE
    assert actual == expected


@pytest.mark.parametrize(
    "value,default_value",
    [
        ("", "default"),
        ([], ["default"]),
        ({}, {"key": "default"}),
    ],
)
def test_default_should_return_default_when_collection_is_empty(value: Any, default_value: Any):
    # Act
    result = default(value, default_value)

    # Assert
    actual = result
    expected = default_value
    assert actual == expected


@pytest.mark.parametrize(
    "value,default_value",
    [
        ("actual", "default"),
        (["actual"], ["default"]),
        ({"key": "actual"}, {"key": "default"}),
    ],
)
def test_default_should_return_original_value_when_collection_is_not_empty(
    value: Any, default_value: Any
):
    # Act
    result = default(value, default_value)

    # Assert
    actual = result
    expected = value
    assert actual == expected


# ============================================================================
# Testing as_list()
# ============================================================================
@pytest.mark.parametrize(
    "value,expected",
    [
        (["item1", "item2"], ["item1", "item2"]),
        (("item1", "item2"), ["item1", "item2"]),
        ("scalar", ["scalar"]),
        (42, [42]),
        (True, [True]),
        ({"key": "value"}, [{"key": "value"}]),
    ],
)
def test_as_list_should_convert_value_to_list(value: Any, expected: list[Any]):
    # Act
    result = as_list(value)

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    ["", None, ()],
)
def test_as_list_should_return_none_when_value_is_empty_without_default(value: Any):
    # Act
    result = as_list(value)

    # Assert
    actual = result
    expected = None
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    ["", None, ()],
)
def test_as_list_should_return_default_when_value_is_empty_with_default(value: Any):
    # Act
    result = as_list(value, ["default"])

    # Assert
    actual = result
    expected = ["default"]
    assert actual == expected


def test_as_list_should_handle_nested_lists():
    # Arrange
    value = [["nested"]]

    # Act
    result = as_list(value)

    # Assert
    actual = result
    expected = [["nested"]]
    assert actual == expected


def test_as_list_should_preserve_list_identity():
    # Arrange
    original_list = ["item"]

    # Act
    result = as_list(original_list)

    # Assert - should be the same object
    assert result is original_list


# ============================================================================
# Testing utcnow()
# ============================================================================
def test_utcnow_should_return_timezone_aware_datetime():
    # Act
    result = utcnow()

    # Assert
    actual = result.tzinfo
    expected = timezone.utc
    assert actual == expected


def test_utcnow_should_return_current_time():
    # Arrange
    before = datetime.now(timezone.utc)

    # Act
    result = utcnow()

    # Arrange
    after = datetime.now(timezone.utc)

    # Assert
    assert before <= result <= after
