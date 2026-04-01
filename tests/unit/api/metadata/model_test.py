from enum import auto

import pytest

from tiozin.api.metadata.model import LowerEnum, UpperEnum


class SampleUpper(UpperEnum):
    FOO = auto()
    BAR = auto()


class SampleLower(LowerEnum):
    FOO = auto()
    BAR = auto()


# =============================================================================
# UpperEnum — value generation
# =============================================================================


def test_upper_enum_should_generate_uppercase_value():
    actual = SampleUpper.FOO.value
    expected = "FOO"
    assert actual == expected


def test_upper_enum_str_should_return_value():
    actual = str(SampleUpper.FOO)
    expected = "FOO"
    assert actual == expected


def test_upper_enum_repr_should_return_value():
    actual = repr(SampleUpper.FOO)
    expected = "FOO"
    assert actual == expected


# =============================================================================
# UpperEnum — _missing_: case-insensitive and whitespace-tolerant lookup
# =============================================================================


def test_upper_enum_should_accept_lowercase_value():
    actual = SampleUpper("foo")
    expected = SampleUpper.FOO
    assert actual == expected


def test_upper_enum_should_accept_mixed_case_value():
    actual = SampleUpper("fOo")
    expected = SampleUpper.FOO
    assert actual == expected


def test_upper_enum_should_strip_whitespace_when_looking_up():
    actual = SampleUpper("  foo  ")
    expected = SampleUpper.FOO
    assert actual == expected


def test_upper_enum_should_raise_when_value_does_not_exist():
    with pytest.raises(ValueError):
        SampleUpper("UNKNOWN")


# =============================================================================
# LowerEnum — value generation
# =============================================================================


def test_lower_enum_should_generate_lowercase_value():
    actual = SampleLower.FOO.value
    expected = "foo"
    assert actual == expected


def test_lower_enum_str_should_return_value():
    actual = str(SampleLower.FOO)
    expected = "foo"
    assert actual == expected


def test_lower_enum_repr_should_return_value():
    actual = repr(SampleLower.FOO)
    expected = "foo"
    assert actual == expected


# =============================================================================
# LowerEnum — _missing_: case-insensitive and whitespace-tolerant lookup
# =============================================================================


def test_lower_enum_should_accept_uppercase_value():
    actual = SampleLower("FOO")
    expected = SampleLower.FOO
    assert actual == expected


def test_lower_enum_should_accept_mixed_case_value():
    actual = SampleLower("FoO")
    expected = SampleLower.FOO
    assert actual == expected


def test_lower_enum_should_strip_whitespace_when_looking_up():
    actual = SampleLower("  FOO  ")
    expected = SampleLower.FOO
    assert actual == expected


def test_lower_enum_should_raise_when_value_does_not_exist():
    with pytest.raises(ValueError):
        SampleLower("unknown")
