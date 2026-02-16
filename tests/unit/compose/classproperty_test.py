import pytest

from tiozin.compose.classproperty import classproperty


class Subject:
    _value = "hello"

    @classproperty
    def value(cls) -> str:
        return cls._value


class Child(Subject):
    _value = "world"


# ============================================================================
# Testing classproperty
# ============================================================================
def test_classproperty_should_return_value_from_class():
    """classproperty is accessible directly on the class without instantiation."""

    # Act
    actual = Subject.value

    # Assert
    expected = "hello"
    assert actual == expected


def test_classproperty_should_return_value_from_instance():
    """classproperty is accessible on an instance, resolving from the class."""

    # Arrange
    instance = Subject()

    # Act
    actual = instance.value

    # Assert
    expected = "hello"
    assert actual == expected


def test_classproperty_should_resolve_from_subclass():
    """classproperty resolves from the subclass, not the parent."""

    # Act
    actual = Child.value

    # Assert
    expected = "world"
    assert actual == expected


def test_classproperty_should_preserve_function_metadata():
    """classproperty preserves the wrapped function's name via update_wrapper."""

    # Arrange
    descriptor = Subject.__dict__["value"]

    # Act
    actual = descriptor.__wrapped__

    # Assert
    expected = Subject.__dict__["value"].fget
    assert actual == expected


def test_classproperty_should_reject_instance_assignment():
    """classproperty raises AttributeError when assigned on an instance."""

    # Arrange
    instance = Subject()

    # Act & Assert
    with pytest.raises(AttributeError):
        instance.value = "override"
