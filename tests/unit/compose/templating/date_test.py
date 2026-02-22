from datetime import UTC, datetime

import pendulum
import pytest

from tiozin.compose import TemplateDate

ISO = "2026-01-17T10:30:45+00:00"
DT = pendulum.parse(ISO)
PY_DT = datetime(2026, 1, 17, 10, 30, 45, tzinfo=UTC)
DT_MICRO = pendulum.instance(datetime(2026, 1, 17, 10, 30, 45, 952713, tzinfo=UTC))


# ============================================================================
# coerce
# ============================================================================


def test_coerce_should_return_none_when_value_is_none():
    # Arrange
    value = None

    # Act
    result = TemplateDate.coerce(value)

    # Assert
    actual = result
    expected = None
    assert actual == expected


@pytest.mark.parametrize("value", [ISO, DT, PY_DT])
def test_coerce_should_return_equivalent_template_date_when_value_is_supported(value):
    # Arrange
    expected_dt = DT

    # Act
    result = TemplateDate.coerce(value)

    # Assert
    actual = result.dt
    expected = expected_dt
    assert actual == expected


def test_coerce_should_raise_type_error_when_value_is_invalid():
    # Arrange
    value = 123

    # Act & Assert
    with pytest.raises(TypeError, match="Expected TemplateDate"):
        TemplateDate.coerce(value)


# ============================================================================
# core
# ============================================================================


def test_template_date_should_store_datetime():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = rd.dt

    # Assert
    actual = result
    expected = DT
    assert actual == expected


def test_str_should_return_date_when_no_fmt():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = str(rd)

    # Assert
    actual = result
    expected = "2026-01-17"
    assert actual == expected


def test_repr_should_return_iso_representation():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = repr(rd)

    # Assert
    actual = result
    expected = "TemplateDate(2026-01-17T10:30:45+00:00)"
    assert actual == expected


# ============================================================================
# getitem navigation
# ============================================================================


@pytest.mark.parametrize(
    "offset,expected",
    [
        (7, "2026-01-24"),
        (-1, "2026-01-16"),
        (0, "2026-01-17"),
    ],
)
def test_getitem_should_navigate_by_offset(offset, expected):
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = rd[offset]

    # Assert
    actual = str(result.date)
    assert actual == expected


def test_getitem_should_raise_when_offset_is_not_int():
    # Arrange
    rd = TemplateDate(DT)

    # Act & Assert
    with pytest.raises(TypeError, match="integer"):
        rd["1"]


# ============================================================================
# relative properties
# ============================================================================


def test_relative_properties_should_navigate_correctly():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = (
        rd.today,
        rd.yesterday,
        rd.tomorrow,
    )

    # Assert
    actual = tuple(str(r) for r in result)
    expected = ("2026-01-17", "2026-01-16", "2026-01-18")
    assert actual == expected


# ============================================================================
# flat formats
# ============================================================================


def test_flat_formats_should_render_expected_values():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = (
        rd.flat_year,
        rd.flat_month,
        rd.flat_date,
        rd.flat_day,
        rd.flat_hour,
        rd.flat_minute,
        rd.flat_second,
        rd.flat_ts,
    )

    # Assert
    actual = tuple(str(r) for r in result)
    expected = (
        "2026",
        "2026-01",
        "2026-01-17",
        "2026-01-17",
        "2026-01-17T10",
        "2026-01-17T10-30",
        "2026-01-17T10-30-45",
        "2026-01-17T10-30-45",
    )
    assert actual == expected


# ============================================================================
# deep formats
# ============================================================================


def test_deep_formats_should_render_expected_values():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = (
        rd.deep_year,
        rd.deep_month,
        rd.deep_date,
        rd.deep_day,
        rd.deep_hour,
        rd.deep_minute,
        rd.deep_second,
        rd.deep_ts,
    )

    # Assert
    actual = tuple(str(r) for r in result)
    expected = (
        "year=2026",
        "year=2026/month=01",
        "year=2026/month=01/day=17",
        "year=2026/month=01/day=17",
        "year=2026/month=01/day=17/hour=10",
        "year=2026/month=01/day=17/hour=10/min=30",
        "year=2026/month=01/day=17/hour=10/min=30/sec=45",
        "year=2026/month=01/day=17/hour=10/min=30/sec=45",
    )
    assert actual == expected


# ============================================================================
# order independence
# ============================================================================


def test_format_and_navigation_should_be_order_independent():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    left = (
        rd.flat_hour.yesterday,
        rd.iso.yesterday,
        rd.deep_date.start_of_month,
        rd.sql_datetime.yesterday,
    )
    right = (
        rd.yesterday.flat_hour,
        rd.yesterday.iso,
        rd.start_of_month.deep_date,
        rd.yesterday.sql_datetime,
    )

    # Assert
    actual = tuple(str(x) for x in left)
    expected = tuple(str(x) for x in right)
    assert actual == expected


# ============================================================================
# to_dict
# ============================================================================


def test_to_dict_should_expose_public_properties():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = rd.to_dict()

    # Assert
    actual = (
        str(result["date"]),
        str(result["iso"]),
        str(result["flat_hour"]),
        str(result["deep_hour"]),
        str(result["ds"]),
        str(result["ts"]),
        str(result["unix"]),
    )
    expected = (
        "2026-01-17",
        ISO,
        "2026-01-17T10",
        "year=2026/month=01/day=17/hour=10",
        "2026-01-17",
        ISO,
        str(DT.int_timestamp),
    )
    assert actual == expected


