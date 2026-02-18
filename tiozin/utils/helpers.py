from collections import deque
from collections.abc import Iterable
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import TypeVar

import pendulum
from slugify import slugify as _slugify
from uuid_utils import uuid7

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


def human_join(items: list[str]) -> str:
    """
    Join a list of strings into a human-readable sentence.

    Uses commas between items and "and" before the last item,
    following natural English formatting.

    Args:
        items: Strings to join. Must contain at least one item.

    Returns:
        A single string with items joined in human-readable form.

    Examples:
        >>> human_join(["Alice"])
        "Alice"
        >>> human_join(["Alice", "Bob"])
        "Alice and Bob"
        >>> human_join(["Alice", "Bob", "Charlie"])
        "Alice, Bob and Charlie"
    """
    items = list(items)
    return (
        items[0]
        if len(items) == 1
        else " and ".join(items)
        if len(items) == 2
        else f"{', '.join(items[:-1])} and {items[-1]}"
    )


def slugify(value: str) -> str:
    """
    Convert a string into a safe SQL/filesystem identifier.

    Lowercases the value, replaces spaces and special characters with
    underscores, and collapses consecutive separators. The result is
    safe for use as SQL view names, table names, database identifiers,
    and filesystem path segments.

    Uses ``python-slugify`` under the hood with underscore as separator.

    Args:
        value: The string to slugify.

    Returns:
        A lowercase, underscore-separated identifier string.

    Examples:
        >>> slugify("My Step Name")
        "my_step_name"
        >>> slugify("orders - 2024")
        "orders_2024"
        >>> slugify("customer_orders")
        "customer_orders"
    """
    return _slugify(value, separator="_")
