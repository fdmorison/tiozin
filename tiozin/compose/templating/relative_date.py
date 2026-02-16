from __future__ import annotations

from datetime import datetime

import pendulum
from pendulum import DateTime


class RelativeDate:
    """
    Represents a logical date relative to a base reference DateTime.

    All representations are exposed as attributes (properties),
    making it fully compatible with Jinja templates.

    Example usage (Jinja):
        {{ D[-1].iso8601 }}
        {{ D[0].fs.hour }}
        {{ D[-1].yesterday.date }}
    """

    def __init__(self, dt: DateTime):
        self._dt = dt

    @staticmethod
    def coerce(value: RelativeDate | DateTime | datetime | str) -> DateTime | None:
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

    def __getitem__(self, offset: int) -> RelativeDate:
        """
        Allows relative navigation using index syntax.

        Examples:
            D[0]    → today
            D[-1]   → yesterday
            D[7]    → 7 days ahead
        """
        if not isinstance(offset, int):
            raise TypeError("RelativeDate offset must be an integer")

        return RelativeDate(self._dt.add(days=offset))

    def __str__(self) -> str:
        """
        Default string representation for templates.

        Equivalent to {{ D.date }}.
        """
        return self.date

    def __repr__(self) -> str:
        return f"RelativeDate({self.date})"

    # ==========================================================================
    # Core
    # ==========================================================================

    @property
    def dt(self) -> DateTime:
        """Pendulum DateTime object."""
        return self._dt

    @property
    def date(self) -> str:
        """Date string, eg: 2026-01-14"""
        return self._dt.to_date_string()

    # ==========================================================================
    # Web / ISO standards
    # ==========================================================================

    @property
    def iso(self) -> str:
        """ISO 8601 datetime, eg: 2026-01-14T01:59:57+00:00"""
        return self._dt.to_iso8601_string()

    @property
    def iso8601(self) -> str:
        """ISO 8601 datetime, eg: 2026-01-14T01:59:57+00:00"""
        return self._dt.to_iso8601_string()

    @property
    def rfc3339(self) -> str:
        """RFC 3339 datetime, eg: 2026-01-14T01:59:57+00:00"""
        return self._dt.to_rfc3339_string()

    @property
    def w3c(self) -> str:
        """W3C datetime, eg: 2026-01-14T01:59:57+00:00"""
        return self._dt.to_w3c_string()

    @property
    def sql_datetime(self) -> str:
        """SQL datetime, eg: 2026-01-14 01:59:57"""
        return self._dt.to_datetime_string()

    # ==========================================================================
    # Unix timestamps
    # ==========================================================================

    @property
    def unix(self) -> int:
        """Unix timestamp (int seconds), eg: 1768370397"""
        return self._dt.int_timestamp

    @property
    def unix_float(self) -> float:
        """Unix timestamp (float seconds), eg: 1768370397.0"""
        return self._dt.float_timestamp

    # ==========================================================================
    # Filesystem formats
    # ==========================================================================

    @property
    def fs(self) -> FilesystemFlatView:
        """Filesystem-safe flat formats, eg: {{ D.fs.hour }}"""
        return FilesystemFlatView(self._dt)

    @property
    def fsdeep(self) -> FilesystemDeepView:
        """Filesystem-safe deep (hierarchical) paths, eg: {{ D.fsdeep.hour }}"""
        return FilesystemDeepView(self._dt)

    # ==========================================================================
    # Relative navigation (still returns RelativeDate)
    # ==========================================================================

    @property
    def today(self) -> RelativeDate:
        """Same day, eg: D[n].today == D[n]"""
        return self

    @property
    def yesterday(self) -> RelativeDate:
        """Previous day, eg: D[n].yesterday == D[n-1]"""
        return RelativeDate(self._dt.subtract(days=1))

    @property
    def tomorrow(self) -> RelativeDate:
        """Next day, eg: D[n].tomorrow == D[n+1]"""
        return RelativeDate(self._dt.add(days=1))

    # ==========================================================================
    # Datetime parts (calendar, time, timezone)
    # ==========================================================================

    @property
    def YYYY(self) -> str:
        """Year (4 digits), eg: 2026"""
        return self._dt.format("YYYY")

    @property
    def MM(self) -> str:
        """Month (2 digits), eg: 01"""
        return self._dt.format("MM")

    @property
    def DD(self) -> str:
        """Day of month (2 digits), eg: 14"""
        return self._dt.format("DD")

    @property
    def DDD(self) -> str:
        """Day of year (3 digits), eg: 014"""
        return self._dt.format("DDD")

    @property
    def HH(self) -> str:
        """Hour (2 digits, 24h), eg: 01"""
        return self._dt.format("HH")

    @property
    def mm(self) -> str:
        """Minute (2 digits), eg: 59"""
        return self._dt.format("mm")

    @property
    def ss(self) -> str:
        """Second (2 digits), eg: 57"""
        return self._dt.format("ss")

    @property
    def time(self) -> str:
        """Time string, eg: 01:59:57"""
        return self._dt.to_time_string()

    @property
    def Z(self) -> str:
        """Timezone offset with colon, eg: +00:00"""
        return self._dt.format("Z")

    @property
    def ZZ(self) -> str:
        """Timezone offset without colon, eg: +0000"""
        return self._dt.format("ZZ")

    @property
    def z(self) -> str:
        """Timezone abbreviation, eg: UTC"""
        return self._dt.format("z")

    @property
    def zz(self) -> str:
        """Timezone abbreviation, eg: UTC"""
        return self._dt.format("zz")

    # ==========================================================================
    # Airflow standards
    # ==========================================================================

    @property
    def ds(self) -> str:
        """Airflow ds format, eg: 2026-01-14"""
        return self._dt.to_date_string()

    @property
    def ts(self) -> str:
        """Airflow ts format, eg: 2026-01-14T01:59:57"""
        return self._dt.format("YYYY-MM-DD[T]HH:mm:ss")

    @property
    def prev_ds(self) -> str:
        """Previous day ds, eg: 2026-01-13"""
        return self._dt.subtract(days=1).to_date_string()

    @property
    def next_ds(self) -> str:
        """Next day ds, eg: 2026-01-15"""
        return self._dt.add(days=1).to_date_string()

    @property
    def execution_date(self) -> DateTime:
        """Airflow execution_date (DateTime object)."""
        return self._dt

    @property
    def logical_date(self) -> DateTime:
        """Airflow logical_date (DateTime object)."""
        return self._dt

    @property
    def data_interval_start(self) -> DateTime:
        """Airflow data_interval_start (DateTime object)."""
        return self._dt

    @property
    def data_interval_end(self) -> DateTime:
        """Airflow data_interval_end (next day DateTime object)."""
        return self._dt.add(days=1)

    def to_dict(self) -> dict[str, object]:
        """Export all public @property attributes as a flat dict."""
        dyct = {}

        for name in dir(self):
            if name.startswith("_"):
                continue

            value = getattr(self, name)

            if callable(value):
                continue

            dyct[name] = value

        return dyct


