from datetime import UTC, date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from tiozin.api.metadata.batch.state import BatchState


# ============================================================================
# defaults
# ============================================================================
def test_state_should_default_all_fields_to_none():
    # Arrange / Act
    result = BatchState()

    # Assert
    actual = (result.start, result.end, result.watermark)
    expected = (None, None, None)
    assert actual == expected


# ============================================================================
# start / end normalization
# ============================================================================
def test_state_should_normalize_start_and_end_to_utc():
    # Arrange
    other_tz = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))

    # Act
    result = BatchState(start=other_tz, end=other_tz)

    # Assert
    actual = (result.start, result.end)
    expected = (
        datetime(2026, 1, 15, 9, 0, 0, tzinfo=UTC),
        datetime(2026, 1, 15, 9, 0, 0, tzinfo=UTC),
    )
    assert actual == expected


def test_state_should_normalize_end_to_utc_on_assignment():
    # Arrange
    state = BatchState()

    # Act
    state.end = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))

    # Assert
    actual = state.end
    expected = datetime(2026, 1, 15, 9, 0, 0, tzinfo=UTC)
    assert actual == expected


# ============================================================================
# watermark - typed round-trip
# ============================================================================
def test_state_should_read_int_watermark_back_as_int():
    # Arrange
    state = BatchState(watermark=42)

    # Act
    result = state.watermark

    # Assert
    actual = (result, type(result))
    expected = (42, int)
    assert actual == expected


def test_state_should_read_date_watermark_back_as_date():
    # Arrange
    state = BatchState(watermark=date(2026, 1, 15))

    # Act
    result = state.watermark

    # Assert
    actual = (result, type(result))
    expected = (date(2026, 1, 15), date)
    assert actual == expected


def test_state_should_read_datetime_watermark_back_as_datetime():
    # Arrange
    state = BatchState(watermark=datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC))

    # Act
    result = state.watermark

    # Assert
    actual = (result, type(result))
    expected = (datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC), datetime)
    assert actual == expected


# ============================================================================
# watermark - serialization
# ============================================================================
@pytest.mark.parametrize(
    "watermark, serialized",
    [
        (42, "00000000000000000042"),
        (date(2026, 1, 15), "2026-01-15"),
        (datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC), "2026-01-15T10:30:45.123456+00:00"),
        (None, None),
    ],
)
def test_state_should_serialize_watermark_as_string(watermark, serialized):
    # Arrange
    state = BatchState(watermark=watermark)

    # Act
    result = state.model_dump()

    # Assert
    actual = result["watermark"]
    expected = serialized
    assert actual == expected


def test_state_should_round_trip_watermark_through_serialized_string():
    # Arrange
    dumped = BatchState(watermark=42).model_dump()

    # Act
    result = BatchState(**dumped).watermark

    # Assert
    actual = (result, type(result))
    expected = (42, int)
    assert actual == expected


# ============================================================================
# watermark - validation
# ============================================================================
def test_state_should_raise_when_watermark_int_is_out_of_range():
    # Act / Assert
    with pytest.raises(ValidationError):
        BatchState(watermark=10**20)


# ============================================================================
# extra fields
# ============================================================================
def test_state_should_ignore_unknown_fields():
    # Arrange / Act
    result = BatchState(unknown1="value1")

    # Assert
    assert "unknown1" not in result.model_dump()
