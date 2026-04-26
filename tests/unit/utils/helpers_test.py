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


class _Status(Enum):
    INACTIVE = 0
    ACTIVE = 1


# ============================================================================
# Testing default()
# ============================================================================
@pytest.mark.parametrize(
    "value",
    [
        "actual",
        ["actual"],
        {"key": "actual"},
        {"actual"},
        frozenset({"actual"}),
        ("actual",),
        deque(["actual"]),
        True,
        -1,
        42,
        -1.5,
        42.7,
        Decimal("999.9"),
        Fraction(1, 2),
        _Status.INACTIVE,
    ],
)
def test_default_should_preserve_value(value: Any):
    # Act
    result = default(value, "fallback")

    # Assert
    actual = result
    expected = value
    assert actual == expected


@pytest.mark.parametrize(
    "default_value",
    ["fallback", 0, [], False],
)
def test_default_should_fallback_when_null(default_value: Any):
    # Act
    result = default(None, default_value)

    # Assert
    actual = result
    expected = default_value
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    [False, 0, 0.0, Decimal("0.0"), Fraction(0, 1)],
)
def test_default_should_preserve_falsy_scalar(value: Any):
    # Act
    result = default(value, "fallback")

    # Assert
    actual = result
    expected = value
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    ["   ", "\t", "\n"],
)
def test_default_should_preserve_blank_string(value: str):
    # Act
    result = default(value, "fallback")

    # Assert
    actual = result
    expected = value
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    ["", [], {}, set(), frozenset(), (), deque()],
)
def test_default_should_preserve_empty_collection(value: Any):
    # Act
    result = default(value, "fallback")

    # Assert
    actual = result
    expected = value
    assert actual == expected


def test_default_should_recursively_replace_null_fields():
    # Act
    result = default({"a": None}, {"a": 1, "b": 2})

    # Assert
    actual = result
    expected = {"a": 1, "b": 2}
    assert actual == expected


def test_default_should_recursively_add_missing_keys():
    # Act
    result = default({"a": 1}, {"b": 2})

    # Assert
    actual = result
    expected = {"a": 1, "b": 2}
    assert actual == expected


@pytest.mark.parametrize(
    "value,default_,expected",
    [
        pytest.param(
            {"a": {"b": None}},
            {"a": {"b": 1}},
            {"a": {"b": 1}},
            id="two-levels",
        ),
        pytest.param(
            {"a": {"b": {"c": None}}},
            {"a": {"b": {"c": 1}}},
            {"a": {"b": {"c": 1}}},
            id="three-levels",
        ),
    ],
)
def test_default_should_apply_recursively_at_any_depth(value: Any, default_: Any, expected: Any):
    # Act
    result = default(value, default_)

    # Assert
    actual = result
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
@pytest.mark.parametrize("items", [[], None])
def test_human_join_should_return_empty_string_when_items_is_empty_or_none(items: list):
    # Act
    actual = human_join(items)

    # Assert
    expected = ""
    assert actual == expected


@pytest.mark.parametrize(
    "items,expected",
    [
        (["Alice"], "Alice"),
        (["Alice", "Bob"], "Alice and Bob"),
        (["Alice", "Bob", "Charlie"], "Alice, Bob and Charlie"),
        (["a", "b", "c", "d", "e"], "a, b, c, d and e"),
        (("x", "y", "z"), "x, y and z"),
    ],
)
def test_human_join_should_join_items_in_human_readable_form(items: list[str], expected: str):
    # Act
    actual = human_join(items, quote=False)

    # Assert
    assert actual == expected


@pytest.mark.parametrize(
    "items,expected",
    [
        (["Alice"], "`Alice`"),
        (["Alice", "Bob"], "`Alice` and `Bob`"),
        (["Alice", "Bob", "Charlie"], "`Alice`, `Bob` and `Charlie`"),
    ],
)
def test_human_join_should_quote_items_when_quote_is_true(items: list[str], expected: str):
    # Act
    actual = human_join(items, quote=True)

    # Assert
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
