from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

import pendulum
from pendulum import DateTime


class TemplateDate:
    """
    Logical date object for expressive data templating.

    TemplateDate provides a fluent, template-friendly interface for navigating and formatting
    logical dates in data workflows. It is designed to maximize developer experience (DX) in
    templating environments such as Jinja, allowing complex date manipulations to be expressed
    declaratively and readably.

    The API favors composability and ergonomics over low-level datetime manipulation, enabling
    common data patterns with minimal syntax. Key capabilities:

    - Relative navigation via index syntax (e.g. ``D[-1]``)
    - Multiple prebuilt string representations
    - Filesystem- and Airflow-friendly formats
    - Fully chainable transformations

    Example (Jinja):

        {{ D }}
        {{ D[-1].iso }}
        {{ D[0].flat_hour }}
        {{ D[-1].yesterday.deep_date }}
        {{ D[-1].deep_date.yesterday }}
        {{ D[-1].flat_date.tomorrow  }}
        {{ D[+1].flat_date           }}

    Note:
        TemplateDate is a logical date helper for data templating, not a
        general-purpose datetime replacement.
    """

    __slots__ = ("_dt", "_fmt")

    def __init__(self, dt: DateTime = None, fmt: Callable[[DateTime], str] = None):
        self._dt = dt or pendulum.now("UTC")
        self._fmt = fmt

    def _navigate(self, dt: DateTime) -> TemplateDate:
        """Navigate to a new datetime preserving the current fmt."""
        return TemplateDate(dt, self._fmt)

    def _at_hour(self, hour: int) -> TemplateDate:
        """Navigate to a specific hour on this day, preserving fmt if already set."""
        new_dt = self._dt.start_of("day").add(hours=hour)
        return TemplateDate(
            new_dt,
            self._fmt or (lambda dt: dt.format("YYYY-MM-DD[T]HH:mm:ssZ")),
        )

    @staticmethod
    def coerce(value: TemplateDate | DateTime | datetime | str) -> TemplateDate | None:
        """
        Coerce a supported value into a ``TemplateDate`` instance.

        Accepted inputs:

        - ``TemplateDate``: returned as-is
        - ``pendulum.DateTime``: wrapped in ``TemplateDate``
        - ``datetime.datetime``: converted via ``pendulum.instance`` and wrapped
        - ISO-8601 string: parsed via ``pendulum.parse`` and wrapped
        - ``None``: returns ``None``

        Raises:
            TypeError: If the value cannot be converted to a datetime.
        """
        if value is None:
            return None

        if isinstance(value, TemplateDate):
            return value

        if isinstance(value, pendulum.DateTime):
            return TemplateDate(value)

        if isinstance(value, datetime):
            return TemplateDate(pendulum.instance(value))

        if isinstance(value, str):
            return TemplateDate(pendulum.parse(value))

        raise TypeError(
            "Expected TemplateDate, pendulum.DateTime, datetime or ISO string, "
            f"got {type(value).__name__}: {value!r}"
        )

    def __getitem__(self, offset: int) -> TemplateDate:
        """
        Allows relative navigation using index syntax.

        Examples:
            D[0]    → today
            D[-1]   → yesterday
            D[7]    → 7 days ahead
        """
        if not isinstance(offset, int):
            raise TypeError("TemplateDate offset must be an integer")

        return self._navigate(self._dt.add(days=offset))

    def __str__(self) -> str:
        """
        String representation uses fmt to determine the format.

        If fmt is None, returns the date string (YYYY-MM-DD).
        If fmt is a callable, calls it with the underlying DateTime.

        fmt propagates through navigation (yesterday, tomorrow, [offset]),
        so D[0].at08.yesterday also renders as ISO.
        """
        if self._fmt is None:
            return self._dt.to_date_string()
        return self._fmt(self._dt)

    def __repr__(self) -> str:
        return f"TemplateDate({self._dt.isoformat()})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TemplateDate):
            return False
        return self._dt == other._dt and self._fmt == other._fmt

    # ==========================================================================
    # Core
    # ==========================================================================

    @property
    def dt(self) -> DateTime:
        """Pendulum DateTime object."""
        return self._dt

    @property
    def date(self) -> TemplateDate:
        """Date string, eg: 2026-01-14"""
        return TemplateDate(self._dt, lambda dt: dt.to_date_string())

    # ==========================================================================
    # Unix timestamps
    # ==========================================================================

    @property
    def unix(self) -> TemplateDate:
        """Unix timestamp (int seconds), eg: 1768370397"""
        return TemplateDate(self._dt, lambda dt: str(dt.int_timestamp))

    @property
    def unix_float(self) -> TemplateDate:
        """Unix timestamp (float seconds), eg: 1768370397.0"""
        return TemplateDate(self._dt, lambda dt: str(dt.float_timestamp))

    # ==========================================================================
    # Web / ISO standards
    # ==========================================================================

    @property
    def iso(self) -> TemplateDate:
        """ISO 8601 datetime (seconds precision), eg: 2026-01-14T01:59:57+00:00"""
        return TemplateDate(self._dt, lambda dt: dt.format("YYYY-MM-DD[T]HH:mm:ssZ"))

    @property
    def iso_ms(self) -> TemplateDate:
        """ISO 8601 datetime with milliseconds, eg: 2026-01-14T01:59:57.123+00:00"""
        return TemplateDate(
            self._dt,
            lambda dt: dt.format("YYYY-MM-DD[T]HH:mm:ss.SSSZ"),
        )

    @property
    def iso_micro(self) -> TemplateDate:
        """ISO 8601 datetime with microseconds, eg: 2026-01-14T01:59:57.123456+00:00"""

        def _fmt(dt: DateTime) -> str:
            base = dt.format("YYYY-MM-DD[T]HH:mm:ss")
            return f"{base}.{dt.microsecond:06d}{dt.format('Z')}"

        return TemplateDate(self._dt, _fmt)

    @property
    def sql_datetime(self) -> TemplateDate:
        """SQL datetime, eg: 2026-01-14 01:59:57"""
        return TemplateDate(self._dt, lambda dt: dt.to_datetime_string())

    # ==========================================================================
    # Airflow standards
    # ==========================================================================

    @property
    def ds(self) -> TemplateDate:
        """Airflow ds format, eg: 2026-01-14"""
        return TemplateDate(self._dt, lambda dt: dt.to_date_string())

    @property
    def ts(self) -> TemplateDate:
        """Airflow ts format — ISO 8601 with timezone, eg: 2026-01-14T01:59:57+00:00"""
        return TemplateDate(self._dt, lambda dt: dt.format("YYYY-MM-DD[T]HH:mm:ssZ"))

    @property
    def ts_naive(self) -> TemplateDate:
        """ISO 8601 datetime without timezone (naive), eg: 2026-01-14T01:59:57"""
        return TemplateDate(self._dt, lambda dt: dt.format("YYYY-MM-DD[T]HH:mm:ss"))

    @property
    def prev_ds(self) -> TemplateDate:
        """Previous day ds, eg: 2026-01-13"""
        return TemplateDate(self._dt.subtract(days=1), lambda dt: dt.to_date_string())

    @property
    def next_ds(self) -> TemplateDate:
        """Next day ds, eg: 2026-01-15"""
        return TemplateDate(self._dt.add(days=1), lambda dt: dt.to_date_string())

    @property
    def execution_date(self) -> TemplateDate:
        """Airflow execution_date — ISO 8601 datetime, eg: 2026-01-14T01:59:57+00:00"""
        return TemplateDate(self._dt, lambda dt: dt.format("YYYY-MM-DD[T]HH:mm:ssZ"))

    @property
    def logical_date(self) -> TemplateDate:
        """Airflow logical_date — ISO 8601 datetime, eg: 2026-01-14T01:59:57+00:00"""
        return TemplateDate(self._dt, lambda dt: dt.format("YYYY-MM-DD[T]HH:mm:ssZ"))

    @property
    def data_interval_start(self) -> TemplateDate:
        """Airflow data_interval_start — ISO 8601 datetime, eg: 2026-01-14T01:59:57+00:00"""
        return TemplateDate(self._dt, lambda dt: dt.format("YYYY-MM-DD[T]HH:mm:ssZ"))

    @property
    def data_interval_end(self) -> TemplateDate:
        """Airflow data_interval_end — next day ISO 8601 datetime, eg: 2026-01-15T01:59:57+00:00"""
        return TemplateDate(self._dt.add(days=1), lambda dt: dt.format("YYYY-MM-DD[T]HH:mm:ssZ"))

    # ==========================================================================
    # Filesystem formats (flat and deep)
    # ==========================================================================

    @property
    def flat_year(self) -> TemplateDate:
        """Year, eg: 2026"""
        return TemplateDate(self._dt, lambda dt: dt.format("YYYY"))

    @property
    def flat_month(self) -> TemplateDate:
        """Year and month, eg: 2026-01"""
        return TemplateDate(self._dt, lambda dt: dt.format("YYYY-MM"))

    @property
    def flat_date(self) -> TemplateDate:
        """Date, eg: 2026-01-14"""
        return TemplateDate(self._dt, lambda dt: dt.to_date_string())

    @property
    def flat_day(self) -> TemplateDate:
        """Date (alias for flat_date), eg: 2026-01-14"""
        return TemplateDate(self._dt, lambda dt: dt.to_date_string())

    @property
    def flat_hour(self) -> TemplateDate:
        """Date with hour, eg: 2026-01-14T01"""
        return TemplateDate(self._dt, lambda dt: dt.format("YYYY-MM-DD[T]HH"))

    @property
    def flat_minute(self) -> TemplateDate:
        """Date with hour and minute, eg: 2026-01-14T01-59"""
        return TemplateDate(self._dt, lambda dt: dt.format("YYYY-MM-DD[T]HH-mm"))

    @property
    def flat_second(self) -> TemplateDate:
        """Date with hour, minute and second, eg: 2026-01-14T01-59-57"""
        return TemplateDate(self._dt, lambda dt: dt.format("YYYY-MM-DD[T]HH-mm-ss"))

    @property
    def flat_ts(self) -> TemplateDate:
        """Full timestamp (alias for flat_second), eg: 2026-01-14T01-59-57"""
        return self.flat_second

    @property
    def deep_year(self) -> TemplateDate:
        """Eg: year=2026"""
        return TemplateDate(self._dt, lambda dt: dt.format("[year]=YYYY"))

    @property
    def deep_month(self) -> TemplateDate:
        """Eg: year=2026/month=01"""
        return TemplateDate(self._dt, lambda dt: dt.format("[year]=YYYY/[month]=MM"))

    @property
    def deep_date(self) -> TemplateDate:
        """Eg: year=2026/month=01/day=14"""
        return TemplateDate(self._dt, lambda dt: dt.format("[year]=YYYY/[month]=MM/[day]=DD"))

    @property
    def deep_day(self) -> TemplateDate:
        """Eg: year=2026/month=01/day=14"""
        return TemplateDate(self._dt, lambda dt: dt.format("[year]=YYYY/[month]=MM/[day]=DD"))

    @property
    def deep_hour(self) -> TemplateDate:
        """Eg: year=2026/month=01/day=14/hour=01"""
        return TemplateDate(
            self._dt, lambda dt: dt.format("[year]=YYYY/[month]=MM/[day]=DD/[hour]=HH")
        )

    @property
    def deep_minute(self) -> TemplateDate:
        """Eg: year=2026/month=01/day=14/hour=01/min=59"""
        return TemplateDate(
            self._dt, lambda dt: dt.format("[year]=YYYY/[month]=MM/[day]=DD/[hour]=HH/[min]=mm")
        )

    @property
    def deep_second(self) -> TemplateDate:
        """Eg: year=2026/month=01/day=14/hour=01/min=59/sec=57"""
        return TemplateDate(
            self._dt,
            lambda dt: dt.format("[year]=YYYY/[month]=MM/[day]=DD/[hour]=HH/[min]=mm/[sec]=ss"),
        )

    @property
    def deep_ts(self) -> TemplateDate:
        """
        Full timestamp path (alias for deep_second),
        eg: year=2026/month=01/day=14/hour=01/min=59/sec=57
        """
        return self.deep_second

    # ==========================================================================
    # Relative navigation (still returns TemplateDate)
    # ==========================================================================

    @property
    def today(self) -> TemplateDate:
        """Same day, eg: D[n].today == D[n]"""
        return self

    @property
    def yesterday(self) -> TemplateDate:
        """Previous day, eg: D[n].yesterday == D[n-1]"""
        return self._navigate(self._dt.subtract(days=1))

    @property
    def tomorrow(self) -> TemplateDate:
        """Next day, eg: D[n].tomorrow == D[n+1]"""
        return self._navigate(self._dt.add(days=1))

    @property
    def start_of_year(self) -> TemplateDate:
        """Start of the year (Jan 1 00:00:00), eg: D[0].start_of_year.flat_date"""
        return self._navigate(self._dt.start_of("year"))

    @property
    def start_of_month(self) -> TemplateDate:
        """Start of the month (1st 00:00:00), eg: D[0].start_of_month.flat_date"""
        return self._navigate(self._dt.start_of("month"))

    @property
    def start_of_day(self) -> TemplateDate:
        """Start of the day (midnight), eg: D[0].start_of_day.flat_date"""
        return self._navigate(self._dt.start_of("day"))

    @property
    def midnight(self) -> TemplateDate:
        """This day at 00:00:00, eg: {{ D[0].midnight }} → 2026-01-17T00:00:00+00:00"""
        return self._at_hour(0)

    @property
    def noon(self) -> TemplateDate:
        """This day at 12:00:00, eg: {{ D[0].noon }} → 2026-01-17T12:00:00+00:00"""
        return self._at_hour(12)

    @property
    def start_of_week(self) -> TemplateDate:
        """Start of the week (Monday 00:00:00), eg: D[0].start_of_week.flat_date"""
        return self._navigate(self._dt.start_of("week"))

    @property
    def start_of_hour(self) -> TemplateDate:
        """Start of the current hour, eg: D[0].start_of_hour.flat_hour"""
        return self._navigate(self._dt.start_of("hour"))

    @property
    def start_of_minute(self) -> TemplateDate:
        """Start of the current minute, eg: D[0].start_of_minute.flat_minute"""
        return self._navigate(self._dt.start_of("minute"))

    @property
    def at00(self) -> TemplateDate:
        """This day at 00:00:00, eg: D[0].at00 → 2026-01-14T00:00:00+00:00"""
        return self._at_hour(0)

    @property
    def at01(self) -> TemplateDate:
        """This day at 01:00:00, eg: D[0].at01 → 2026-01-14T01:00:00+00:00"""
        return self._at_hour(1)

    @property
    def at02(self) -> TemplateDate:
        """This day at 02:00:00, eg: D[0].at02 → 2026-01-14T02:00:00+00:00"""
        return self._at_hour(2)

    @property
    def at03(self) -> TemplateDate:
        """This day at 03:00:00, eg: D[0].at03 → 2026-01-14T03:00:00+00:00"""
        return self._at_hour(3)

    @property
    def at04(self) -> TemplateDate:
        """This day at 04:00:00, eg: D[0].at04 → 2026-01-14T04:00:00+00:00"""
        return self._at_hour(4)

    @property
    def at05(self) -> TemplateDate:
        """This day at 05:00:00, eg: D[0].at05 → 2026-01-14T05:00:00+00:00"""
        return self._at_hour(5)

    @property
    def at06(self) -> TemplateDate:
        """This day at 06:00:00, eg: D[0].at06 → 2026-01-14T06:00:00+00:00"""
        return self._at_hour(6)

    @property
    def at07(self) -> TemplateDate:
        """This day at 07:00:00, eg: D[0].at07 → 2026-01-14T07:00:00+00:00"""
        return self._at_hour(7)

    @property
    def at08(self) -> TemplateDate:
        """This day at 08:00:00, eg: D[0].at08 → 2026-01-14T08:00:00+00:00"""
        return self._at_hour(8)

    @property
    def at09(self) -> TemplateDate:
        """This day at 09:00:00, eg: D[0].at09 → 2026-01-14T09:00:00+00:00"""
        return self._at_hour(9)

    @property
    def at10(self) -> TemplateDate:
        """This day at 10:00:00, eg: D[0].at10 → 2026-01-14T10:00:00+00:00"""
        return self._at_hour(10)

    @property
    def at11(self) -> TemplateDate:
        """This day at 11:00:00, eg: D[0].at11 → 2026-01-14T11:00:00+00:00"""
        return self._at_hour(11)

    @property
    def at12(self) -> TemplateDate:
        """This day at 12:00:00 (alias for noon), eg: D[0].at12 → 2026-01-14T12:00:00+00:00"""
        return self._at_hour(12)

    @property
    def at13(self) -> TemplateDate:
        """This day at 13:00:00, eg: D[0].at13 → 2026-01-14T13:00:00+00:00"""
        return self._at_hour(13)

    @property
    def at14(self) -> TemplateDate:
        """This day at 14:00:00, eg: D[0].at14 → 2026-01-14T14:00:00+00:00"""
        return self._at_hour(14)

    @property
    def at15(self) -> TemplateDate:
        """This day at 15:00:00, eg: D[0].at15 → 2026-01-14T15:00:00+00:00"""
        return self._at_hour(15)

    @property
    def at16(self) -> TemplateDate:
        """This day at 16:00:00, eg: D[0].at16 → 2026-01-14T16:00:00+00:00"""
        return self._at_hour(16)

    @property
    def at17(self) -> TemplateDate:
        """This day at 17:00:00, eg: D[0].at17 → 2026-01-14T17:00:00+00:00"""
        return self._at_hour(17)

    @property
    def at18(self) -> TemplateDate:
        """This day at 18:00:00, eg: D[0].at18 → 2026-01-14T18:00:00+00:00"""
        return self._at_hour(18)

    @property
    def at19(self) -> TemplateDate:
        """This day at 19:00:00, eg: D[0].at19 → 2026-01-14T19:00:00+00:00"""
        return self._at_hour(19)

    @property
    def at20(self) -> TemplateDate:
        """This day at 20:00:00, eg: D[0].at20 → 2026-01-14T20:00:00+00:00"""
        return self._at_hour(20)

    @property
    def at21(self) -> TemplateDate:
        """This day at 21:00:00, eg: D[0].at21 → 2026-01-14T21:00:00+00:00"""
        return self._at_hour(21)

    @property
    def at22(self) -> TemplateDate:
        """This day at 22:00:00, eg: D[0].at22 → 2026-01-14T22:00:00+00:00"""
        return self._at_hour(22)

    @property
    def at23(self) -> TemplateDate:
        """This day at 23:00:00, eg: D[0].at23 → 2026-01-14T23:00:00+00:00"""
        return self._at_hour(23)

    # ==========================================================================
    # Datetime parts (calendar, time, timezone)
    # ==========================================================================

    @property
    def YYYY(self) -> TemplateDate:
        """Year (4 digits), eg: 2026"""
        return TemplateDate(self._dt, lambda dt: dt.format("YYYY"))

    @property
    def MM(self) -> TemplateDate:
        """Month (2 digits), eg: 01"""
        return TemplateDate(self._dt, lambda dt: dt.format("MM"))

    @property
    def DD(self) -> TemplateDate:
        """Day of month (2 digits), eg: 14"""
        return TemplateDate(self._dt, lambda dt: dt.format("DD"))

    @property
    def DDD(self) -> TemplateDate:
        """Day of year, zero-padded to 3 digits, eg: 084"""
        return TemplateDate(self._dt, lambda dt: f"{dt.day_of_year:03d}")

    @property
    def HH(self) -> TemplateDate:
        """Hour (2 digits, 24h), eg: 01"""
        return TemplateDate(self._dt, lambda dt: dt.format("HH"))

    @property
    def mm(self) -> TemplateDate:
        """Minute (2 digits), eg: 59"""
        return TemplateDate(self._dt, lambda dt: dt.format("mm"))

    @property
    def ss(self) -> TemplateDate:
        """Second (2 digits), eg: 57"""
        return TemplateDate(self._dt, lambda dt: dt.format("ss"))

    @property
    def time(self) -> TemplateDate:
        """Time string, eg: 01:59:57"""
        return TemplateDate(self._dt, lambda dt: dt.to_time_string())

    @property
    def Z(self) -> TemplateDate:
        """Timezone offset with colon, eg: +00:00"""
        return TemplateDate(self._dt, lambda dt: dt.format("Z"))

    @property
    def ZZ(self) -> TemplateDate:
        """Timezone offset without colon, eg: +0000"""
        return TemplateDate(self._dt, lambda dt: dt.format("ZZ"))

    @property
    def z(self) -> TemplateDate:
        """Timezone name or fixed offset, eg: UTC (named) or +00:00 (fixed offset)"""
        return TemplateDate(self._dt, lambda dt: dt.format("z"))

    @property
    def zz(self) -> TemplateDate:
        """Timezone name or fixed offset (alias for z), eg: UTC (named) or +00:00 (fixed offset)"""
        return TemplateDate(self._dt, lambda dt: dt.format("zz"))

    def to_dict(self) -> dict[str, object]:
        """Export all public @property attributes as a flat dict."""
        dyct = {}

        for name, attr in type(self).__dict__.items():
            if not isinstance(attr, property):
                continue
            dyct[name] = getattr(self, name)

        return dyct
