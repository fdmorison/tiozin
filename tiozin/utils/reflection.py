import inspect
from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeVar

T = TypeVar("T")


def get(obj: Mapping | Sequence | object, field: str | int) -> Any:
    """
    Get a field from a dict, list, or object.

    Args:
        obj: The dict, list, or object to get the field from. Must not be None.
        field: The field name (str) or index (int) to retrieve.

    Returns:
        The field value.

    Raises:
        ValueError: If obj is None.
        KeyError: If field not found or index out of range.

    Examples:
        >>> get({"name": "John"}, "name")
        "John"
        >>> get(["a", "b", "c"], 1)
        "b"
        >>> from types import SimpleNamespace
        >>> get(SimpleNamespace(age=30), "age")
        30
        >>> get({"name": "John"}, "age")
        KeyError: Field 'age' not found in dict
        >>> get(None, "field")
        ValueError: Cannot get field from None object
    """
    if obj is None:
        raise ValueError("Cannot get field from None object")

    try:
        if isinstance(obj, (Mapping, Sequence)):
            return obj[field]
        return getattr(obj, field)
    except (KeyError, IndexError, AttributeError) as e:
        raise KeyError(f"Field '{field}' not found in {type(obj).__name__}") from e


def try_get(obj: Mapping | Sequence | object, field: str | int, default: Any = None) -> Any:
    """
    Safely get a field from a dict, list, or object.

    Args:
        obj: The dict, list, or object to get the field from. Must not be None.
        field: The field name (str) or index (int) to retrieve.
        default: The value to return if the field is not found.

    Returns:
        The field value if found, otherwise the default value.

    Raises:
        ValueError: If obj is None.

    Examples:
        >>> try_get({"name": "John"}, "name")
        "John"
        >>> try_get({"name": "John"}, "age")
        None
        >>> try_get({"name": "John"}, "age", 0)
        0
        >>> try_get(["a", "b", "c"], 1)
        "b"
        >>> try_get(["a", "b"], 5, "default")
        "default"
        >>> from types import SimpleNamespace
        >>> try_get(SimpleNamespace(name="Jane"), "name")
        "Jane"
        >>> try_get(None, "field")
        ValueError: Cannot get field from None object
    """
    if obj is None:
        raise ValueError("Cannot get field from None object")

    try:
        if isinstance(obj, Mapping):
            return obj.get(field, default)
        if isinstance(obj, Sequence):
            return obj[field]
        return getattr(obj, field, default)
    except (IndexError, KeyError, AttributeError):
        return default


def set_field(obj: Mapping | Sequence | object, field: str | int, value: Any) -> None:
    """
    Set a field on a dict, list, or object.

    Args:
        obj: The dict, list, or object to set the field on. Must not be None.
        field: The field name (str) or index (int) to set.
        value: The value to set.

    Raises:
        ValueError: If obj is None.

    Examples:
        >>> obj = {"name": "John"}
        >>> set_field(obj, "age", 30)
        >>> obj
        {"name": "John", "age": 30}
        >>> obj = ["a", "b", "c"]
        >>> set_field(obj, 1, "x")
        >>> obj
        ["a", "x", "c"]
        >>> from types import SimpleNamespace
        >>> obj = SimpleNamespace(name="Jane")
        >>> set_field(obj, "age", 25)
        >>> obj.age
        25
        >>> set_field(None, "field", "value")
        ValueError: Cannot set field on None object
    """
    if obj is None:
        raise ValueError("Cannot set field on None object")

    if isinstance(obj, (Mapping, Sequence)):
        obj[field] = value
    else:
        setattr(obj, field, value)


