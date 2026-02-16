from datetime import datetime

import pendulum
import pytest

from tiozin.compose.templating.relative_date import (
    FilesystemDeepView,
    FilesystemFlatView,
    RelativeDate,
)


# ============================================================================
# Testing RelativeDate.coerce()
# ============================================================================
def test_coerce_should_return_none_when_none():
    actual = RelativeDate.coerce(None)
    assert actual is None


def test_coerce_should_return_dt_from_relative_date():
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)
    actual = RelativeDate.coerce(rd)
    assert actual == dt


def test_coerce_should_return_pendulum_datetime_unchanged():
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    actual = RelativeDate.coerce(dt)
    assert actual is dt


def test_coerce_should_convert_datetime_to_pendulum():
    dt = datetime(2026, 1, 17, 10, 30, 45)
    actual = RelativeDate.coerce(dt)
    assert isinstance(actual, pendulum.DateTime)
    assert actual.year == 2026
    assert actual.month == 1
    assert actual.day == 17


def test_coerce_should_parse_iso_string():
    actual = RelativeDate.coerce("2026-01-17T10:30:45+00:00")
    assert isinstance(actual, pendulum.DateTime)
    assert actual.year == 2026
    assert actual.month == 1
    assert actual.day == 17


def test_coerce_should_raise_when_invalid_type():
    with pytest.raises(TypeError, match="Expected RelativeDate, datetime or ISO string"):
        RelativeDate.coerce(12345)


# ============================================================================
# Testing RelativeDate - Core
# ============================================================================
def test_relative_date_should_store_datetime():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")

    # Act
    rd = RelativeDate(dt)

    # Assert
    assert rd.dt == dt


def test_str_should_return_date():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = str(rd)

    # Assert
    expected = "2026-01-17"
    assert actual == expected


def test_repr_should_return_formatted_string():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = repr(rd)

    # Assert
    expected = "RelativeDate(2026-01-17)"
    assert actual == expected


def test_date_should_return_iso_date():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.date

    # Assert
    expected = "2026-01-17"
    assert actual == expected


# ============================================================================
# Testing RelativeDate - Index Navigation
# ============================================================================
def test_getitem_should_return_future_date_when_positive_offset():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd[7].date

    # Assert
    expected = "2026-01-24"
    assert actual == expected


def test_getitem_should_return_past_date_when_negative_offset():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd[-1].date

    # Assert
    expected = "2026-01-16"
    assert actual == expected


def test_getitem_should_return_same_date_when_zero_offset():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd[0].date

    # Assert
    expected = "2026-01-17"
    assert actual == expected


def test_getitem_should_raise_when_non_int_offset():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act & Assert
    with pytest.raises(TypeError, match="offset must be an integer"):
        rd["1"]


def test_getitem_should_support_chained_navigation():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd[-1][3].date  # yesterday + 3 days = +2 days

    # Assert
    expected = "2026-01-19"
    assert actual == expected


# ============================================================================
# Testing RelativeDate - Relative Navigation Properties
# ============================================================================
def test_today_should_return_same_date():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.today.date

    # Assert
    expected = "2026-01-17"
    assert actual == expected


def test_yesterday_should_return_previous_date():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.yesterday.date

    # Assert
    expected = "2026-01-16"
    assert actual == expected


def test_tomorrow_should_return_next_date():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.tomorrow.date

    # Assert
    expected = "2026-01-18"
    assert actual == expected


def test_relative_date_should_support_chained_relative_navigation():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.yesterday.tomorrow.date

    # Assert
    expected = "2026-01-17"
    assert actual == expected


# ============================================================================
# Testing RelativeDate - Web / ISO Standards
# ============================================================================
def test_iso_should_return_iso8601_string():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.iso

    # Assert
    assert actual == dt.to_iso8601_string()


def test_iso8601_should_return_iso8601_string():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.iso8601

    # Assert
    assert actual == dt.to_iso8601_string()


