from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from tiozin.api.metadata.batch.watermark import (
    check_watermark,
    parse_watermark,
    serialize_watermark,
)


# ============================================================================
# parse_watermark
# ============================================================================
def test_parse_watermark_should_parse_fixed_width_digits_as_int():
    # Arrange
    value = "00000000000000000042"

    # Act
    result = parse_watermark(value)

    # Assert
    actual = (result, type(result))
    expected = (42, int)
    assert actual == expected


def test_parse_watermark_should_parse_iso_date_as_date():
    # Arrange
    value = "2026-01-15"

    # Act
    result = parse_watermark(value)

    # Assert
    actual = (result, type(result))
    expected = (date(2026, 1, 15), date)
    assert actual == expected


def test_parse_watermark_should_parse_iso_timestamp_as_datetime():
    # Arrange
    value = "2026-01-15T10:30:45.123456+00:00"

    # Act
    result = parse_watermark(value)

    # Assert
    actual = (result, type(result))
    expected = (datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC), datetime)
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    [42, date(2026, 1, 15), datetime(2026, 1, 15, tzinfo=UTC), None],
)
def test_parse_watermark_should_pass_through_non_string(value):
    # Act
    result = parse_watermark(value)

    # Assert
    actual = result
    expected = value
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    ["not-a-watermark", "42", "2026-1-5", "2026-01-15T10:30:45+00:00"],
)
def test_parse_watermark_should_raise_value_error_when_string_is_not_canonical(value):
    # Act / Assert
    with pytest.raises(ValueError):
        parse_watermark(value)


# ============================================================================
# check_watermark
# ============================================================================
@pytest.mark.parametrize(
    "value",
    [0, 42, date(2026, 1, 15), None],
)
def test_check_watermark_should_pass_through_valid_value(value):
    # Act
    result = check_watermark(value)

    # Assert
    actual = result
    expected = value
    assert actual == expected


def test_check_watermark_should_normalize_datetime_to_utc():
    # Arrange
    value = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))

    # Act
    result = check_watermark(value)

    # Assert
    actual = result
    expected = datetime(2026, 1, 15, 9, 0, 0, tzinfo=UTC)
    assert actual == expected


def test_check_watermark_should_raise_value_error_when_value_is_bool():
    # Act / Assert
    with pytest.raises(ValueError):
        check_watermark(True)


@pytest.mark.parametrize(
    "value",
    [-1, 10**20],
)
def test_check_watermark_should_raise_value_error_when_int_is_out_of_range(value):
    # Act / Assert
    with pytest.raises(ValueError):
        check_watermark(value)


# ============================================================================
# serialize_watermark
# ============================================================================
def test_serialize_watermark_should_zero_pad_int_to_fixed_width():
    # Arrange
    value = 42

    # Act
    result = serialize_watermark(value)

    # Assert
    actual = result
    expected = "00000000000000000042"
    assert actual == expected


def test_serialize_watermark_should_render_date_as_iso():
    # Arrange
    value = date(2026, 1, 15)

    # Act
    result = serialize_watermark(value)

    # Assert
    actual = result
    expected = "2026-01-15"
    assert actual == expected


def test_serialize_watermark_should_render_datetime_with_microsecond_precision():
    # Arrange
    value = datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)

    # Act
    result = serialize_watermark(value)

    # Assert
    actual = result
    expected = "2026-01-15T10:30:45.123456+00:00"
    assert actual == expected


def test_serialize_watermark_should_return_none_when_value_is_none():
    # Act
    result = serialize_watermark(None)

    # Assert
    actual = result
    expected = None
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    [42, date(2026, 1, 15), datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)],
)
def test_serialize_watermark_should_round_trip_through_parse(value):
    # Act
    result = parse_watermark(serialize_watermark(value))

    # Assert
    actual = result
    expected = value
    assert actual == expected
