import inspect
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import Any, TypeVar

T = TypeVar("T")


def is_package(obj: Any) -> bool:
    return inspect.ismodule(obj) and hasattr(obj, "__path__")


def is_plugin(plugin: Any) -> bool:
    from tiozin.api import Plugable, Registry

    return (
        inspect.isclass(plugin)
        and issubclass(plugin, Plugable)
        and plugin is not Plugable
        and Plugable not in plugin.__bases__
        and Registry not in plugin.__bases__
        and not inspect.isabstract(plugin)
    )


def detect_base_kind(instance: Any, interface: type) -> type:
    """
    Returns the class immediately below the given boundary in the MRO.

    Example:
        detect_base_kind(self, Plugable) -> Input
    """
    mro = type(instance).__mro__
    idx = mro.index(interface)
    if idx == 0:
        raise RuntimeError(f"{interface.__name__} cannot be instantiated directly")
    return mro[idx - 1]


def utcnow() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """
    return datetime.now(timezone.utc)


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
) -> list[T] | None:
    """
    Normalize a value into a list.

    Scalars are wrapped into a single-element list, tuples are converted
    to lists, and lists are returned as-is. `None` is preserved.
    """
    value = default(value, default_)
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]