def test_to_dict_should_exclude_private_attributes_and_methods():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = rd.to_dict()

    # Assert
    actual = (
        "_dt" in result,
        any(k.startswith("_") for k in result),
        "to_dict" in result,
    )
    expected = (False, False, False)
    assert actual == expected


# ============================================================================
# unix timestamps
# ============================================================================


def test_unix_float_should_return_float_timestamp():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = rd.unix_float

    # Assert
    actual = str(result)
    expected = str(DT.float_timestamp)
    assert actual == expected


# ============================================================================
# microsecond regression
# ============================================================================


@pytest.mark.parametrize("attr", ["iso", "ts"])
def test_iso_formats_should_strip_microseconds_when_input_has_them(attr):
    # Arrange
    rd = TemplateDate(DT_MICRO)

    # Act
    result = getattr(rd, attr)

    # Assert
    actual = str(result)
    expected = "2026-01-17T10:30:45+00:00"
    assert actual == expected


# ============================================================================
# precision formats
# ============================================================================


def test_iso_ms_should_render_milliseconds():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = rd.iso_ms

    # Assert
    actual = str(result)
    expected = "2026-01-17T10:30:45.000+00:00"
    assert actual == expected


def test_iso_micro_should_render_zero_microseconds_when_input_has_none():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = rd.iso_micro

    # Assert
    actual = str(result)
    expected = "2026-01-17T10:30:45.000000+00:00"
    assert actual == expected


def test_iso_micro_should_render_actual_microseconds_when_input_has_them():
    # Arrange
    rd = TemplateDate(DT_MICRO)

    # Act
    result = rd.iso_micro

    # Assert
    actual = str(result)
    expected = "2026-01-17T10:30:45.952713+00:00"
    assert actual == expected


def test_ts_naive_should_render_without_timezone():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = rd.ts_naive

    # Assert
    actual = str(result)
    expected = "2026-01-17T10:30:45"
    assert actual == expected


# ============================================================================
# Airflow interval formats
# ============================================================================


def test_airflow_interval_formats_should_render_expected_values():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = (
        rd.prev_ds,
        rd.next_ds,
        rd.execution_date,
        rd.logical_date,
        rd.data_interval_start,
        rd.data_interval_end,
    )

    # Assert
    actual = tuple(str(r) for r in result)
    expected = (
        "2026-01-16",
        "2026-01-18",
        "2026-01-17T10:30:45+00:00",
        "2026-01-17T10:30:45+00:00",
        "2026-01-17T10:30:45+00:00",
        "2026-01-18T10:30:45+00:00",
    )
    assert actual == expected


# ============================================================================
# start-of navigation
# ============================================================================


def test_start_of_navigation_should_navigate_correctly():
    # Arrange
    rd = TemplateDate(DT)  # 2026-01-17T10:30:45 (Saturday)

    # Act
    result = (
        rd.start_of_year,
        rd.start_of_month,
        rd.start_of_day,
        rd.start_of_week,
        rd.start_of_hour.flat_hour,
        rd.start_of_minute.flat_minute,
    )

    # Assert
    actual = tuple(str(r) for r in result)
    expected = (
        "2026-01-01",
        "2026-01-01",
        "2026-01-17",
        "2026-01-12",  # Monday
        "2026-01-17T10",
        "2026-01-17T10-30",
    )
    assert actual == expected


# ============================================================================
# at-hour
# ============================================================================


@pytest.mark.parametrize(
    "prop,expected",
    [
        ("at00", "2026-01-17T00:00:00+00:00"),
        ("at06", "2026-01-17T06:00:00+00:00"),
        ("at09", "2026-01-17T09:00:00+00:00"),
        ("at12", "2026-01-17T12:00:00+00:00"),
        ("at23", "2026-01-17T23:00:00+00:00"),
        ("midnight", "2026-01-17T00:00:00+00:00"),
        ("noon", "2026-01-17T12:00:00+00:00"),
    ],
)
def test_at_hour_should_render_expected_time(prop, expected):
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = getattr(rd, prop)

    # Assert
    actual = str(result)
    assert actual == expected


def test_at_hour_should_preserve_fmt_when_chained_after_format():
    # Arrange
    rd = TemplateDate(DT)

    # Act
    result = rd.flat_hour.at09

    # Assert
    actual = str(result)
    expected = "2026-01-17T09"
    assert actual == expected


# ============================================================================
# datetime parts
# ============================================================================


def test_datetime_parts_should_render_expected_values():
    # Arrange
    rd = TemplateDate(DT)  # 2026-01-17T10:30:45+00:00

    # Act
    result = (
        rd.YYYY,
        rd.MM,
        rd.DD,
        rd.DDD,
        rd.HH,
        rd.mm,
        rd.ss,
        rd.time,
        rd.Z,
        rd.ZZ,
    )

    # Assert
    actual = tuple(str(r) for r in result)
    expected = (
        "2026",
        "01",
        "17",
        "017",
        "10",
        "30",
        "45",
        "10:30:45",
        "+00:00",
        "+0000",
    )
    assert actual == expected


def test_day_of_year_should_be_zero_padded_when_day_is_in_first_month():
    # Arrange
    rd = TemplateDate(pendulum.parse("2026-01-01T00:00:00+00:00"))

    # Act
    result = rd.DDD

    # Assert
    actual = str(result)
    expected = "001"
    assert actual == expected