# ==============================================================================
# Filesystem flat view
# ==============================================================================


class FilesystemFlatView:
    """Flat filesystem-safe date representations."""

    def __init__(self, dt: DateTime):
        self._dt = dt

    @property
    def date(self) -> str:
        """Date, eg: 2026-01-14"""
        return self._dt.to_date_string()

    @property
    def day(self) -> str:
        """Date (alias for date), eg: 2026-01-14"""
        return self._dt.to_date_string()

    @property
    def hour(self) -> str:
        """Date with hour, eg: 2026-01-14T01"""
        return self._dt.format("YYYY-MM-DD[T]HH")

    @property
    def minute(self) -> str:
        """Date with hour and minute, eg: 2026-01-14T01-59"""
        return self._dt.format("YYYY-MM-DD[T]HH-mm")

    @property
    def second(self) -> str:
        """Date with hour, minute and second, eg: 2026-01-14T01-59-57"""
        return self._dt.format("YYYY-MM-DD[T]HH-mm-ss")

    def __str__(self) -> str:
        return self.date

    def __repr__(self) -> str:
        return f"'{self.date}'"


class FilesystemDeepView:
    """Deep (hierarchical) filesystem-safe date representations."""

    def __init__(self, dt: DateTime):
        self._dt = dt

    @property
    def year(self) -> str:
        """Eg: year=2026"""
        return self._dt.format("[year]=YYYY")

    @property
    def month(self) -> str:
        """Eg: year=2026/month=01"""
        return self._dt.format("[year]=YYYY/[month]=MM")

    @property
    def date(self) -> str:
        """Eg: year=2026/month=01/day=14"""
        return self._dt.format("[year]=YYYY/[month]=MM/[day]=DD")

    @property
    def day(self) -> str:
        """eg: year=2026/month=01/day=14"""
        return self._dt.format("[year]=YYYY/[month]=MM/[day]=DD")

    @property
    def hour(self) -> str:
        """
        eg: year=2026/month=01/day=14/hour=01
        """
        return self._dt.format("[year]=YYYY/[month]=MM/[day]=DD/[hour]=HH")

    @property
    def minute(self) -> str:
        """
        Eg: year=2026/month=01/day=14/hour=01/min=59
        """
        return self._dt.format("[year]=YYYY/[month]=MM/[day]=DD/[hour]=HH/[min]=mm")

    @property
    def second(self) -> str:
        """
        Eg: year=2026/month=01/day=14/hour=01/min=59/sec=57
        """
        return self._dt.format("[year]=YYYY/[month]=MM/[day]=DD/[hour]=HH/[min]=mm/[sec]=ss")

    def __str__(self) -> str:
        return self.date

    def __repr__(self) -> str:
        return f"'{self.date}'"
