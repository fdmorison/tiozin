from datetime import UTC, date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from tiozin.api.metadata.batch.state import BatchState

# Window bounds of the state being advanced, named after their semantic role.
PREVIOUS_START = datetime(2026, 1, 14, tzinfo=UTC)
PREVIOUS_END = datetime(2026, 1, 15, 10, 30, tzinfo=UTC)

# Time the previous state advances to.
NEW_END = datetime(2026, 1, 16, 8, 15, tzinfo=UTC)

# Sub-minute-precision datetime used to exercise watermark round-tripping.
WATERMARK_DATETIME = datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)


# ============================================================================
# defaults
# ============================================================================
def test_state_should_default_start_to_epoch():
    # Arrange / Act
    result = BatchState()

    # Assert
    actual = result.start
    expected = datetime(1970, 1, 1, tzinfo=UTC)
    assert actual == expected


def test_state_should_default_watermark_to_epoch():
    # Arrange / Act
    result = BatchState()

    # Assert
    actual = result.watermark
    expected = datetime(1970, 1, 1, tzinfo=UTC)
    assert actual == expected


def test_state_should_default_end_to_current_utc_time_truncated_to_minute():
    # Arrange
    before = datetime.now(UTC).replace(second=0, microsecond=0)

    # Act
    result = BatchState()

    # Assert
    after = datetime.now(UTC).replace(second=0, microsecond=0)
    assert before <= result.end <= after


def test_state_should_default_end_with_zero_seconds_and_microseconds():
    # Arrange / Act
    result = BatchState()

    # Assert
    actual = (result.end.second, result.end.microsecond)
    expected = (0, 0)
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


def test_state_should_truncate_start_and_end_to_minute():
    # Arrange
    dirty = datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)

    # Act
    result = BatchState(start=dirty, end=dirty)

    # Assert
    actual = (result.start, result.end)
    expected = (
        datetime(2026, 1, 15, 10, 30, tzinfo=UTC),
        datetime(2026, 1, 15, 10, 30, tzinfo=UTC),
    )
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
    state = BatchState(watermark=WATERMARK_DATETIME)

    # Act
    result = state.watermark

    # Assert
    actual = (result, type(result))
    expected = (WATERMARK_DATETIME, datetime)
    assert actual == expected


# ============================================================================
# watermark - serialization
# ============================================================================
@pytest.mark.parametrize(
    "watermark, serialized",
    [
        (42, "00000000000000000042"),
        (date(2026, 1, 15), "2026-01-15"),
        (WATERMARK_DATETIME, "2026-01-15T10:30:45.123456+00:00"),
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
# advance_to
# ============================================================================
def test_advance_to_should_set_start_to_previous_end():
    # Arrange
    previous = BatchState(
        start=PREVIOUS_START,
        end=PREVIOUS_END,
    )

    # Act
    result = previous.advance_to(NEW_END)

    # Assert
    actual = (result.start, result.end)
    expected = (
        previous.end,
        NEW_END,
    )
    assert actual == expected


def test_advance_to_should_carry_watermark_forward():
    # Arrange
    previous = BatchState(
        start=PREVIOUS_START,
        end=PREVIOUS_END,
        watermark=42,
    )

    # Act
    result = previous.advance_to(NEW_END)

    # Assert
    actual = result.watermark
    expected = 42
    assert actual == expected


def test_advance_to_should_not_mutate_the_original_state():
    # Arrange
    previous = BatchState(
        start=PREVIOUS_START,
        end=PREVIOUS_END,
    )

    # Act
    previous.advance_to(NEW_END)

    # Assert
    actual = (previous.start, previous.end)
    expected = (
        PREVIOUS_START,
        PREVIOUS_END,
    )
    assert actual == expected


def test_advance_to_should_truncate_end_to_minute():
    # Arrange
    previous = BatchState(
        start=PREVIOUS_START,
        end=PREVIOUS_END,
    )
    dirty_end = datetime(2026, 1, 16, 8, 15, 7, 555, tzinfo=UTC)

    # Act
    result = previous.advance_to(dirty_end)

    # Assert
    actual = result.end
    expected = datetime(2026, 1, 16, 8, 15, tzinfo=UTC)
    assert actual == expected


@pytest.mark.parametrize("end", [None, 0])
def test_advance_to_should_return_same_state_when_end_is_falsy(end):
    # Arrange
    previous = BatchState(
        start=PREVIOUS_START,
        end=PREVIOUS_END,
    )

    # Act
    result = previous.advance_to(end)

    # Assert
    assert result is previous


# ============================================================================
# extra fields
# ============================================================================
def test_state_should_ignore_unknown_fields():
    # Arrange / Act
    result = BatchState(unknown1="value1")

    # Assert
    assert "unknown1" not in result.model_dump()
