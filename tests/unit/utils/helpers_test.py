from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from types import SimpleNamespace
from typing import Any

import pytest

from tiozin.utils.helpers import (
    as_flat_list,
    as_list,
    default,
    try_get,
    try_get_public_setter,
    utcnow,
)


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
        ([["nested"]], [["nested"]]),
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


def test_as_list_should_preserve_list_identity():
    # Arrange
    original_list = ["item"]

    # Act
    result = as_list(original_list)

    # Assert - should be the same object
    assert result is original_list


def test_as_list_should_wrap_none_when_wrap_none_is_true():
    # Act
    result = as_list(None, wrap_none=True)

    # Assert
    actual = result
    expected = [None]
    assert actual == expected


# ============================================================================
# Testing as_flat_list()
# ============================================================================
def test_as_flat_list_should_flatten_multiple_lists():
    # Act
    result = as_flat_list(["a", "b"], ["c", "d"])

    # Assert
    actual = result
    expected = ["a", "b", "c", "d"]
    assert actual == expected


def test_as_flat_list_should_flatten_tuples():
    # Act
    result = as_flat_list(("a", "b"), ("c", "d"))

    # Assert
    actual = result
    expected = ["a", "b", "c", "d"]
    assert actual == expected


def test_as_flat_list_should_flatten_mixed_types():
    # Act
    result = as_flat_list(["a"], ("b",), "c", [1, 2])

    # Assert
    actual = result
    expected = ["a", "b", "c", 1, 2]
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    ["string", 42, True, {"key": "value"}, None],
)
def test_as_flat_list_should_wrap_single_scalar(value: Any):
    # Act
    result = as_flat_list(value)

    # Assert
    actual = result
    expected = [value]
    assert actual == expected


def test_as_flat_list_should_preserve_single_list():
    # Act
    result = as_flat_list(["a", "b", "c"])

    # Assert
    actual = result
    expected = ["a", "b", "c"]
    assert actual == expected


def test_as_flat_list_should_not_flatten_deep_lists():
    # Act
    result = as_flat_list([["nested"]], "scalar", [1, 2])

    # Assert
    actual = result
    expected = [["nested"], "scalar", 1, 2]
    assert actual == expected


# ============================================================================
# Testing try_get()
# ============================================================================
@pytest.mark.parametrize(
    "obj",
    [
        {"name": "value"},
        SimpleNamespace(name="value"),
    ],
)
def test_try_get_should_return_value_when_field_exists(obj: Any):
    # Act
    result = try_get(obj, "name")

    # Assert
    actual = result
    expected = "value"
    assert actual == expected


@pytest.mark.parametrize(
    "obj",
    [
        {"name": "value"},
        SimpleNamespace(name="value"),
    ],
)
def test_try_get_should_return_default_when_field_not_found(obj: Any):
    # Act
    result = try_get(obj, "age", 0)

    # Assert
    actual = result
    expected = 0
    assert actual == expected


@pytest.mark.parametrize(
    "obj",
    [
        {"name": "value"},
        SimpleNamespace(name="value"),
    ],
)
def test_try_get_should_return_none_by_default_when_field_not_found(obj: Any):
    # Act
    result = try_get(obj, "age")

    # Assert
    actual = result
    expected = None
    assert actual == expected


def test_try_get_should_return_default_when_obj_is_none():
    # Act
    result = try_get(None, "field", "default")

    # Assert
    actual = result
    expected = "default"
    assert actual == expected


def test_try_get_should_return_none_when_obj_is_none_without_default():
    # Act
    result = try_get(None, "field")

    # Assert
    actual = result
    expected = None
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    [0, False, "", None],
)
def test_try_get_should_handle_falsy_values(value: Any):
    # Arrange
    obj = {"field": value}

    # Act
    result = try_get(obj, "field")

    # Assert
    actual = result
    expected = value
    assert actual == expected


# ============================================================================
# Testing try_get_public_setter()
# ============================================================================
def test_try_get_public_setter_should_return_method():
    # Arrange
    class TestClass:
        def set_value(self, _) -> None:
            pass

    # Act
    result = try_get_public_setter(TestClass, "set_value")

    # Assert
    assert callable(result)


def test_try_get_public_setter_should_return_method_when_varargs():
    # Arrange
    class TestClass:
        def input(self, *_):
            pass

    # Act
    result = try_get_public_setter(TestClass, "input")

    # Assert
    assert callable(result)


def test_try_get_public_setter_should_return_none_when_multiple_fixed_parameters():
    # Arrange
    class TestClass:
        def set_values(self, a, b, c):
            pass

    # Act
    result = try_get_public_setter(TestClass, "set_values")

    # Assert
    assert result is None


def test_try_get_public_setter_should_return_none_when_no_parameters():
    # Arrange
    class TestClass:
        def get_value(self):
            pass

    # Act
    result = try_get_public_setter(TestClass, "get_value")

    # Assert
    assert result is None


def test_try_get_public_setter_should_return_none_when_private():
    # Arrange
    class TestClass:
        def _set_value(self, _):
            pass

    # Act
    result = try_get_public_setter(TestClass, "_set_value")

    # Assert
    assert result is None


def test_try_get_public_setter_should_return_none_when_not_callable():
    # Arrange
    class TestClass:
        value = 42

    # Act
    result = try_get_public_setter(TestClass, "value")

    # Assert
    assert result is None


def test_try_get_public_setter_should_return_none_when_method_not_found():
    # Arrange
    class TestClass:
        pass

    # Act
    result = try_get_public_setter(TestClass, "set_value")

    # Assert
    assert result is None


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
