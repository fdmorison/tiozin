from collections import deque
from datetime import datetime
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from types import SimpleNamespace
from typing import Any

import pendulum
import pytest
from pendulum import UTC

from tiozin.utils.helpers import (
    as_flat_list,
    as_list,
    coerce_datetime,
    create_temp_dir,
    default,
    get,
    merge_fields,
    set_field,
    try_get,
    try_get_public_setter,
    try_set_field,
    utcnow,
)
from tiozin.utils.relative_date import RelativeDate


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
# Testing get()
# ============================================================================
@pytest.mark.parametrize(
    "obj",
    [
        {"name": "value"},
        SimpleNamespace(name="value"),
    ],
)
def test_get_should_return_value_when_field_exists(obj: Any):
    # Act
    result = get(obj, "name")

    # Assert
    actual = result
    expected = "value"
    assert actual == expected


@pytest.mark.parametrize(
    "obj,index,expected",
    [
        (["a", "b", "c"], 0, "a"),
        (["a", "b", "c"], 1, "b"),
        (["a", "b", "c"], 2, "c"),
        (("x", "y", "z"), 0, "x"),
        (("x", "y", "z"), 2, "z"),
    ],
)
def test_get_should_return_value_from_sequence_by_index(obj: Any, index: int, expected: Any):
    # Act
    result = get(obj, index)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "obj",
    [
        {"name": "value"},
        SimpleNamespace(name="value"),
    ],
)
def test_get_should_raise_error_when_field_not_found(obj: Any):
    # Act & Assert
    with pytest.raises(KeyError, match="Field 'age' not found"):
        get(obj, "age")


def test_get_should_raise_error_when_index_out_of_range():
    # Arrange
    obj = ["a", "b", "c"]

    # Act & Assert
    with pytest.raises(KeyError, match="Field '10' not found"):
        get(obj, 10)


def test_get_should_raise_error_when_obj_is_none():
    # Act & Assert
    with pytest.raises(ValueError, match="Cannot get field from None object"):
        get(None, "field")


@pytest.mark.parametrize(
    "value",
    [0, False, "", None],
)
def test_get_should_handle_falsy_values(value: Any):
    # Arrange
    obj = {"field": value}

    # Act
    result = get(obj, "field")

    # Assert
    actual = result
    expected = value
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
    "obj,index,expected",
    [
        (["a", "b", "c"], 0, "a"),
        (["a", "b", "c"], 1, "b"),
        (("x", "y", "z"), 0, "x"),
        (("x", "y", "z"), 2, "z"),
    ],
)
def test_try_get_should_return_value_from_sequence_by_index(obj: Any, index: int, expected: Any):
    # Act
    result = try_get(obj, index)

    # Assert
    assert result == expected


def test_try_get_should_return_default_when_index_out_of_range():
    # Arrange
    obj = ["a", "b"]

    # Act
    result = try_get(obj, 10, "default")

    # Assert
    assert result == "default"


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


@pytest.mark.parametrize("default", [None, "blahblah"])
def test_try_get_should_raise_error_when_obj_is_none(default: str):
    # Act & Assert
    with pytest.raises(ValueError, match="Cannot get field from None object"):
        try_get(None, "field", default)


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
# Testing set_field()
# ============================================================================
@pytest.mark.parametrize(
    "obj",
    [
        {"name": "John"},
        SimpleNamespace(name="John"),
    ],
)
def test_set_field_should_set_field_on_object(obj: Any):
    # Act
    set_field(obj, "age", 30)

    # Assert
    if isinstance(obj, dict):
        assert obj["age"] == 30
    else:
        assert obj.age == 30


def test_set_field_should_set_value_in_list_by_index():
    # Arrange
    obj = ["a", "b", "c"]

    # Act
    set_field(obj, 1, "x")

    # Assert
    assert obj == ["a", "x", "c"]


def test_set_field_should_raise_error_when_setting_tuple():
    # Arrange
    obj = ("a", "b", "c")

    # Act & Assert - tuples are immutable, should raise TypeError
    with pytest.raises(TypeError):
        set_field(obj, 1, "x")


@pytest.mark.parametrize(
    "obj",
    [
        {},
        SimpleNamespace(),
    ],
)
def test_set_field_should_create_new_field(obj: Any):
    # Act
    set_field(obj, "name", "Jane")

    # Assert
    if isinstance(obj, dict):
        assert obj["name"] == "Jane"
    else:
        assert obj.name == "Jane"


def test_set_field_should_raise_error_when_obj_is_none():
    # Act & Assert
    with pytest.raises(ValueError, match="Cannot set field on None object"):
        set_field(None, "field", "value")


@pytest.mark.parametrize(
    "value",
    [0, False, "", None],
)
def test_set_field_should_handle_falsy_values(value: Any):
    # Arrange
    obj = {"field": "initial"}

    # Act
    set_field(obj, "field", value)

    # Assert
    assert obj["field"] == value


# ============================================================================
# Testing try_set_field()
# ============================================================================
@pytest.mark.parametrize(
    "obj",
    [
        {"name": "John"},
        SimpleNamespace(name="John"),
    ],
)
def test_try_set_field_should_set_field_on_object(obj: Any):
    # Act
    try_set_field(obj, "age", 30)

    # Assert
    if isinstance(obj, dict):
        assert obj["age"] == 30
    else:
        assert obj.age == 30


