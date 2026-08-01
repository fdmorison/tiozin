from collections import deque
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import Any
from unittest.mock import patch
from uuid import UUID

import pendulum
import pytest
from pendulum import UTC

from tiozin.utils import (
    as_flat_list,
    as_list,
    as_utc,
    batched,
    check_time_ordered_id,
    default,
    epoch,
    generate_time_ordered_id,
    human_join,
    isozformat,
    prune,
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
# Testing prune()
# ============================================================================
def test_prune_should_remove_root_nulls():
    # Arrange
    data = {
        "a": 1,
        "b": None,
        "c": 3,
    }

    # Act
    result = prune(data)

    # Assert
    actual = result
    expected = {"a": 1, "c": 3}
    assert actual == expected


def test_prune_should_remove_nested_nulls():
    # Arrange
    data = {
        "a": {
            "b": None,
            "c": {
                "d": None,
                "e": 5,
            },
        },
        "f": None,
    }

    # Act
    result = prune(data)

    # Assert
    actual = result
    expected = {
        "a": {
            "c": {
                "e": 5,
            }
        }
    }
    assert actual == expected


def test_prune_should_remove_nested_nulls_from_list_of_dicts():
    # Arrange
    data = [
        {"a": None, "b": 1},
        {"c": 2, "d": None},
    ]

    # Act
    result = prune(data)

    # Assert
    actual = result
    expected = [
        {"b": 1},
        {"c": 2},
    ]
    assert actual == expected


def test_prune_should_remove_nulls_from_dict_of_list_of_dicts():
    # Arrange
    data = {
        "items": [
            {"a": None, "b": 1},
            {"c": 2},
        ],
        "x": None,
    }

    # Act
    result = prune(data)

    # Assert
    actual = result
    expected = {
        "items": [
            {"b": 1},
            {"c": 2},
        ]
    }
    assert actual == expected


def test_prune_should_preserve_falsy_values():
    # Arrange
    data = {
        "a": 0,
        "b": False,
        "c": "",
        "d": [],
        "e": {},
    }

    # Act
    result = prune(data)

    # Assert
    actual = result
    expected = {
        "a": 0,
        "b": False,
        "c": "",
        "d": [],
        "e": {},
    }
    assert actual == expected


def test_prune_should_preserve_dict_when_no_nulls():
    # Arrange
    data = {"a": 1, "b": 2}

    # Act
    result = prune(data)

    # Assert
    actual = result
    expected = {"a": 1, "b": 2}
    assert actual == expected


def test_prune_should_remove_emptied_dict_when_dicts_enabled():
    # Arrange
    data = {
        "a": {"b": None},
        "c": 1,
    }

    # Act
    result = prune(data, dicts=True)

    # Assert
    actual = result
    expected = {"c": 1}
    assert actual == expected


def test_prune_should_cascade_emptied_dicts_when_dicts_enabled():
    # Arrange
    data = {
        "a": {
            "b": {
                "c": None,
            },
        },
        "d": 1,
    }

    # Act
    result = prune(data, dicts=True)

    # Assert
    actual = result
    expected = {"d": 1}
    assert actual == expected


def test_prune_should_preserve_non_empty_dict_when_dicts_enabled():
    # Arrange
    data = {
        "a": {"b": 1},
        "c": 2,
    }

    # Act
    result = prune(data, dicts=True)

    # Assert
    actual = result
    expected = {"a": {"b": 1}, "c": 2}
    assert actual == expected


def test_prune_should_keep_emptied_list_when_lists_disabled():
    # Arrange
    data = {
        "items": [],
        "x": 1,
    }

    # Act
    result = prune(data)

    # Assert
    actual = result
    expected = {"items": [], "x": 1}
    assert actual == expected


def test_prune_should_remove_emptied_list_when_dicts_and_lists_enabled():
    # Arrange
    data = {
        "x": [{"a": None}],
    }

    # Act
    result = prune(data, dicts=True, lists=True)

    # Assert
    actual = result
    expected = {}
    assert actual == expected


def test_prune_should_preserve_none_list_elements_when_lists_enabled():
    # Arrange
    data = {
        "a": [None, None],
    }

    # Act
    result = prune(data, lists=True)

    # Assert
    actual = result
    expected = {"a": [None, None]}
    assert actual == expected


def test_prune_should_preserve_non_empty_containers_when_dicts_and_lists_enabled():
    # Arrange
    data = {
        "a": {"b": 1},
        "c": [1, 2],
    }

    # Act
    result = prune(data, dicts=True, lists=True)

    # Assert
    actual = result
    expected = {"a": {"b": 1}, "c": [1, 2]}
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    ["scalar", 42, 0, False, None],
)
def test_prune_should_return_scalar_unchanged(value: Any):
    # Act
    result = prune(value)

    # Assert
    actual = result
    expected = value
    assert actual == expected


