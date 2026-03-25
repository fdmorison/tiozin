import pytest
from assertpy import assert_that

from tiozin.compose.templating.filters import (
    JINJA,
    compact,
    fs_safe,
    nodash,
    notz,
)


def test_filters_should_be_available_in_public_api():
    """
    Detects regressions where a filter function exists but is not registered in JINJA.
    """
    # Arrange / Act
    public_filters = JINJA.filters

    # Assert
    actual = public_filters
    expected = {"nodash", "notz", "compact", "fs_safe"}
    assert_that(actual).contains_key(*expected)


def test_nodash_should_remove_dashes():
    # Arrange / Act
    actual = nodash("2026-01-14")

    # Assert
    expected = "20260114"
    assert actual == expected


def test_nodash_should_return_none_when_none():
    # Arrange / Act
    actual = nodash(None)

    # Assert
    assert actual is None


@pytest.mark.parametrize(
    "value,expected",
    [
        ("2026-01-14T01:59:57+00:00", "2026-01-14T01:59:57"),
        ("2026-01-14T01:59:57-03:00", "2026-01-14T01:59:57"),
        ("2026-01-14T01:59:57Z", "2026-01-14T01:59:57"),
        ("2026-01-14T01:59:57", "2026-01-14T01:59:57"),
        ("2026-01-14", "2026-01-14"),
    ],
)
def test_notz_should_strip_timezone(value: str, expected: str):
    # Arrange / Act
    actual = notz(value)

    # Assert
    assert actual == expected


def test_notz_should_return_none_when_none():
    # Arrange / Act
    actual = notz(None)

    # Assert
    assert actual is None


def test_compact_should_remove_non_alphanumeric():
    # Arrange / Act
    actual = compact("2026-01-14T01:59:57+00:00")

    # Assert
    expected = "20260114T0159570000"
    assert actual == expected


def test_compact_should_return_none_when_none():
    # Arrange / Act
    actual = compact(None)

    # Assert
    assert actual is None


def test_sanitize_date_should_replace_colons_and_spaces():
    # Arrange / Act
    actual = fs_safe("2026-01-14 01:59:57")

    # Assert
    expected = "2026-01-14_01-59-57"
    assert actual == expected


def test_sanitize_date_should_return_none_when_none():
    # Arrange / Act
    actual = fs_safe(None)

    # Assert
    assert actual is None
