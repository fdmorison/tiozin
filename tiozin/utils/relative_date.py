from __future__ import annotations

from pendulum import DateTime


class RelativeDate:
    """
    Represents a logical date relative to a base reference DateTime.

    All representations are exposed as attributes (properties),
    making it fully compatible with Jinja templates.

    Example usage (Jinja):
        {{ D[-1].iso8601 }}
        {{ D[0].fs.hms_nodash }}
        {{ D[-1].yesterday.date }}
    """

    def __init__(self, dt: DateTime):
        self._dt = dt

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
        """Pendulum DateTime object"""
        return self._dt

    @property
    def date(self) -> str:
        """YYYY-MM-DD"""
        return self._dt.to_date_string()

    # ==========================================================================
    # Web / ISO standards
    # ==========================================================================

    @property
    def iso(self) -> str:
        """ISO 8601 datetime"""
        return self._dt.to_iso8601_string()

    @property
    def iso8601(self) -> str:
        """ISO 8601 datetime"""
        return self._dt.to_iso8601_string()

    @property
    def rfc3339(self) -> str:
        """RFC 3339 datetime"""
        return self._dt.to_rfc3339_string()

    @property
    def w3c(self) -> str:
        """W3C datetime"""
        return self._dt.to_w3c_string()

    @property
    def sql_datetime(self) -> str:
        """W3C datetime"""
        return self._dt.to_datetime_string()

    # ==========================================================================
    # Unix timestamps
    # ==========================================================================

    @property
    def unix(self) -> int:
        """Unix timestamp (seconds)"""
        return self._dt.int_timestamp

    @property
    def unix_float(self) -> float:
        """Unix timestamp (seconds, float)"""
        return self._dt.float_timestamp

    # ==========================================================================
    # Filesystem formats
    # ==========================================================================

    @property
    def fs(self) -> FilesystemFlatView:
        """
        Filesystem-safe flat formats.

        Example:
            {{ D[-1].fs.hms_nodash }}
        """
        return FilesystemFlatView(self._dt)

    @property
    def fsdeep(self) -> FilesystemDeepView:
        """
        Filesystem-safe deep (hierarchical) paths.

        Example:
            {{ D[-1].fsdeep.hms }}
        """
        return FilesystemDeepView(self._dt)

    # ==========================================================================
    # Relative navigation (still returns RelativeDate)
    # ==========================================================================

    @property
    def today(self) -> RelativeDate:
        """D[n+0]"""
        return self

    @property
    def yesterday(self) -> RelativeDate:
        """D[n-1]"""
        return RelativeDate(self._dt.subtract(days=1))

    @property
    def tomorrow(self) -> RelativeDate:
        """D[n+1]"""
        return RelativeDate(self._dt.add(days=1))

    # ==========================================================================
    # Datetime parts (calendar, time, timezone)
    # ==========================================================================

    @property
    def YYYY(self) -> str:
        return self._dt.format("YYYY")  # 2026

    @property
    def MM(self) -> str:
        return self._dt.format("MM")  # 01

    @property
    def DD(self) -> str:
        return self._dt.format("DD")  # 14

    @property
    def DDD(self) -> str:
        return self._dt.format("DDD")  # 014 (day of year)

    @property
    def HH(self) -> str:
        return self._dt.format("HH")  # 01

    @property
    def mm(self) -> str:
        return self._dt.format("mm")  # 59

    @property
    def ss(self) -> str:
        return self._dt.format("ss")  # 57

    @property
    def time(self) -> str:
        return self._dt.to_time_string()  # 01:59:57

    @property
    def Z(self) -> str:
        return self._dt.format("Z")  # +00:00

    @property
    def ZZ(self) -> str:
        return self._dt.format("ZZ")  # +0000

    @property
    def z(self) -> str:
        return self._dt.format("z")  # UTC

    @property
    def zz(self) -> str:
        return self._dt.format("zz")  # UTC

    # ==========================================================================
    # Airflow standards
    # ==========================================================================
    @property
    def ds(self) -> str:
        """YYYY-MM-DD"""
        return self._dt.to_date_string()

    @property
    def ds_nodash(self) -> str:
        """YYYYMMDD"""
        return self._dt.format("YYYYMMDD")

    @property
    def ts(self) -> str:
        """YYYY-MM-DDTHH:MM:SS"""
        return self._dt.format("YYYY-MM-DD[T]HH:mm:ss")

    @property
    def ts_nodash(self) -> str:
        """YYYYMMDDTHHMMSS"""
        return self._dt.format("YYYYMMDD[T]HHmmss")

    @property
    def ts_nodash_with_tz(self) -> str:
        """YYYYMMDDTHHMMSSZZ"""
        return self._dt.format("YYYYMMDD[T]HHmmssZZ")

    @property
    def prev_ds(self) -> str:
        return self._dt.subtract(days=1).to_date_string()

    @property
    def prev_ds_nodash(self) -> str:
        return self._dt.subtract(days=1).format("YYYYMMDD")

    @property
    def next_ds(self) -> str:
        return self._dt.add(days=1).to_date_string()

    @property
    def next_ds_nodash(self) -> str:
        return self._dt.add(days=1).format("YYYYMMDD")

    @property
    def execution_date(self) -> DateTime:
        return self._dt

    @property
    def logical_date(self) -> DateTime:
        return self._dt

    @property
    def data_interval_start(self) -> DateTime:
        return self._dt

    @property
    def data_interval_end(self) -> DateTime:
        return self._dt.add(days=1)

    def to_dict(self) -> dict[str, object]:
        """
        Export all public @property attributes as a flat dict
        suitable for template rendering.
        """
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
    """
    Flat filesystem-safe date representations.
    """

    def __init__(self, dt: DateTime):
        self._dt = dt

    @property
    def date(self) -> str:
        """YYYY-MM-DD"""
        return self._dt.to_date_string()

    @property
    def day(self) -> str:
        """YYYY-MM-DD"""
        return self._dt.to_date_string()

    @property
    def nodash(self) -> str:
        """YYYYMMDD"""
        return self._dt.format("YYYYMMDD")

    @property
    def hour(self) -> str:
        """YYYY-MM-DDTHH"""
        return self._dt.format("YYYY-MM-DD[T]HH")

    @property
    def hour_nodash(self) -> str:
        """YYYYMMDDTHH"""
        return self._dt.format("YYYYMMDD[T]HH")

    @property
    def minute(self) -> str:
        """YYYY-MM-DDTHH-MM"""
        return self._dt.format("YYYY-MM-DD[T]HH-mm")

    @property
    def minute_nodash(self) -> str:
        """YYYYMMDDTHHMM"""
        return self._dt.format("YYYYMMDD[T]HHmm")

    @property
    def second(self) -> str:
        """YYYY-MM-DDTHH-MM-SS"""
        return self._dt.format("YYYY-MM-DD[T]HH-mm-ss")

    @property
    def second_nodash(self) -> str:
        """YYYYMMDDTHHMMSS"""
        return self._dt.format("YYYYMMDD[T]HHmmss")

    def __str__(self) -> str:
        return self.date

    def __repr__(self) -> str:
        return f"'{self.date}'"


class FilesystemDeepView:
    """
    Deep (hierarchical) filesystem-safe date representations.
    """

    def __init__(self, dt: DateTime):
        self._dt = dt

    @property
    def year(self) -> str:
        return self._dt.format("[year]=YYYY")

    @property
    def month(self) -> str:
        return self._dt.format("[year]=YYYY/[month]=MM")

    @property
    def date(self) -> str:
        return self._dt.format("[year]=YYYY/[month]=MM/[day]=DD")

    @property
    def day(self) -> str:
        return self._dt.format("[year]=YYYY/[month]=MM/[day]=DD")

    @property
    def hour(self) -> str:
        return self._dt.format("[year]=YYYY/[month]=MM/[day]=DD/[hour]=HH")

    @property
    def minute(self) -> str:
        return self._dt.format("[year]=YYYY/[month]=MM/[day]=DD/[hour]=HH/[min]=mm")

    @property
    def second(self) -> str:
        return self._dt.format("[year]=YYYY/[month]=MM/[day]=DD/[hour]=HH/[min]=mm/[sec]=ss")

    def __str__(self) -> str:
        return self.date

    def __repr__(self) -> str:
        return f"'{self.date}'"