def test_try_set_field_should_set_value_in_list_by_index():
    # Arrange
    obj = ["a", "b", "c"]

    # Act
    try_set_field(obj, 1, "x")

    # Assert
    assert obj == ["a", "x", "c"]


def test_try_set_field_should_raise_error_when_obj_is_none():
    # Act & Assert
    with pytest.raises(ValueError, match="Cannot set field on None object"):
        try_set_field(None, "field", "value")


def test_try_set_field_should_not_raise_on_immutable_object():
    # Arrange
    obj = (1, 2, 3)  # Tuples are immutable

    # Act - should not raise exception
    try_set_field(obj, "field", "value")

    # Assert - tuple unchanged
    assert obj == (1, 2, 3)


def test_try_set_field_should_not_raise_on_tuple_index_assignment():
    # Arrange
    obj = ("a", "b", "c")

    # Act - should not raise exception even though tuples are immutable
    try_set_field(obj, 1, "x")

    # Assert - tuple unchanged
    assert obj == ("a", "b", "c")


# ============================================================================
# Testing merge_fields()
# ============================================================================
def test_merge_fields_should_merge_from_dict_to_dict():
    # Arrange
    source = {"name": "John", "age": 30, "city": "NYC"}
    target = {"name": "Jane"}

    # Act
    merge_fields(source, target, "age", "city")

    # Assert
    actual = target
    expected = {"name": "Jane", "age": 30, "city": "NYC"}
    assert actual == expected


def test_merge_fields_should_merge_from_object_to_object():
    # Arrange
    source = SimpleNamespace(name="John", age=30, city="NYC")
    target = SimpleNamespace(name="Jane")

    # Act
    merge_fields(source, target, "age", "city")

    # Assert
    actual = (target.name, target.age, target.city)
    expected = ("Jane", 30, "NYC")
    assert actual == expected


def test_merge_fields_should_merge_from_dict_to_object():
    # Arrange
    source = {"name": "John", "age": 30}
    target = SimpleNamespace(name="Jane")

    # Act
    merge_fields(source, target, "age")

    # Assert
    actual = (target.name, target.age)
    expected = ("Jane", 30)
    assert actual == expected


def test_merge_fields_should_merge_from_object_to_dict():
    # Arrange
    source = SimpleNamespace(name="John", age=30)
    target = {"name": "Jane"}

    # Act
    merge_fields(source, target, "age")

    # Assert
    actual = target
    expected = {"name": "Jane", "age": 30}
    assert actual == expected


def test_merge_fields_should_not_overwrite_when_force_false_and_target_has_value():
    # Arrange
    source = {"name": "John", "age": 30}
    target = {"name": "Jane", "age": 25}

    # Act
    merge_fields(source, target, "name", "age")

    # Assert
    actual = target
    expected = {"name": "Jane", "age": 25}
    assert actual == expected


def test_merge_fields_should_overwrite_when_force_true_and_target_has_value():
    # Arrange
    source = {"name": "John", "age": 30}
    target = {"name": "Jane", "age": 25}

    # Act
    merge_fields(source, target, "name", "age", force=True)

    # Assert
    actual = target
    expected = {"name": "John", "age": 30}
    assert actual == expected


def test_merge_fields_should_merge_when_target_is_none():
    # Arrange
    source = {"name": "John", "age": 30}
    target = {"name": None, "age": None}

    # Act
    merge_fields(source, target, "name", "age")

    # Assert
    actual = target
    expected = {"name": "John", "age": 30}
    assert actual == expected


def test_merge_fields_should_merge_when_target_field_missing():
    # Arrange
    source = {"name": "John", "age": 30}
    target = {"name": "Jane"}

    # Act
    merge_fields(source, target, "age")

    # Assert
    actual = target
    expected = {"name": "Jane", "age": 30}
    assert actual == expected


def test_merge_fields_should_not_merge_none_values():
    # Arrange
    source = {"name": None, "age": 30}
    target = {"name": "Jane"}

    # Act
    merge_fields(source, target, "name", "age")

    # Assert
    actual = target
    expected = {"name": "Jane", "age": 30}
    assert actual == expected


def test_merge_fields_should_raise_error_when_source_is_none():
    # Arrange
    source = None
    target = {"name": "Jane"}

    # Act & Assert
    with pytest.raises(ValueError, match="Cannot merge fields from None source"):
        merge_fields(source, target, "name")


def test_merge_fields_should_raise_error_when_target_is_none():
    # Arrange
    source = {"name": "John"}
    target = None

    # Act & Assert
    with pytest.raises(ValueError, match="Cannot merge fields into None target"):
        merge_fields(source, target, "name")


def test_merge_fields_should_raise_error_when_field_not_in_source():
    # Arrange
    source = {"name": "John"}
    target = {"name": "Jane"}

    # Act & Assert
    with pytest.raises(KeyError, match="Field 'age' not found"):
        merge_fields(source, target, "age")