def try_set_field(obj: Mapping | Sequence | object, field: str | int, value: Any) -> None:
    """
    Safely set a field on a dict, list, or object.

    Unlike set_field(), this function does not raise exceptions if the field
    cannot be set (e.g., on immutable objects), making it safe for
    optional updates.

    Args:
        obj: The dict, list, or object to set the field on. Must not be None.
        field: The field name (str) or index (int) to set.
        value: The value to set.

    Raises:
        ValueError: If obj is None.

    Examples:
        >>> obj = {"name": "John"}
        >>> try_set_field(obj, "age", 30)
        >>> obj
        {"name": "John", "age": 30}
        >>> obj = ["a", "b", "c"]
        >>> try_set_field(obj, 1, "x")
        >>> obj
        ["a", "x", "c"]
        >>> try_set_field(None, "field", "value")
        ValueError: Cannot set field on None object
        >>> from types import SimpleNamespace
        >>> obj = SimpleNamespace(name="Jane")
        >>> try_set_field(obj, "age", 25)
        >>> obj.age
        25
    """
    if obj is None:
        raise ValueError("Cannot set field on None object")

    try:
        if isinstance(obj, (Mapping, Sequence)):
            obj[field] = value
        else:
            setattr(obj, field, value)
    except Exception:
        pass


def merge_fields(source: Any, target: Any, *fields: str, force: bool = False) -> None:
    """
    Merge selected fields from source into target.

    Supports both dicts and objects. By default, only fills missing or None values.
    Use `force=True` to overwrite existing values.

    Args:
        source: Object or dict to read fields from.
        target: Object or dict to write fields to.
        *fields: Field names to merge.
        force: If True, overwrites existing values. If False (default),
               only sets missing or None fields.

    Examples:
        >>> source = {"name": "John", "age": 30}
        >>> target = {"name": "Jane"}
        >>> merge_fields(source, target, "age")
        >>> target
        {"name": "Jane", "age": 30}

        >>> merge_fields(source, target, "name", force=True)
        >>> target  # name overwritten
        {"name": "John", "age": 30}
    """
    if source is None:
        raise ValueError("Cannot merge fields from None source")

    if target is None:
        raise ValueError("Cannot merge fields into None target")

    for field in fields:
        value = get(source, field)

        if not force:
            target_value = try_get(target, field)
            if target_value is not None:
                continue

        set_field(target, field, value)


def try_get_public_setter(obj: Any, method_name: str) -> Callable | None:
    """
    Get a method if it's a valid public setter, otherwise return None.

    Public setters are callable methods that accept exactly one parameter
    (excluding self) and have names that don't start with underscore.

    Args:
        obj: The object to get the method from.
        method_name: The name of the method to retrieve.

    Returns:
        The method if it's a valid public setter, otherwise None.

    Examples:
        >>> class Person:
        ...     def set_name(self, name): self.name = name
        ...     def _set_age(self, age): self.age = age
        ...     def get_name(self): return self.name
        >>> person = Person()
        >>> try_get_public_setter(person, "set_name")
        <bound method Person.set_name...>
        >>> try_get_public_setter(person, "_set_age")
        None
        >>> try_get_public_setter(person, "get_name")
        None
    """
    if method_name.startswith("_"):
        return None

    method = getattr(obj, method_name, None)
    if not callable(method):
        return None

    sig = inspect.signature(method)
    if len(sig.parameters) != 1:
        return None

    return method


def is_package(obj: Any) -> bool:
    """
    Check if an object is a Python package.

    A package is a module that has a __path__ attribute.

    Args:
        obj: The object to check.

    Returns:
        True if the object is a package, False otherwise.

    Examples:
        >>> import os
        >>> is_package(os)
        False
        >>> import collections
        >>> is_package(collections)
        True
    """
    return inspect.ismodule(obj) and hasattr(obj, "__path__")


def is_plugin(plugin: Any) -> bool:
    """
    Check if an object is a valid plugin class.

    A valid plugin is a class that:
    - Inherits from PlugIn
    - Is not the PlugIn base class itself

    Args:
        plugin: The object to check.

    Returns:
        True if the object is a valid plugin class, False otherwise.

    Examples:
        >>> from tiozin.api import PlugIn
        >>> class MyPlugin(PlugIn): pass
        >>> is_plugin(MyPlugin)
        False  # Direct inheritance not allowed
        >>> class BasePlugin(PlugIn): pass
        >>> class MyActualPlugin(BasePlugin): pass
        >>> is_plugin(MyActualPlugin)
        True
    """
    from tiozin.api import PlugIn

    return inspect.isclass(plugin) and issubclass(plugin, PlugIn) and plugin is not PlugIn
