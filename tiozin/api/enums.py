from __future__ import annotations

from datetime import datetime
from enum import StrEnum, auto
from typing import Self


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
    Granularity at which a recurring datetime (e.g. a job's nominal time) advances.

    Ordered from finest to coarsest. `truncate` zeroes out everything below
    the given granularity.
    """

    MINUTE = auto()
    HOUR = auto()
    DAY = auto()
    MONTH = auto()

    def truncate(self, value: datetime) -> datetime:
        """
        Truncate a datetime down to the start of this cadence's slot.

        Args:
            value: The datetime to truncate.

        Examples:
            >>> Cadence.MINUTE.truncate(datetime(2024, 3, 15, 10, 30, 45, tzinfo=UTC))
            datetime(2024, 3, 15, 10, 30, tzinfo=UTC)
            >>> Cadence.MONTH.truncate(datetime(2024, 3, 15, 10, 30, 45, tzinfo=UTC))
            datetime(2024, 3, 1, 0, 0, tzinfo=UTC)
        """
        fields = {
            self.MINUTE: {"second": 0, "microsecond": 0},
            self.HOUR: {"minute": 0, "second": 0, "microsecond": 0},
            self.DAY: {"hour": 0, "minute": 0, "second": 0, "microsecond": 0},
            self.MONTH: {"day": 1, "hour": 0, "minute": 0, "second": 0, "microsecond": 0},
        }
        return value.replace(**fields[self])

    def truncate_iso(self, value: datetime) -> str:
        """
        Truncate a datetime down to the start of this cadence's slot and format it
        as an ISO 8601 string, using `Z` instead of `+00:00` for UTC.

        Args:
            value: The datetime to truncate.

        Examples:
            >>> Cadence.MINUTE.truncate_iso(datetime(2024, 3, 15, 10, 30, 45, tzinfo=UTC))
            '2024-03-15T10:30:00Z'
        """
        return self.truncate(value).isoformat().replace("+00:00", "Z")