def test_rfc3339_should_return_rfc3339_string():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.rfc3339

    # Assert
    assert actual == dt.to_rfc3339_string()


def test_w3c_should_return_w3c_string():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.w3c

    # Assert
    assert actual == dt.to_w3c_string()


def test_sql_datetime_should_return_datetime_string():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.sql_datetime

    # Assert
    expected = "2026-01-17 10:30:45"
    assert actual == expected


# ============================================================================
# Testing RelativeDate - Unix Timestamps
# ============================================================================
def test_unix_should_return_int_timestamp():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.unix

    # Assert
    assert actual == dt.int_timestamp
    assert isinstance(actual, int)


def test_unix_float_should_return_float_timestamp():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45.123456+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.unix_float

    # Assert
    assert actual == dt.float_timestamp
    assert isinstance(actual, float)


# ============================================================================
# Testing RelativeDate - Datetime Parts
# ============================================================================
def test_datetime_parts_should_return_formatted_values():
    # Arrange
    dt = pendulum.parse("2026-03-25T14:07:33+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = (
        rd.YYYY,
        rd.MM,
        rd.DD,
        rd.DDD,
        rd.HH,
        rd.mm,
        rd.ss,
        rd.time,
    )

    # Assert
    expected = (
        "2026",
        "03",
        "25",
        "84",  # day of year
        "14",
        "07",
        "33",
        "14:07:33",
    )
    assert actual == expected


def test_timezone_parts_should_return_formatted_values():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = (
        rd.Z,
        rd.ZZ,
        rd.z,
        rd.zz,
    )

    # Assert
    expected = (
        "+00:00",
        "+0000",
        "+00:00",  # z format returns offset not timezone name
        "+00:00",  # zz format returns offset not timezone name
    )
    assert actual == expected


# ============================================================================
# Testing RelativeDate - Airflow Standards
# ============================================================================
def test_ds_should_return_date_string():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.ds

    # Assert
    expected = "2026-01-17"
    assert actual == expected


def test_ts_should_return_timestamp_string():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.ts

    # Assert
    expected = "2026-01-17T10:30:45"
    assert actual == expected


def test_prev_ds_should_return_previous_date():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.prev_ds

    # Assert
    expected = "2026-01-16"
    assert actual == expected


def test_next_ds_should_return_next_date():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.next_ds

    # Assert
    expected = "2026-01-18"
    assert actual == expected


def test_execution_date_should_return_datetime():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.execution_date

    # Assert
    assert actual == dt


def test_logical_date_should_return_datetime():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.logical_date

    # Assert
    assert actual == dt


def test_data_interval_start_should_return_datetime():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.data_interval_start

    # Assert
    assert actual == dt


def test_data_interval_end_should_return_next_day():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.data_interval_end

    # Assert
    expected = dt.add(days=1)
    assert actual == expected


# ============================================================================
# Testing RelativeDate - Filesystem Views
# ============================================================================
def test_fs_should_return_flat_view():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.fs

    # Assert
    assert isinstance(actual, FilesystemFlatView)


def test_fsdeep_should_return_deep_view():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.fsdeep

    # Assert
    assert isinstance(actual, FilesystemDeepView)


# ============================================================================
# Testing RelativeDate - to_dict
# ============================================================================
def test_to_dict_should_contain_core_properties():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    dyct = rd.to_dict()

    # Assert
    assert dyct["date"] == "2026-01-17"
    assert dyct["ds"] == "2026-01-17"
    assert dyct["ts"] == "2026-01-17T10:30:45"
    assert dyct["YYYY"] == "2026"
    assert dyct["MM"] == "01"
    assert dyct["DD"] == "17"


def test_to_dict_should_exclude_private_attributes():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    dyct = rd.to_dict()

    # Assert
    assert "_dt" not in dyct
    assert not any(k.startswith("_") for k in dyct.keys())


def test_to_dict_should_exclude_methods():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    dyct = rd.to_dict()

    # Assert
    assert "to_dict" not in dyct


