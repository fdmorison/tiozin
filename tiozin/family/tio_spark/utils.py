"""
Pure Python functions.

Functions that operate on standard Python objects and values.

For functions that operate on PySpark ``DataFrame`` and ``Column`` objects,
see ``functions.py``.
"""

from __future__ import annotations

FIELD_DELIMITER = "."
FIELD_PLACEHOLDER = "\x00"
FIELD_ESCAPED_DELIMITER = "\\."


def split_field(field: str) -> list[str]:
    """
    Splits a dotted field path into components.

    Escaped dots (`\.`) are treated as literal characters and do not split the path.

    Args:
        field:
            Dotted field path. Escape dots with `\.` to not treat them as delimiters.

    Returns:
        List of field path components.

    Example:
        ```python
        split_field("address.city")
        # -> ["address", "city"]

        split_field("created\\.at")
        # -> ["created.at"]
        ```
    """
    escaped = field.replace(FIELD_ESCAPED_DELIMITER, FIELD_PLACEHOLDER)
    parts = escaped.split(FIELD_DELIMITER)
    return [part.replace(FIELD_PLACEHOLDER, FIELD_DELIMITER) for part in parts]


def join_field(fields: list[str], escape: bool = False) -> str:
    """
    Joins field path components into a dotted path.

    Spark does not support escaped dots in field names. Set `escape=True` to
    escape literal dots with `\.` when the result must be parsed again by `split_field`.

    Args:
        fields:
            Field path components to join.
        escape:
            Whether to escape literal dots. Defaults to False.

    Returns:
        The dotted field path.

    Example:
        ```python
        join_field(["address", "city"])
        # -> "address.city"

        join_field(["address.city"])
        # -> "address.city"

        join_field(["address.city"], escape=True)
        # -> "address\\.city"

        join_field(["address.city", "name"], escape=True)
        # -> "address\\.city.name"
        ```
    """
    if fields is None:
        return None

    if escape:
        fields = [field.replace(FIELD_DELIMITER, FIELD_ESCAPED_DELIMITER) for field in fields]

    return FIELD_DELIMITER.join(fields)
