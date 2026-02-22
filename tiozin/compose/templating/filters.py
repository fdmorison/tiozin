"""
Jinja2 environment and custom filters for template rendering.
"""

import re
from typing import Any

from jinja2 import Environment, StrictUndefined


def nodash(value: str) -> str:
    """
    Return the input string with all dash characters removed.

    Useful for compact date representations and identifier normalization.

    Example:
        {{ "2026-01-14" | nodash }} -> "20260114"
    """
    if value is None:
        return value
    return str(value).replace("-", "")


def notz(value: str) -> str:
    """
    Return the input string without a trailing timezone designator.

    Removes common ISO 8601 timezone suffixes such as ``Z``,
    ``+HH:MM`` and ``+HHMM`` when present at the end of the string.

    Example:
        {{ "2026-01-14T01:59:57+00:00" | notz }} -> "2026-01-14T01:59:57"
        {{ "2026-01-14T01:59:57Z" | notz }} -> "2026-01-14T01:59:57"
    """
    if value is None:
        return value
    return re.sub(r"([+-]\d{2}:?\d{2}|Z)$", "", str(value))


def compact(value: str) -> str:
    """
    Return the input string with all non-alphanumeric characters removed.

    Useful for generating compact identifiers or normalized keys.

    Example:
        {{ "2026-01-14T01:59" | compact }} -> "20260114T0159"
    """
    if value is None:
        return value
    return re.sub(r"[^A-Za-z0-9]", "", str(value))


def fs_safe(value: Any) -> str:
    """
    Return a filesystem-safe representation of the input string.

    Normalizes common datetime separators to make the value suitable
    for filenames and paths by:

    - replacing ':' with '-'
    - replacing whitespace with '_'
    - removing the colon in timezone offsets (e.g. ``+00:00`` → ``+0000``)

    Example:
        {{ "2026-01-14 01:59" | fs_safe }} -> "2026-01-14_01-59"
    """
    if value is None:
        return value
    value = str(value)
    value = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", value)
    value = value.replace(":", "-")
    value = re.sub(r"\s+", "_", value)
    return value


# =============================================================================
# Environment factory
# =============================================================================
def create_jinja_environment() -> Environment:
    """
    Create and return a preconfigured Jinja2 environment.

    The environment uses ``StrictUndefined`` and registers the custom
    string normalization filters provided by this module.
    """
    env = Environment(
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["nodash"] = nodash
    env.filters["notz"] = notz
    env.filters["compact"] = compact
    env.filters["fs_safe"] = fs_safe
    return env