# ============================================================================
# Testing try_get_public_setter()
# ============================================================================
def test_try_get_public_setter_should_return_method():
    # Arrange
    class TestClass:
        def set_value(self, _) -> None:
            pass

    # Act
    result = try_get_public_setter(TestClass(), "set_value")

    # Assert
    assert callable(result)


def test_try_get_public_setter_should_return_method_when_varargs():
    # Arrange
    class TestClass:
        def input(self, *_):
            pass

    # Act
    result = try_get_public_setter(TestClass(), "input")

    # Assert
    assert callable(result)


def test_try_get_public_setter_should_return_none_when_multiple_fixed_parameters():
    # Arrange
    class TestClass:
        def set_values(self, a, b, c):
            pass

    # Act
    result = try_get_public_setter(TestClass(), "set_values")

    # Assert
    assert result is None


def test_try_get_public_setter_should_return_none_when_no_parameters():
    # Arrange
    class TestClass:
        def get_value(self):
            pass

    # Act
    result = try_get_public_setter(TestClass(), "get_value")

    # Assert
    assert result is None


def test_try_get_public_setter_should_return_none_when_private():
    # Arrange
    class TestClass:
        def _set_value(self, _):
            pass

    # Act
    result = try_get_public_setter(TestClass(), "_set_value")

    # Assert
    assert result is None


def test_try_get_public_setter_should_return_none_when_not_callable():
    # Arrange
    class TestClass:
        value = 42

    # Act
    result = try_get_public_setter(TestClass(), "value")

    # Assert
    assert result is None


def test_try_get_public_setter_should_return_none_when_method_not_found():
    # Arrange
    class TestClass:
        pass

    # Act
    result = try_get_public_setter(TestClass(), "set_value")

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
# Testing create_temp_dir()
# ============================================================================
def test_create_temp_dir_should_create_directory_with_single_entry(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)

    # Act
    result = create_temp_dir("my_job")

    # Assert
    actual = result
    expected = tmp_path / "my_job"
    assert actual == expected
    assert actual.exists()
    assert actual.is_dir()


def test_create_temp_dir_should_create_nested_directory_with_multiple_entries(
    tmp_path, monkeypatch
):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)

    # Act
    result = create_temp_dir("job_name", "run_id", "step_name")

    # Assert
    actual = result
    expected = tmp_path / "job_name" / "run_id" / "step_name"
    assert actual == expected
    assert actual.exists()
    assert actual.is_dir()


def test_create_temp_dir_should_skip_empty_entries(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)

    # Act
    result = create_temp_dir("job_name", "", "step_name")

    # Assert
    actual = result
    expected = tmp_path / "job_name" / "step_name"
    assert actual == expected


def test_create_temp_dir_should_skip_none_entries(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)

    # Act
    result = create_temp_dir("job_name", None, "step_name")

    # Assert
    actual = result
    expected = tmp_path / "job_name" / "step_name"
    assert actual == expected


def test_create_temp_dir_should_return_base_path_when_no_entries(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)

    # Act
    result = create_temp_dir()

    # Assert
    actual = result
    expected = tmp_path
    assert actual == expected


def test_create_temp_dir_should_be_idempotent(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)

    # Act
    first_call = create_temp_dir("my_job", "run_123")
    second_call = create_temp_dir("my_job", "run_123")

    # Assert
    actual = first_call
    expected = second_call
    assert actual == expected
    assert actual.exists()


def test_create_temp_dir_should_accept_path_as_first_entry(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)
    base_path = tmp_path / "existing_job"
    base_path.mkdir()

    # Act
    result = create_temp_dir(base_path, "step_name")

    # Assert
    actual = result
    expected = base_path / "step_name"
    assert actual == expected
    assert actual.exists()


# ============================================================================
# Testing coerce_datetime()
# ============================================================================
def test_coerce_datetime_should_return_none_when_none():
    # Act
    actual = coerce_datetime(None)

    # Assert
    expected = None
    assert actual == expected


def test_coerce_datetime_should_return_dt_from_relative_date():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = coerce_datetime(rd)

    # Assert
    expected = dt
    assert actual == expected


def test_coerce_datetime_should_return_pendulum_datetime_unchanged():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")

    # Act
    actual = coerce_datetime(dt)

    # Assert
    assert actual is dt


def test_coerce_datetime_should_convert_datetime_to_pendulum():
    # Arrange
    dt = datetime(2026, 1, 17, 10, 30, 45)

    # Act
    actual = coerce_datetime(dt)

    # Assert
    assert isinstance(actual, pendulum.DateTime)
    assert actual.year == 2026
    assert actual.month == 1
    assert actual.day == 17


def test_coerce_datetime_should_parse_iso_string():
    # Act
    actual = coerce_datetime("2026-01-17T10:30:45+00:00")

    # Assert
    assert isinstance(actual, pendulum.DateTime)
    assert actual.year == 2026
    assert actual.month == 1
    assert actual.day == 17


def test_coerce_datetime_should_raise_when_invalid_type():
    # Act/Assert
    with pytest.raises(TypeError, match="Expected RelativeDate, datetime or ISO string"):
        coerce_datetime(12345)
