import inspect
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import Any, TypeVar

T = TypeVar("T")


def utcnow() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """
    return datetime.now(UTC)


def default(value: T, default_: T) -> T:
    """
    Returns a default value only when the input is considered unset.

    Empty strings and empty collections are treated as unset values.
    Scalar values are considered unset only when they are null.
    """
    if value is None:
        return default_
    if isinstance(value, (bool, int, float, Decimal, Fraction, Enum)):
        return value
    return value or default_


def as_list(
    value: T | list[T] | tuple[T, ...],
    default_: T | list[T] | tuple[T, ...] | None = None,
    wrap_none: bool = False,
) -> list[T] | None:
    """
    Normalize a value into a list.

    Scalars are wrapped into a single-element list, tuples are converted
    to lists, and lists are returned as-is. By default, `None` is preserved
    and returned as `None`, but if `wrap_none=True`, `None` is wrapped as `[None]`.
    """
    value = value if value is not None else default_
    if value is None:
        return [None] if wrap_none else None
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def as_flat_list(*values: T) -> list[T]:
    """
    Flatten multiple lists and scalars into a single list.

    Each value is normalized using `as_list` before flattening.
    Scalars, lists, and tuples from all arguments are merged into one list.
    None values are included as list items.
    """
    result = []
    for v in values:
        result.extend(as_list(v, wrap_none=True))
    return result


def try_get(obj: Any, field: str, default: Any = None) -> Any:
    """
    Safely get a field from a dict or an object.

    Returns the value when present, otherwise returns the default.
    """
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(field, default)

    return getattr(obj, field, default)


def try_get_public_setter(obj: Any, method_name: str) -> Callable | None:
    """
    Get a method if it's a valid public setter, otherwise return None.

    Public setters are callable methods that accept exactly one parameter
    (excluding self) and have names that don't start with underscore.
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
    return inspect.ismodule(obj) and hasattr(obj, "__path__")


def is_plugin(plugin: Any) -> bool:
    from tiozin.api import PlugIn, Registry

    return (
        inspect.isclass(plugin)
        and issubclass(plugin, PlugIn)
        and plugin is not PlugIn
        and PlugIn not in plugin.__bases__
        and Registry not in plugin.__bases__
    )
