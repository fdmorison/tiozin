from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self

import pendulum

from tiozin.utils import default


class UpperEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name: str, *_) -> str:
        return name.upper()

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value

    @classmethod
    def _missing_(cls, value: str) -> Self:
        if isinstance(value, str):
            normalized = value.strip().upper()
            member = cls._value2member_map_.get(normalized)
            if member is not None:
                return member
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")


class LowerEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name: str, *_) -> str:
        return name.lower()

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value

    @classmethod
    def _missing_(cls, value: str) -> Self:
        if isinstance(value, str):
            normalized = value.strip().lower()
            member = cls._value2member_map_.get(normalized)
            if member is not None:
                return member
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")


class Cadence(LowerEnum):
    """
    Frequency at which a job runs, ordered from finest to coarsest.

    Each cadence carries the calendar unit its slots are measured in and
    provides slot arithmetic on top of it: truncation, advancement, and the
    interval a slot covers.
    """

    unit: str

    MINUTELY = "minutely", "minute"
    HOURLY = "hourly", "hour"
    DAILY = "daily", "day"
    WEEKLY = "weekly", "week"
    MONTHLY = "monthly", "month"

    def __new__(cls, value: str, unit: str) -> Self:
        member = str.__new__(cls, value)
        member._value_ = value
        member.unit = unit
        return member

    @property
    def step(self) -> dict[str, int]:
        """
        The advance of one slot expressed as datetime keyword arguments, ready
        to be splatted into arithmetic like ``dt.add(**cadence.step)``.

        Examples:
            >>> Cadence.MINUTELY.step
            {'minutes': 1}
            >>> Cadence.DAILY.step
            {'days': 1}
        """
        return {f"{self.unit}s": 1}

    @property
    def duration(self) -> pendulum.Duration:
        """
        The length of one slot of this cadence, as a ``pendulum.Duration``
        ready for datetime arithmetic and unit conversions.

        Examples:
            >>> Cadence.MINUTELY.duration
            Duration(minutes=1)
            >>> Cadence.DAILY.duration.in_hours()
            24
            >>> nominal_time + Cadence.HOURLY.duration
            DateTime(2024, 3, 15, 11, 30, 0, tzinfo=Timezone('UTC'))
        """
        return pendulum.Duration(**self.step)

    def truncate(self, value: datetime) -> pendulum.DateTime:
        """
        Truncate a datetime down to the start of its slot in this cadence.

        Args:
            value: The datetime to truncate.

        Examples:
            >>> Cadence.MINUTELY.truncate(datetime(2024, 3, 15, 10, 30, 45, tzinfo=UTC))
            datetime(2024, 3, 15, 10, 30, tzinfo=UTC)
            >>> Cadence.MONTHLY.truncate(datetime(2024, 3, 15, 10, 30, 45, tzinfo=UTC))
            datetime(2024, 3, 1, 0, 0, tzinfo=UTC)
        """
        return pendulum.instance(value).start_of(self.unit)

    def next(self, value: datetime) -> pendulum.DateTime:
        """
        Return the start of the slot that follows the one containing the datetime.

        Examples:
            >>> Cadence.DAILY.next(datetime(2024, 3, 15, 10, 30, tzinfo=UTC))
            datetime(2024, 3, 16, 0, 0, tzinfo=UTC)
        """
        return self.truncate(value).add(**self.step)

    def previous(self, value: datetime) -> pendulum.DateTime:
        """
        Return the start of the slot that precedes the one containing the datetime.

        Examples:
            >>> Cadence.DAILY.previous(datetime(2024, 3, 15, 10, 30, tzinfo=UTC))
            datetime(2024, 3, 14, 0, 0, tzinfo=UTC)
        """
        return self.truncate(value).subtract(**self.step)

    def interval(
        self, value: datetime, is_start: bool = None
    ) -> tuple[pendulum.DateTime, pendulum.DateTime]:
        """
        Return the [start, end) interval of one slot anchored at the datetime's slot.

        By default the datetime marks the end of the interval, which is the
        convention for nominal times. Pass ``is_start=True`` when it marks
        the beginning instead.

        Examples:
            >>> Cadence.DAILY.interval(datetime(2024, 3, 15, 10, 30, tzinfo=UTC))
            (datetime(2024, 3, 14, 0, 0, tzinfo=UTC), datetime(2024, 3, 15, 0, 0, tzinfo=UTC))
            >>> Cadence.DAILY.interval(datetime(2024, 3, 15, 10, 30, tzinfo=UTC), is_start=True)
            (datetime(2024, 3, 15, 0, 0, tzinfo=UTC), datetime(2024, 3, 16, 0, 0, tzinfo=UTC))
        """
        is_start = default(is_start, False)
        if is_start:
            return self.truncate(value), self.next(value)
        return self.previous(value), self.truncate(value)

    def is_nominal(self, value: datetime) -> bool:
        """
        Whether the datetime is a valid nominal time for this cadence, i.e.
        sits exactly on a slot boundary.

        Examples:
            >>> Cadence.HOURLY.is_nominal(datetime(2024, 3, 15, 10, 0, tzinfo=UTC))
            True
            >>> Cadence.HOURLY.is_nominal(datetime(2024, 3, 15, 10, 30, tzinfo=UTC))
            False
        """
        return pendulum.instance(value) == self.truncate(value)
