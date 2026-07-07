from __future__ import annotations

import re
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, TypeAlias

from tiozin import config

if TYPE_CHECKING:
    from ...types import Watermark

_WATERMARK_INT_MAX = 10**config.batch_watermark_int_digits
_WATERMARK_INT_RE = re.compile(rf"^\d{{{config.batch_watermark_int_digits}}}$")
_WATERMARK_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_WATERMARK_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00$")

RawWatermark: TypeAlias = str


def parse_watermark(value: RawWatermark | Watermark | None) -> Watermark | None:
    if isinstance(value, str):
        if _WATERMARK_INT_RE.fullmatch(value):
            return int(value)
        if _WATERMARK_DATE_RE.fullmatch(value):
            return date.fromisoformat(value)
        if _WATERMARK_TIMESTAMP_RE.fullmatch(value):
            return datetime.fromisoformat(value)
        raise ValueError(f"invalid watermark format: {value!r}")
    return value


def check_watermark(value: Watermark | None) -> Watermark | None:
    match value:
        case bool():
            raise ValueError("watermark cannot be bool")
        case int() if not 0 <= value < _WATERMARK_INT_MAX:
            raise ValueError(
                f"watermark int must fit in {config.batch_watermark_int_digits} digits"
            )
        case datetime():
            return value.astimezone(UTC)
    return value


def serialize_watermark(value: Watermark | None) -> RawWatermark | None:
    match value:
        case None:
            return None
        case int():
            return f"{value:0{config.batch_watermark_int_digits}d}"
        case datetime():
            return value.isoformat(timespec="microseconds")
        case date():
            return value.isoformat()
