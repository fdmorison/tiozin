from datetime import UTC, datetime

import pendulum
import pytest

from tiozin.api.enums import Cadence

# =============================================================================
# Cadence.unit — the pendulum calendar unit each cadence measures its slots in
# =============================================================================


@pytest.mark.parametrize(
    "cadence, expected",
    [
        (Cadence.MINUTELY, "minute"),
        (Cadence.HOURLY, "hour"),
        (Cadence.DAILY, "day"),
        (Cadence.WEEKLY, "week"),
        (Cadence.MONTHLY, "month"),
    ],
)
def test_unit_should_return_calendar_unit(cadence, expected):
    # Act
    result = cadence.unit

    # Assert
    actual = result
    assert actual == expected


# =============================================================================
# Cadence.step — one slot advance as datetime keyword arguments
# =============================================================================


@pytest.mark.parametrize(
    "cadence, expected",
    [
        (Cadence.MINUTELY, {"minutes": 1}),
        (Cadence.HOURLY, {"hours": 1}),
        (Cadence.DAILY, {"days": 1}),
        (Cadence.WEEKLY, {"weeks": 1}),
        (Cadence.MONTHLY, {"months": 1}),
    ],
)
def test_step_should_return_datetime_kwargs(cadence, expected):
    # Act
    result = cadence.step

    # Assert
    actual = result
    assert actual == expected


# =============================================================================
# Cadence.duration — the length of one slot as a pendulum.Duration
# =============================================================================


def test_duration_should_return_one_slot_duration():
    # Act
    result = Cadence.MINUTELY.duration

    # Assert
    actual = result
    expected = pendulum.Duration(minutes=1)
    assert actual == expected


def test_duration_should_span_24_hours_for_daily():
    # Act
    result = Cadence.DAILY.duration

    # Assert
    actual = result.in_hours()
    expected = 24
    assert actual == expected


# =============================================================================
# Cadence.truncate — zeroes everything below the cadence granularity
# =============================================================================


@pytest.mark.parametrize(
    "cadence, expected",
    [
        (Cadence.MINUTELY, pendulum.parse("2024-03-15T10:30:00Z")),
        (Cadence.HOURLY, pendulum.parse("2024-03-15T10:00:00Z")),
        (Cadence.DAILY, pendulum.parse("2024-03-15T00:00:00Z")),
        (Cadence.WEEKLY, pendulum.parse("2024-03-11T00:00:00Z")),
        (Cadence.MONTHLY, pendulum.parse("2024-03-01T00:00:00Z")),
    ],
)
def test_truncate_should_zero_fields_below_cadence(cadence, expected):
    # Arrange
    value = pendulum.parse("2024-03-15T10:30:45.123456Z")

    # Act
    result = cadence.truncate(value)

    # Assert
    actual = result
    assert actual == expected


def test_truncate_should_return_pendulum_datetime():
    # Arrange
    value = datetime(2024, 3, 15, 10, 30, 45, tzinfo=UTC)

    # Act
    result = Cadence.MINUTELY.truncate(value)

    # Assert
    assert isinstance(result, pendulum.DateTime)


def test_truncate_should_assume_utc_when_datetime_is_naive():
    # Arrange
    value = datetime(2024, 3, 15, 10, 30, 45)

    # Act
    result = Cadence.MINUTELY.truncate(value)

    # Assert
    actual = result
    expected = datetime(2024, 3, 15, 10, 30, 0, tzinfo=UTC)
    assert actual == expected


# =============================================================================
# Cadence.next / previous — start of the following / preceding slot
# =============================================================================


def test_next_should_return_start_of_following_slot():
    # Arrange
    value = pendulum.parse("2024-03-15T10:30:00Z")

    # Act
    result = Cadence.DAILY.next(value)

    # Assert
    actual = result
    expected = pendulum.parse("2024-03-16T00:00:00Z")
    assert actual == expected


def test_previous_should_return_start_of_preceding_slot():
    # Arrange
    value = pendulum.parse("2024-03-15T10:30:00Z")

    # Act
    result = Cadence.DAILY.previous(value)

    # Assert
    actual = result
    expected = pendulum.parse("2024-03-14T00:00:00Z")
    assert actual == expected


# =============================================================================
# Cadence.interval — the [start, end) window of one slot
# =============================================================================


def test_interval_should_end_at_value_slot_by_default():
    # Arrange
    value = pendulum.parse("2024-03-15T10:30:00Z")

    # Act
    result = Cadence.DAILY.interval(value)

    # Assert
    actual = result
    expected = (
        pendulum.parse("2024-03-14T00:00:00Z"),
        pendulum.parse("2024-03-15T00:00:00Z"),
    )
    assert actual == expected


def test_interval_should_start_at_value_slot_when_is_start():
    # Arrange
    value = pendulum.parse("2024-03-15T10:30:00Z")

    # Act
    result = Cadence.DAILY.interval(value, is_start=True)

    # Assert
    actual = result
    expected = (
        pendulum.parse("2024-03-15T00:00:00Z"),
        pendulum.parse("2024-03-16T00:00:00Z"),
    )
    assert actual == expected


# =============================================================================
# Cadence.is_nominal — whether a datetime sits exactly on a slot boundary
# =============================================================================


def test_is_nominal_should_pass_when_on_slot_boundary():
    # Arrange
    value = pendulum.parse("2024-03-15T10:00:00Z")

    # Act
    result = Cadence.HOURLY.is_nominal(value)

    # Assert
    assert result


def test_is_nominal_should_not_pass_when_off_slot_boundary():
    # Arrange
    value = pendulum.parse("2024-03-15T10:30:00Z")

    # Act
    result = Cadence.HOURLY.is_nominal(value)

    # Assert
    assert not result