def test_prune_should_return_list_of_scalars_unchanged():
    # Arrange
    data = [1, None, "a"]

    # Act
    result = prune(data)

    # Assert
    actual = result
    expected = [1, None, "a"]
    assert actual == expected


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
# Testing epoch()
# ============================================================================
def test_epoch_should_return_unix_epoch():
    # Act
    result = epoch()

    # Assert
    actual = result
    expected = datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC)
    assert actual == expected


def test_epoch_should_return_timezone_aware_datetime():
    # Act
    result = epoch()

    # Assert
    actual = result.tzinfo
    expected = UTC
    assert actual == expected


# ============================================================================
# Testing as_utc()
# ============================================================================
@pytest.mark.parametrize(
    "dt",
    [
        datetime(2026, 7, 13, 9, 30, tzinfo=timezone(timedelta(hours=-3))),
        pendulum.datetime(2026, 7, 13, 9, 30, tz="America/Sao_Paulo"),
    ],
)
def test_as_utc_should_convert_to_same_instant_in_utc(dt: datetime):
    # Act
    result = as_utc(dt)

    # Assert
    actual = result
    expected = datetime(2026, 7, 13, 12, 30, tzinfo=UTC)
    assert actual == expected


def test_as_utc_should_preserve_instant_when_already_utc():
    # Arrange
    dt = datetime(2026, 7, 13, 12, 30, tzinfo=UTC)

    # Act
    result = as_utc(dt)

    # Assert
    actual = result
    expected = datetime(2026, 7, 13, 12, 30, tzinfo=UTC)
    assert actual == expected


def test_as_utc_should_assume_utc_when_datetime_is_naive():
    # Arrange
    dt = datetime(2026, 7, 13, 9, 30)

    # Act
    result = as_utc(dt)

    # Assert
    actual = result
    expected = datetime(2026, 7, 13, 9, 30, tzinfo=UTC)
    assert actual == expected


# ============================================================================
# Testing isozformat()
# ============================================================================
def test_isozformat_should_preserve_timezone_offset():
    # Arrange
    dt = datetime(2026, 7, 13, 9, 30, tzinfo=timezone(timedelta(hours=-3)))

    # Act
    result = isozformat(dt)

    # Assert
    actual = result
    expected = "2026-07-13T09:30:00-03:00"
    assert actual == expected


def test_isozformat_should_return_none_when_dt_is_none():
    # Act
    result = isozformat(None)

    # Assert
    assert result is None


@pytest.mark.parametrize(
    "dt",
    [
        datetime(2026, 7, 13, 12, 30, 0, tzinfo=UTC),
        pendulum.datetime(2026, 7, 13, 12, 30, 0, tz="UTC"),
    ],
)
def test_isozformat_should_format_utc_with_z_suffix(dt: datetime):
    # Act
    result = isozformat(dt)

    # Assert
    actual = result
    expected = "2026-07-13T12:30:00Z"
    assert actual == expected


@pytest.mark.parametrize(
    "timespec, expected",
    [
        ("seconds", "2026-07-13T12:30:00Z"),
        ("milliseconds", "2026-07-13T12:30:00.123Z"),
        ("microseconds", "2026-07-13T12:30:00.123456Z"),
    ],
)
def test_isozformat_should_apply_given_timespec_precision(timespec: str, expected: str):
    # Arrange
    dt = datetime(2026, 7, 13, 12, 30, 0, 123456, tzinfo=UTC)

    # Act
    result = isozformat(dt, timespec=timespec)

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "timespec",
    ["seconds", "milliseconds", "microseconds"],
)
def test_isozformat_should_ignore_timespec_for_date(timespec: str):
    # Act
    result = isozformat(date(2026, 7, 13), timespec=timespec)

    # Assert
    actual = result
    expected = "2026-07-13"
    assert actual == expected


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
        ("FooBar", "foo_bar"),
        ("FooBarBaz", "foo_bar_baz"),
        ("parseURL", "parse_url"),
        ("HTTPServer", "http_server"),
        ("foo-bar", "foo_bar"),
        ("foo----bar", "foo_bar"),
        ("1foo", "_1foo"),
    ],
)
def test_slugify_should_return_safe_identifier(value: str, expected: str):
    # Act
    result = slugify(value)

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize("value", [None, ""])
def test_slugify_should_accept_null_or_empty_string(value: str | None):
    # Act
    result = slugify(value)

    # Assert
    actual = result
    expected = value
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


