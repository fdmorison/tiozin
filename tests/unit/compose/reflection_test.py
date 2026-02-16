from types import SimpleNamespace
from typing import Any

import pytest

from tiozin.compose.reflection import (
    get,
    set_field,
    try_get,
    try_get_public_setter,
    try_set_field,
)


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
