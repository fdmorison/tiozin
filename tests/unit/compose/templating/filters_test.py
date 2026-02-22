import pytest
from jinja2 import StrictUndefined, UndefinedError

from tiozin.compose.templating.filters import (
    compact,
    create_jinja_environment,
    fs_safe,
    nodash,
    notz,
)


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


def test_notz_should_remove_timezone_offset():
    assert notz("2026-01-14T01:59:57+00:00") == "2026-01-14T01:59:57"


def test_notz_should_remove_negative_timezone_offset():
    assert notz("2026-01-14T01:59:57-03:00") == "2026-01-14T01:59:57"


def test_notz_should_remove_z_suffix():
    assert notz("2026-01-14T01:59:57Z") == "2026-01-14T01:59:57"


def test_notz_should_return_none_when_none():
    assert notz(None) is None


def test_notz_should_leave_date_without_timezone_unchanged():
    assert notz("2026-01-14T01:59:57") == "2026-01-14T01:59:57"
    assert notz("2026-01-14") == "2026-01-14"


def test_compact_should_remove_non_alphanumeric():
    actual = compact("2026-01-14T01:59:57+00:00")
    expected = "20260114T0159570000"
    assert actual == expected


def test_compact_should_return_none_when_none():
    actual = compact(None)
    assert actual is None


def test_sanitize_date_should_replace_colons_and_spaces():
    actual = fs_safe("2026-01-14 01:59:57")
    expected = "2026-01-14_01-59-57"
    assert actual == expected


def test_sanitize_date_should_return_none_when_none():
    actual = fs_safe(None)
    assert actual is None


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
        "notz",
        "compact",
        "fs_safe",
    }
    actual = {k for k in expected_filters if k in env.filters}
    assert actual == expected_filters
