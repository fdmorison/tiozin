from collections import deque
from datetime import datetime
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import Any

import pytest
from pendulum import UTC

from tiozin.utils import (
    as_flat_list,
    as_list,
    default,
    human_join,
    slugify,
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
        ({"item1", "item2"}, ["item1", "item2"]),
        (frozenset({"item1", "item2"}), ["item1", "item2"]),
        (deque(["item1", "item2"]), ["item1", "item2"]),
        (range(3), [0, 1, 2]),
        ({"key": "value"}, [{"key": "value"}]),
        ("scalar", ["scalar"]),
        (42, [42]),
        (True, [True]),
        ([["nested"]], [["nested"]]),
    ],
)
def test_as_list_should_convert_value_to_list(value: Any, expected: list[Any]):
    # Act
    result = as_list(value)

    # Assert
    actual = sorted(result)
    expected = sorted(expected)
    assert actual == expected


def test_as_list_should_return_none_when_none():
    # Act
    result = as_list(None)

    # Assert
    actual = result
    expected = None
    assert actual == expected


def test_as_list_should_return_default_when_none():
    # Act
    result = as_list(None, "default")

    # Assert
    actual = result
    expected = ["default"]
    assert actual == expected


def test_as_list_should_return_none_in_list_none_when_wrap_none():
    # Act
    result = as_list(None, wrap_none=True)

    # Assert
    actual = result
    expected = [None]
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    [[], set(), ()],
)
def test_as_list_should_return_empty_list_when_empty_collection(value: Any):
    # Act
    result = as_list(value)

    # Assert
    actual = result
    expected = []
    assert actual == expected


def test_as_list_should_return_list_when_empty_string():
    # Arrange
    value = ""

    # Act
    result = as_list(value)

    # Assert
    actual = result
    expected = [""]
    assert actual == expected


def test_as_list_should_preserve_list_identity():
    # Arrange
    original_list = ["item"]

    # Act
    result = as_list(original_list)

    # Assert - should be the same object
    assert result is original_list


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


def test_as_flat_list_should_recursively_flatten_nested_lists():
    # Act
    result = as_flat_list([["nested"]], "scalar", [1, 2])

    # Assert
    actual = result
    expected = ["nested", "scalar", 1, 2]
    assert actual == expected


def test_as_flat_list_should_flatten_deeply_nested_structures():
    # Act
    result = as_flat_list([1, [2, [3, [4]]]], 5)

    # Assert
    actual = result
    expected = [1, 2, 3, 4, 5]
    assert actual == expected


def test_as_flat_list_should_flatten_mixed_nested_collections():
    # Act
    result = as_flat_list([[1, 2], [[3], [4, [5]]]], (6, [7]))

    # Assert
    actual = result
    expected = [1, 2, 3, 4, 5, 6, 7]
    assert actual == expected


def test_as_flat_list_should_flatten_frozensets_deques_and_ranges():
    # Act
    result = as_flat_list(frozenset({1, 2}), deque([3, 4]), range(5, 7))

    # Assert
    actual = sorted(result)
    expected = [1, 2, 3, 4, 5, 6]
    assert actual == expected


@pytest.mark.parametrize(
    "values",
    [
        {5, 1, 3, 2, 4},
        {4, 2, 3, 1, 5},
        {1, 5, 2, 4, 3},
    ],
)
def test_as_flat_list_should_sort_sets_for_determinism(values: Any):
    # Act
    result = as_flat_list(values)

    # Assert - regardless of set order, output should always be sorted
    assert result == [1, 2, 3, 4, 5]


# ============================================================================
# Testing utcnow()
# ============================================================================
def test_utcnow_should_return_timezone_aware_datetime():
    # Act
    result = utcnow()

    # Assert
    actual = result.tzinfo
    expected = UTC
    assert actual == expected


def test_utcnow_should_return_current_time():
    # Arrange
    before = datetime.now(UTC)

    # Act
    result = utcnow()

    # Arrange
    after = datetime.now(UTC)

    # Assert
    assert before <= result <= after


# ============================================================================
# Testing human_join()
# ============================================================================
def test_human_join_should_return_single_item_as_is():
    # Act
    actual = human_join(["Alice"])

    # Assert
    expected = "Alice"
    assert actual == expected


def test_human_join_should_join_two_items_with_and():
    # Act
    actual = human_join(["Alice", "Bob"])

    # Assert
    expected = "Alice and Bob"
    assert actual == expected


def test_human_join_should_join_three_items_with_commas_and_and():
    # Act
    actual = human_join(["Alice", "Bob", "Charlie"])

    # Assert
    expected = "Alice, Bob and Charlie"
    assert actual == expected


def test_human_join_should_join_many_items_with_commas_and_and():
    # Act
    actual = human_join(["a", "b", "c", "d", "e"])

    # Assert
    expected = "a, b, c, d and e"
    assert actual == expected


def test_human_join_should_accept_any_iterable():
    # Act
    actual = human_join(("x", "y", "z"))

    # Assert
    expected = "x, y and z"
    assert actual == expected


# ============================================================================
# Testing slugify()
# ============================================================================
@pytest.mark.parametrize(
    "value,expected",
    [
        ("my step name", "my_step_name"),
        ("orders - 2024", "orders_2024"),
        ("customer_orders", "customer_orders"),
        ("My Step Name", "my_step_name"),
        ("  leading and trailing  ", "leading_and_trailing"),
        ("multiple   spaces", "multiple_spaces"),
        ("special!@#chars", "special_chars"),
        ("already_valid", "already_valid"),
        ("UPPER CASE", "upper_case"),
    ],
)
def test_slugify_should_return_safe_identifier(value: str, expected: str):
    # Act
    result = slugify(value)

    # Assert
    actual = result
    assert actual == expected


def test_slugify_should_produce_valid_sql_identifier():
    # Arrange
    name = "My Complex Step - 2024!"

    # Act
    result = slugify(name)

    # Assert
    actual = result.replace("_", "").isalnum() or "_" in result
    expected = True
    assert actual == expected


def test_slugify_should_be_idempotent():
    # Arrange
    name = "some step name"

    # Act
    result = slugify(slugify(name))

    # Assert
    actual = result
    expected = slugify(name)
    assert actual == expected