# ============================================================================
# Testing check_time_ordered_id()
# ============================================================================
def test_check_time_ordered_id_should_return_value():
    # Act
    result = check_time_ordered_id("01920000-0000-7000-8000-000000000000")

    # Assert
    actual = result
    expected = "01920000-0000-7000-8000-000000000000"
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    ["00000000-0000-4000-8000-000000000000", "not-a-uuid"],
)
def test_check_time_ordered_id_should_raise_when_not_uuidv7(value: str):
    # Act / Assert
    with pytest.raises(ValueError):
        check_time_ordered_id(value)


# ============================================================================
# Testing generate_time_ordered_id()
# ============================================================================
def test_generate_time_ordered_id_should_return_uuidv7():
    # Act
    result = generate_time_ordered_id()

    # Assert
    actual = UUID(result).version
    expected = 7
    assert actual == expected


def test_generate_time_ordered_id_should_return_chronologically_ordered_ids():
    # Act
    result = [generate_time_ordered_id(), generate_time_ordered_id()]

    # Assert
    earlier, later = result
    assert earlier < later


@patch("tiozin.utils.helpers.uuid7")
def test_generate_time_ordered_id_should_prepend_prefix(mock_uuid7):
    # Arrange
    mock_uuid7.return_value = "01920000-0000-7000-8000-000000000000"

    # Act
    result = generate_time_ordered_id(prefix="orders")

    # Assert
    actual = result
    expected = "orders_01920000-0000-7000-8000-000000000000"
    assert actual == expected


@patch("tiozin.utils.helpers.uuid7")
def test_generate_time_ordered_id_should_append_suffix(mock_uuid7):
    # Arrange
    mock_uuid7.return_value = "01920000-0000-7000-8000-000000000000"

    # Act
    result = generate_time_ordered_id(suffix="v2")

    # Assert
    actual = result
    expected = "01920000-0000-7000-8000-000000000000_v2"
    assert actual == expected


@patch("tiozin.utils.helpers.uuid7")
def test_generate_time_ordered_id_should_wrap_with_prefix_and_suffix(mock_uuid7):
    # Arrange
    mock_uuid7.return_value = "01920000-0000-7000-8000-000000000000"

    # Act
    result = generate_time_ordered_id(prefix="orders", suffix="v2")

    # Assert
    actual = result
    expected = "orders_01920000-0000-7000-8000-000000000000_v2"
    assert actual == expected


@patch("tiozin.utils.helpers.uuid7")
@pytest.mark.parametrize(
    "kwargs",
    [{"prefix": ""}, {"suffix": ""}],
)
def test_generate_time_ordered_id_should_ignore_affix_when_empty(mock_uuid7, kwargs):
    # Arrange
    mock_uuid7.return_value = "01920000-0000-7000-8000-000000000000"

    # Act
    result = generate_time_ordered_id(**kwargs)

    # Assert
    actual = result
    expected = "01920000-0000-7000-8000-000000000000"
    assert actual == expected


# ============================================================================
# Testing batched()
# ============================================================================
def test_batched_should_split_into_even_batches():
    # Act
    result = batched([1, 2, 3, 4], 2)

    # Assert
    actual = list(result)
    expected = [(1, 2), (3, 4)]
    assert actual == expected


def test_batched_should_shorten_last_batch_when_not_divisible():
    # Act
    result = batched("ABCDEFG", 3)

    # Assert
    actual = list(result)
    expected = [("A", "B", "C"), ("D", "E", "F"), ("G",)]
    assert actual == expected


def test_batched_should_yield_single_batch_when_n_exceeds_length():
    # Act
    result = batched([1, 2, 3], 10)

    # Assert
    actual = list(result)
    expected = [(1, 2, 3)]
    assert actual == expected


def test_batched_should_yield_nothing_when_iterable_is_empty():
    # Act
    result = batched([], 3)

    # Assert
    actual = list(result)
    expected = []
    assert actual == expected


def test_batched_should_consume_a_generator_input():
    # Arrange
    source = (char for char in "ABCDE")

    # Act
    result = batched(source, 2)

    # Assert
    actual = list(result)
    expected = [("A", "B"), ("C", "D"), ("E",)]
    assert actual == expected


def test_batched_should_not_consume_source_until_iterated():
    # Arrange
    consumed = []

    def source():
        for value in [1, 2, 3]:
            consumed.append(value)
            yield value

    # Act
    batched(source(), 2)

    # Assert
    actual = consumed
    expected = []
    assert actual == expected


def test_batched_should_yield_first_batch_on_first_iteration():
    # Act
    result = batched([1, 2, 3, 4], 2)

    # Assert
    actual = next(result)
    expected = (1, 2)
    assert actual == expected


@pytest.mark.parametrize("n", [0, -1])
def test_batched_should_raise_value_error_when_n_is_less_than_one(n: int):
    # Act / Assert
    with pytest.raises(ValueError):
        list(batched([1, 2, 3], n))
