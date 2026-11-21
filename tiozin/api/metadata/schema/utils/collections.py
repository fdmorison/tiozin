from __future__ import annotations

from typing import Any


def without_none(attributes: dict[str, Any]) -> dict[str, Any]:
    """
    The attributes that have a value. Nested values are kept as they are.

    Examples:

        ```python
        without_none({"name": "id", "description": None, "map": {"key": None}})
        # {"name": "id", "map": {"key": None}}
        ```
    """
    return {key: value for key, value in attributes.items() if value is not None}