# ============================================================================
# Testing FilesystemFlatView
# ============================================================================
def test_filesystem_flat_view_date_should_return_iso_date():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    fs = FilesystemFlatView(dt)

    # Act
    actual = fs.date

    # Assert
    expected = "2026-01-17"
    assert actual == expected


def test_filesystem_flat_view_day_should_return_iso_date():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    fs = FilesystemFlatView(dt)

    # Act
    actual = fs.day

    # Assert
    expected = "2026-01-17"
    assert actual == expected


def test_filesystem_flat_view_hour_should_return_date_with_hour():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    fs = FilesystemFlatView(dt)

    # Act
    actual = fs.hour

    # Assert
    expected = "2026-01-17T10"
    assert actual == expected


def test_filesystem_flat_view_minute_should_return_date_with_hour_minute():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    fs = FilesystemFlatView(dt)

    # Act
    actual = fs.minute

    # Assert
    expected = "2026-01-17T10-30"
    assert actual == expected


def test_filesystem_flat_view_second_should_return_full_timestamp():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    fs = FilesystemFlatView(dt)

    # Act
    actual = fs.second

    # Assert
    expected = "2026-01-17T10-30-45"
    assert actual == expected


# ============================================================================
# Testing FilesystemDeepView
# ============================================================================
def test_filesystem_deep_view_year_should_return_year_path():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    fsdeep = FilesystemDeepView(dt)

    # Act
    actual = fsdeep.year

    # Assert
    expected = "year=2026"
    assert actual == expected


def test_filesystem_deep_view_month_should_return_year_month_path():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    fsdeep = FilesystemDeepView(dt)

    # Act
    actual = fsdeep.month

    # Assert
    expected = "year=2026/month=01"
    assert actual == expected


def test_filesystem_deep_view_date_should_return_full_date_path():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    fsdeep = FilesystemDeepView(dt)

    # Act
    actual = fsdeep.date

    # Assert
    expected = "year=2026/month=01/day=17"
    assert actual == expected


def test_filesystem_deep_view_day_should_return_full_date_path():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    fsdeep = FilesystemDeepView(dt)

    # Act
    actual = fsdeep.day

    # Assert
    expected = "year=2026/month=01/day=17"
    assert actual == expected


def test_filesystem_deep_view_hour_should_return_date_hour_path():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    fsdeep = FilesystemDeepView(dt)

    # Act
    actual = fsdeep.hour

    # Assert
    expected = "year=2026/month=01/day=17/hour=10"
    assert actual == expected


def test_filesystem_deep_view_minute_should_return_date_hour_minute_path():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    fsdeep = FilesystemDeepView(dt)

    # Act
    actual = fsdeep.minute

    # Assert
    expected = "year=2026/month=01/day=17/hour=10/min=30"
    assert actual == expected


def test_filesystem_deep_view_second_should_return_full_path():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    fsdeep = FilesystemDeepView(dt)

    # Act
    actual = fsdeep.second

    # Assert
    expected = "year=2026/month=01/day=17/hour=10/min=30/sec=45"
    assert actual == expected


# ============================================================================
# Testing RelativeDate - Combined Navigation with Formats
# ============================================================================
def test_yesterday_should_return_correct_rfc3339():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.yesterday.rfc3339

    # Assert
    expected = pendulum.parse("2026-01-16T10:30:45+00:00").to_rfc3339_string()
    assert actual == expected


def test_offset_should_return_correct_fsdeep_hour():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd[-7].fsdeep.hour

    # Assert
    expected = "year=2026/month=01/day=10/hour=10"
    assert actual == expected


def test_tomorrow_should_return_correct_fs_date():
    # Arrange
    dt = pendulum.parse("2026-01-17T10:30:45+00:00")
    rd = RelativeDate(dt)

    # Act
    actual = rd.tomorrow.fs.date

    # Assert
    expected = "2026-01-18"
    assert actual == expected
