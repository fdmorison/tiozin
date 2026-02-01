from collections import deque
from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from pathlib import Path
from typing import TypeVar

import pendulum
from uuid_utils import uuid7

from tiozin import config

from .relative_date import RelativeDate

T = TypeVar("T")


def utcnow() -> pendulum.DateTime:
    """
    Return the current UTC time as a timezone-aware datetime.

    Returns Pendulum DateTime which prints in ISO 8601 format.
    """
    return pendulum.now("UTC")


def trim(value: str | None) -> str | None:
    """
    Strip leading and trailing whitespace from the string.

    Returns ``None`` if the input is ``None``.
    """
    if value is None:
        return None
    return value.strip()


def trim_upper(value: str | None) -> str | None:
    """
    Strip leading and trailing whitespace and convert the string to uppercase.

    Returns ``None`` if the input is ``None``.
    """
    if value is None:
        return None
    return value.strip().upper()


def trim_lower(value: str | None) -> str | None:
    """
    Strip leading and trailing whitespace and convert the string to lowercase.

    Returns ``None`` if the input is ``None``.
    """
    if value is None:
        return None
    return value.strip().lower()


def create_temp_dir(*entries: str) -> Path:
    """
    Create a temporary working directory under the application temp root.

    Each entry is treated as a path segment and appended in order, producing
    a hierarchical directory structure. The directory is created if it does
    not already exist.
    """
    path = config.app_temp_workdir
    for key in entries:
        if key:
            path /= key
    path.mkdir(parents=True, exist_ok=True)
    return path


def coerce_datetime(value) -> pendulum.DateTime:
    """
    Convert various datetime representations to Pendulum DateTime.

    Accepts: RelativeDate, pendulum.DateTime, datetime, ISO-8601 string.
    Returns None if value is None.

    Raises:
        TypeError: If value cannot be converted to datetime.
    """
    if value is None:
        return None

    if isinstance(value, RelativeDate):
        return value.dt

    if isinstance(value, pendulum.DateTime):
        return value

    if isinstance(value, datetime):
        return pendulum.instance(value)

    if isinstance(value, str):
        return pendulum.parse(value)

    raise TypeError(
        f"Expected RelativeDate, datetime or ISO string, got {type(value).__name__}: {value!r}"
    )


def generate_id() -> str:
    """
    Generate a unique identifier.

    Creates a time-ordered UUID v7 that uniquely identifies a resource or resource run and can be
    sorted chronologically.

    Returns:
        A UUIDv7 string (time-ordered, globally unique).
    """
    return str(uuid7())


def default(value: T, default_: T) -> T:
    """
    Returns a default value only when the input is considered unset.

    Empty strings and empty collections are treated as unset values.
    Scalar values are considered unset only when they are null.

    Args:
        value: The value to check.
        default_: The default value to return if value is unset.

    Returns:
        The original value if set, otherwise the default value.

    Examples:
        >>> default(None, "fallback")
        "fallback"
        >>> default("", "fallback")
        "fallback"
        >>> default([], [1, 2, 3])
        [1, 2, 3]
        >>> default(0, 10)
        0
        >>> default(False, True)
        False
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

    Scalars are wrapped, iterables are converted, and lists are returned as-is.
    By default, `None` is preserved, unless `wrap_none=True`.

    Args:
        value: The value to normalize into a list.
        default_: Default value to use if value is None.
        wrap_none: If True, wraps None in a list instead of returning None.

    Returns:
        A list containing the value(s), or None.

    Examples:
        >>> as_list("scalar")
        ["scalar"]
        >>> as_list([1, 2, 3])
        [1, 2, 3]
        >>> as_list((1, 2, 3))
        [1, 2, 3]
        >>> as_list({1, 2, 3})
        [1, 2, 3]
        >>> as_list(None)
        None
        >>> as_list(None, wrap_none=True)
        [None]
        >>> as_list(None, "default")
        ["default"]
    """
    value = default_ if value is None else value

    if value is None:
        return [None] if wrap_none else None

    if isinstance(value, list):
        return value

    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray, dict)):
        return list(value)

    return [value]


def as_flat_list(*values: T) -> list[T]:
    """
    Flattens nested iterables into a single list.

    Accepts scalars and arbitrarily nested lists, tuples, sets, frozensets, deques,
    or ranges, preserving the original order of elements.

    Args:
        values: One or more values, possibly nested.

    Returns:
        A flat list of all elements.

    Examples:
        >>> as_flat_list(1, [2, 3], [[4, 5]], 6)
        [1, 2, 3, 4, 5, 6]
        >>> as_flat_list([1, [2, [3, [4]]]])
        [1, 2, 3, 4]
        >>> as_flat_list([[1, 2], [[3], [4, [5]]]])
        [1, 2, 3, 4, 5]
    """
    result = []
    stack = deque(values)

    while stack:
        item = stack.popleft()
        if isinstance(item, (set, frozenset)):
            # Sets are unordered, sort for determinism
            stack.extendleft(reversed(sorted(item)))
        elif isinstance(item, (list, tuple, deque, range)):
            stack.extendleft(reversed(item))
        else:
            result.append(item)

    return result
