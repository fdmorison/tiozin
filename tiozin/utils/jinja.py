"""
Jinja2 environment and custom filters for template rendering.
"""

import re

from jinja2 import Environment, StrictUndefined

from .helpers import coerce_datetime
from .relative_date import FilesystemDeepView, FilesystemFlatView

SUPPORTED_UNITS = {"minute", "hour", "day", "month", "year"}


# =============================================================================
# String filters
# =============================================================================
def nodash(value: str) -> str:
    """
    Remove dashes.
    Eg: {{ "2026-01-14" | nodash }} -> "20260114"
    """
    if value is None:
        return value
    return str(value).replace("-", "")


def compact(value: str) -> str:
    """
    Remove all non-alphanumeric.
    Eg: {{ "2026-01-14T01:59" | compact }} -> "20260114T0159"
    """
    if value is None:
        return value
    return re.sub(r"[^A-Za-z0-9]", "", str(value))


def sanitize_date(value: str) -> str:
    """
    Make datetime filesystem-safe.
    Eg: {{ "2026-01-14 01:59" | sanitize_date }} -> "2026-01-14_01-59"
    """
    if value is None:
        return value
    value = str(value)
    value = value.replace(":", "-")
    value = re.sub(r"\s+", "_", value)
    return value


# =============================================================================
# Truncation filters
# =============================================================================
def trunc_date(dt, unit: str) -> str:
    """Truncate datetime to start of unit (minute, hour, day, month, year)."""
    if dt is None:
        return dt

    if unit not in SUPPORTED_UNITS:
        raise ValueError(f"Invalid unit '{unit}'. Supported: {', '.join(SUPPORTED_UNITS)}")

    return coerce_datetime(dt).start_of(unit).to_iso8601_string()


def trunc_min(dt) -> str:
    """Truncate to start of minute."""
    return trunc_date(dt, "minute")


def trunc_hour(dt) -> str:
    """Truncate to start of hour."""
    return trunc_date(dt, "hour")


def trunc_day(dt) -> str:
    """Truncate to start of day."""
    return trunc_date(dt, "day")


def trunc_month(dt) -> str:
    """Truncate to start of month."""
    return trunc_date(dt, "month")


def trunc_year(dt) -> str:
    """Truncate to start of year."""
    return trunc_date(dt, "year")


# =============================================================================
# Format filters
# =============================================================================
def iso(value) -> str:
    """Convert to ISO-8601 string."""
    return coerce_datetime(value).to_iso8601_string()


def iso8601(value) -> str:
    """Convert to ISO-8601 string (alias for iso)."""
    return coerce_datetime(value).to_iso8601_string()


def rfc3339(value) -> str:
    """Convert to RFC-3339 string."""
    return coerce_datetime(value).to_rfc3339_string()


def w3c(value) -> str:
    """Convert to W3C datetime string."""
    return coerce_datetime(value).to_w3c_string()


def sql_datetime(value) -> str:
    """Convert to SQL datetime string (YYYY-MM-DD HH:MM:SS)."""
    return coerce_datetime(value).to_datetime_string()


# =============================================================================
# Unix timestamp filters
# =============================================================================
def unix(value) -> int:
    """Convert to Unix timestamp (int seconds)."""
    return coerce_datetime(value).int_timestamp


def unix_float(value) -> float:
    """Convert to Unix timestamp (float seconds)."""
    return coerce_datetime(value).float_timestamp


# =============================================================================
# Datetime part filters
# =============================================================================
def year(value) -> str:
    """Extract year as YYYY."""
    return coerce_datetime(value).format("YYYY")


def month(value) -> str:
    """Extract month as MM."""
    return coerce_datetime(value).format("MM")


def day(value) -> str:
    """Extract day as DD."""
    return coerce_datetime(value).format("DD")


def hour(value) -> str:
    """Extract hour as HH."""
    return coerce_datetime(value).format("HH")


def minute(value) -> str:
    """Extract minute as mm."""
    return coerce_datetime(value).format("mm")


def second(value) -> str:
    """Extract second as ss."""
    return coerce_datetime(value).format("ss")


# =============================================================================
# Filesystem path filters
# =============================================================================
def fs(value) -> FilesystemFlatView:
    """Convert to FilesystemFlatView for flat path formats."""
    return FilesystemFlatView(coerce_datetime(value))


def fsdeep(value) -> FilesystemDeepView:
    """Convert to FilesystemDeepView for Hive-style partitioned paths."""
    return FilesystemDeepView(coerce_datetime(value))


# =============================================================================
# Environment factory
# =============================================================================
def create_jinja_environment() -> Environment:
    """Create a pre-configured Jinja2 environment with custom filters."""
    env = Environment(
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # String filters
    env.filters["nodash"] = nodash
    env.filters["compact"] = compact
    env.filters["sanitize_date"] = sanitize_date
    # Truncation filters
    env.filters["trunc_min"] = trunc_min
    env.filters["trunc_hour"] = trunc_hour
    env.filters["trunc_day"] = trunc_day
    env.filters["trunc_month"] = trunc_month
    env.filters["trunc_year"] = trunc_year
    # Format filters
    env.filters["iso"] = iso
    env.filters["iso8601"] = iso8601
    env.filters["rfc3339"] = rfc3339
    env.filters["w3c"] = w3c
    env.filters["sql_datetime"] = sql_datetime
    # Unix timestamp filters
    env.filters["unix"] = unix
    env.filters["unix_float"] = unix_float
    # Datetime part filters
    env.filters["year"] = year
    env.filters["month"] = month
    env.filters["day"] = day
    env.filters["hour"] = hour
    env.filters["minute"] = minute
    env.filters["second"] = second
    # Filesystem path filters
    env.filters["fs"] = fs
    env.filters["fsdeep"] = fsdeep
    return env
