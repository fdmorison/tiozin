from collections import deque
from collections.abc import Iterable, Mapping
from typing import TypeVar
from uuid import uuid4

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


def generate_id(prefix: str = None, suffix: str = None) -> str:
    """
    Generate a unique identifier.

    Produces a chronologically sortable identifier suitable for naming
    resources or executions. When provided, ``prefix`` is prepended and
    ``suffix`` is appended using the format "<prefix>_<id>_<suffix>".
    """
    identifier = str(uuid7())

    if prefix:
        identifier = f"{prefix}_{identifier}"

    if suffix:
        identifier = f"{identifier}_{suffix}"

    return identifier


def default(value: T | None, default_: T = None) -> T:
    """
    Returns ``value`` unless it is ``None``, otherwise returns ``default_``.

    Mappings are resolved recursively, filling missing or ``None`` keys from ``default_``.

    Args:
        value: Input value.
        default_: Fallback value.

    Examples:
        >>> default(None, "fallback")
        "fallback"
        >>> default(0, 10)
        0
        >>> default(False, True)
        False
        >>> default({"a": None}, {"a": 1, "b": 2})
        {"a": 1, "b": 2}
        >>> default({"a": 1}, {"b": 2})
        {"a": 1, "b": 2}
        >>> default({"a": {"b": None}}, {"a": {"b": 1}})
        {"a": {"b": 1}}
    """
    if value is None:
        return default_

    if isinstance(value, Mapping) and isinstance(default_, Mapping) and default_:
        return {
            key: default(value.get(key), default_.get(key))
            for key in value.keys() | default_.keys()
        }

    return value


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


def human_join(items: list[str], quote: bool = True) -> str:
    """
    Join a list of strings into a human-readable sentence.

    Uses commas between items and "and" before the last item,
    following natural English formatting. Returns an empty string
    for an empty list.

    Args:
        items: Strings to join.
        quote: When `True`, quotes each item before joining.

    Returns:
        A single string with items joined in human-readable form.

    Examples:
        >>> human_join(["Alice"])
        "Alice"
        >>> human_join(["Alice", "Bob"])
        "Alice and Bob"
        >>> human_join(["Alice", "Bob", "Charlie"])
        "Alice, Bob and Charlie"
        >>> human_join(["Alice", "Bob"], quote=True)
        "`Alice` and `Bob`"
    """
    if not items:
        return ""

    quoted = [f"`{i}`" if quote else i for i in items]

    if len(quoted) == 1:
        return quoted[0]

    if len(quoted) == 2:
        return f"{quoted[0]} and {quoted[1]}"

    return f"{', '.join(quoted[:-1])} and {quoted[-1]}"


def randstr(n: int = 6) -> str:
    """
    Generate a short random hex string.

    Useful for creating unique temporary names for tables, files,
    or other resources that must not collide within a run.

    Args:
        n: Number of hex characters to return. Defaults to 6.

    Returns:
        A lowercase hex string of length ``n``.

    Examples:
        >>> hex_token()
        "a3f9c1"
        >>> hex_token(8)
        "a3f9c1b2"
    """
    return uuid4().hex[:n]


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
