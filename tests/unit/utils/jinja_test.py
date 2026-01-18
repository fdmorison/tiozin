import pytest
from jinja2 import StrictUndefined, UndefinedError

from tiozin.utils.jinja import (
    compact,
    create_jinja_environment,
    day,
    fs,
    fsdeep,
    hour,
    iso,
    iso8601,
    minute,
    month,
    nodash,
    rfc3339,
    sanitize_date,
    second,
    sql_datetime,
    trunc_date,
    trunc_day,
    trunc_hour,
    trunc_min,
    trunc_month,
    trunc_year,
    unix,
    unix_float,
    w3c,
    year,
)
from tiozin.utils.relative_date import FilesystemDeepView, FilesystemFlatView


# ============================================================================
# Testing string filters
# ============================================================================
def test_nodash_should_remove_dashes():
    actual = nodash("2026-01-14")
    expected = "20260114"
    assert actual == expected


def test_nodash_should_return_none_when_none():
    actual = nodash(None)
    assert actual is None


def test_compact_should_remove_non_alphanumeric():
    actual = compact("2026-01-14T01:59:57+00:00")
    expected = "20260114T0159570000"
    assert actual == expected


def test_compact_should_return_none_when_none():
    actual = compact(None)
    assert actual is None


def test_sanitize_date_should_replace_colons_and_spaces():
    actual = sanitize_date("2026-01-14 01:59:57")
    expected = "2026-01-14_01-59-57"
    assert actual == expected


def test_sanitize_date_should_return_none_when_none():
    actual = sanitize_date(None)
    assert actual is None


# ============================================================================
# Testing truncation filters
# ============================================================================
def test_trunc_date_should_truncate_to_day():
    actual = trunc_date("2026-01-14T01:59:57+00:00", "day")
    assert "2026-01-14T00:00:00" in actual


def test_trunc_date_should_return_none_when_none():
    actual = trunc_date(None, "day")
    assert actual is None


def test_trunc_date_should_raise_when_invalid_unit():
    with pytest.raises(ValueError, match="Invalid unit"):
        trunc_date("2026-01-14T01:59:57+00:00", "invalid")


def test_trunc_min_should_truncate_to_minute():
    actual = trunc_min("2026-01-14T01:59:57+00:00")
    assert "2026-01-14T01:59:00" in actual


def test_trunc_hour_should_truncate_to_hour():
    actual = trunc_hour("2026-01-14T01:59:57+00:00")
    assert "2026-01-14T01:00:00" in actual


def test_trunc_day_should_truncate_to_day():
    actual = trunc_day("2026-01-14T01:59:57+00:00")
    assert "2026-01-14T00:00:00" in actual


def test_trunc_month_should_truncate_to_month():
    actual = trunc_month("2026-01-14T01:59:57+00:00")
    assert "2026-01-01T00:00:00" in actual


def test_trunc_year_should_truncate_to_year():
    actual = trunc_year("2026-03-14T01:59:57+00:00")
    assert "2026-01-01T00:00:00" in actual


# ============================================================================
# Testing format filters
# ============================================================================
def test_iso_should_return_iso8601_string():
    actual = iso("2026-01-14T01:59:57+00:00")
    assert "2026-01-14T01:59:57" in actual


def test_iso8601_should_return_iso8601_string():
    actual = iso8601("2026-01-14T01:59:57+00:00")
    assert "2026-01-14T01:59:57" in actual


def test_rfc3339_should_return_rfc3339_string():
    actual = rfc3339("2026-01-14T01:59:57+00:00")
    assert "2026-01-14T01:59:57" in actual


def test_w3c_should_return_w3c_string():
    actual = w3c("2026-01-14T01:59:57+00:00")
    assert "2026-01-14T01:59:57" in actual


def test_sql_datetime_should_return_sql_string():
    actual = sql_datetime("2026-01-14T01:59:57+00:00")
    expected = "2026-01-14 01:59:57"
    assert actual == expected


# ============================================================================
# Testing unix timestamp filters
# ============================================================================
def test_unix_should_return_int_timestamp():
    actual = unix("2026-01-14T01:59:57+00:00")
    assert isinstance(actual, int)
    assert actual > 0


def test_unix_float_should_return_float_timestamp():
    actual = unix_float("2026-01-14T01:59:57+00:00")
    assert isinstance(actual, float)
    assert actual > 0


# ============================================================================
# Testing datetime part filters
# ============================================================================
def test_year_should_return_yyyy():
    actual = year("2026-01-14T01:59:57+00:00")
    expected = "2026"
    assert actual == expected


def test_month_should_return_mm():
    actual = month("2026-01-14T01:59:57+00:00")
    expected = "01"
    assert actual == expected


def test_day_should_return_dd():
    actual = day("2026-01-14T01:59:57+00:00")
    expected = "14"
    assert actual == expected


def test_hour_should_return_hh():
    actual = hour("2026-01-14T01:59:57+00:00")
    expected = "01"
    assert actual == expected


def test_minute_should_return_mm():
    actual = minute("2026-01-14T01:59:57+00:00")
    expected = "59"
    assert actual == expected


def test_second_should_return_ss():
    actual = second("2026-01-14T01:59:57+00:00")
    expected = "57"
    assert actual == expected


# ============================================================================
# Testing filesystem path filters
# ============================================================================
def test_fs_should_return_flat_view():
    actual = fs("2026-01-14T01:59:57+00:00")
    assert isinstance(actual, FilesystemFlatView)
    assert actual.date == "2026-01-14"


def test_fsdeep_should_return_deep_view():
    actual = fsdeep("2026-01-14T01:59:57+00:00")
    assert isinstance(actual, FilesystemDeepView)
    assert actual.date == "year=2026/month=01/day=14"


# ============================================================================
# Testing create_jinja_environment
# ============================================================================
def test_create_jinja_environment_should_use_strict_undefined():
    env = create_jinja_environment()
    actual = env.undefined
    expected = StrictUndefined
    assert actual == expected


def test_create_jinja_environment_should_raise_on_undefined():
    env = create_jinja_environment()
    template = env.from_string("{{ undefined_var }}")
    with pytest.raises(UndefinedError):
        template.render()


def test_create_jinja_environment_should_register_all_filters():
    env = create_jinja_environment()
    expected_filters = {
        "nodash",
        "compact",
        "sanitize_date",
        "trunc_min",
        "trunc_hour",
        "trunc_day",
        "trunc_month",
        "trunc_year",
        "iso",
        "iso8601",
        "rfc3339",
        "w3c",
        "sql_datetime",
        "unix",
        "unix_float",
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "second",
        "fs",
        "fsdeep",
    }
    actual = {k for k in expected_filters if k in env.filters}
    assert actual == expected_filters
