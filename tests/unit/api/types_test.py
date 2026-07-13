import warnings
from datetime import UTC, date, datetime, timedelta, timezone

import pendulum
import pytest
from pydantic import TypeAdapter, ValidationError

from tiozin.api.types import NominalTime, TechnicalTime, Watermark

# The TechnicalTime pipeline carries an inert Field(default_factory=utcnow) that
# emits UnsupportedFieldAttributeWarning when a TypeAdapter builds its schema. It
# has no effect on validation, so the adapters are built with the warning silenced.
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    TECHNICAL_TIME = TypeAdapter(TechnicalTime)
    NOMINAL_TIME = TypeAdapter(NominalTime)

WATERMARK = TypeAdapter(Watermark)


# =============================================================================
# TechnicalTime — an aware datetime normalized to UTC, keeping the full instant
# =============================================================================


@pytest.mark.parametrize(
    "value",
    [
        datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone(timedelta(hours=-3))),
        pendulum.datetime(2026, 1, 15, 9, 0, 0, tz="America/Sao_Paulo"),
    ],
)
def test_technical_time_should_normalize_aware_datetime_to_utc(value):
    # Act
    result = TECHNICAL_TIME.validate_python(value)

    # Assert
    actual = result
    expected = pendulum.datetime(2026, 1, 15, 12, 0, 0, tz="UTC")
    assert actual == expected


def test_technical_time_should_return_pendulum_datetime():
    # Arrange
    value = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)

    # Act
    result = TECHNICAL_TIME.validate_python(value)

    # Assert
    assert isinstance(result, pendulum.DateTime)


def test_technical_time_should_preserve_seconds_and_microseconds():
    # Arrange
    value = datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)

    # Act
    result = TECHNICAL_TIME.validate_python(value)

    # Assert
    actual = result
    expected = pendulum.datetime(2026, 1, 15, 10, 30, 45, 123456, tz="UTC")
    assert actual == expected


def test_technical_time_should_raise_validation_error_when_datetime_is_naive():
    # Arrange
    value = datetime(2026, 1, 15, 12, 0, 0)

    # Act / Assert
    with pytest.raises(ValidationError):
        TECHNICAL_TIME.validate_python(value)


# =============================================================================
# NominalTime — a TechnicalTime truncated down to minute precision
# =============================================================================


def test_nominal_time_should_truncate_to_minute():
    # Arrange
    value = datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)

    # Act
    result = NOMINAL_TIME.validate_python(value)

    # Assert
    actual = result
    expected = pendulum.datetime(2026, 1, 15, 10, 30, 0, tz="UTC")
    assert actual == expected


def test_nominal_time_should_convert_to_utc_before_truncating():
    # Arrange
    value = datetime(2026, 1, 15, 10, 15, 45, tzinfo=timezone(timedelta(hours=5, minutes=30)))

    # Act
    result = NOMINAL_TIME.validate_python(value)

    # Assert
    actual = result
    expected = pendulum.datetime(2026, 1, 15, 4, 45, 0, tz="UTC")
    assert actual == expected


def test_nominal_time_should_return_pendulum_datetime():
    # Arrange
    value = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)

    # Act
    result = NOMINAL_TIME.validate_python(value)

    # Assert
    assert isinstance(result, pendulum.DateTime)


def test_nominal_time_should_raise_validation_error_when_datetime_is_naive():
    # Arrange
    value = datetime(2026, 1, 15, 12, 30, 0)

    # Act / Assert
    with pytest.raises(ValidationError):
        NOMINAL_TIME.validate_python(value)


# =============================================================================
# Watermark — int, date, or datetime passed through the parse/check pipeline
# =============================================================================


@pytest.mark.parametrize(
    "value, expected",
    [
        (42, 42),
        (date(2026, 1, 15), date(2026, 1, 15)),
    ],
)
def test_watermark_should_accept_value(value, expected):
    # Act
    result = WATERMARK.validate_python(value)

    # Assert
    actual = result
    assert actual == expected


def test_watermark_should_normalize_datetime_to_utc():
    # Arrange
    value = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))

    # Act
    result = WATERMARK.validate_python(value)

    # Assert
    actual = result
    expected = datetime(2026, 1, 15, 9, 0, 0, tzinfo=UTC)
    assert actual == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("00000000000000000042", 42),
        ("2026-01-15", date(2026, 1, 15)),
        ("2026-01-15T10:30:45.123456+00:00", datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)),
    ],
)
def test_watermark_should_parse_canonical_string(value, expected):
    # Act
    result = WATERMARK.validate_python(value)

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    ["not-a-watermark", "42", -1, 10**20],
)
def test_watermark_should_raise_validation_error_when_value_is_invalid(value):
    # Act / Assert
    with pytest.raises(ValidationError):
        WATERMARK.validate_python(value)
