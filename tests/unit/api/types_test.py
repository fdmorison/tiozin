from datetime import UTC, date, datetime, timedelta, timezone
from unittest.mock import patch

import pendulum
import pytest
import uuid_utils
from pydantic import BaseModel, TypeAdapter, ValidationError

from tiozin.api.types import NominalTime, TechnicalTime, TimeOrderedId, Watermark

GENERATED_ID = "01920000-0000-7000-8000-000000000001"
PROVIDED_ID = "01920000-0000-7000-8000-000000000000"
WATERMARK = TypeAdapter(Watermark)
TECHNICAL_TIME = TypeAdapter(TechnicalTime)
NOMINAL_TIME = TypeAdapter(NominalTime)


class TimeOrderedIdModel(BaseModel):
    id: TimeOrderedId


class TimeOrderedIdModelWithDefault(BaseModel):
    id: TimeOrderedId = None


class OptionalTimeOrderedIdModel(BaseModel):
    id: TimeOrderedId | None = None


# =============================================================================
# TimeOrderedId
# =============================================================================


@pytest.mark.parametrize("model_cls", [TimeOrderedIdModel, TimeOrderedIdModelWithDefault])
@patch("tiozin.api.types.generate_time_ordered_id", return_value=GENERATED_ID)
def test_time_ordered_id_should_generate_id_when_id_is_null(_generate, model_cls):
    # Act
    result = model_cls(id=None)

    # Assert
    actual = result.id
    expected = GENERATED_ID
    assert actual == expected


@pytest.mark.parametrize("model_cls", [TimeOrderedIdModel, TimeOrderedIdModelWithDefault])
@patch("tiozin.api.types.generate_time_ordered_id", return_value=GENERATED_ID)
def test_time_ordered_id_should_generate_id_when_id_is_absent(_generate, model_cls):
    # Act
    result = model_cls()

    # Assert
    actual = result.id
    expected = GENERATED_ID
    assert actual == expected


@patch("tiozin.api.types.generate_time_ordered_id", return_value=GENERATED_ID)
def test_time_ordered_id_should_keep_none_when_id_is_null(_generate):
    # Act
    result = OptionalTimeOrderedIdModel(id=None)

    # Assert
    actual = result.id
    expected = None
    assert actual == expected


@patch("tiozin.api.types.generate_time_ordered_id", return_value=GENERATED_ID)
def test_time_ordered_id_should_keep_none_when_id_is_absent(_generate):
    # Act
    result = OptionalTimeOrderedIdModel()

    # Assert
    actual = result.id
    expected = None
    assert actual == expected


@pytest.mark.parametrize(
    "model_cls", [TimeOrderedIdModel, TimeOrderedIdModelWithDefault, OptionalTimeOrderedIdModel]
)
@patch("tiozin.api.types.generate_time_ordered_id", return_value=GENERATED_ID)
def test_time_ordered_id_should_preserve_provided_value(_generate, model_cls):
    # Act
    result = model_cls(id=PROVIDED_ID)

    # Assert
    actual = result.id
    expected = PROVIDED_ID
    assert actual == expected


@pytest.mark.parametrize(
    "model_cls", [TimeOrderedIdModel, TimeOrderedIdModelWithDefault, OptionalTimeOrderedIdModel]
)
@patch("tiozin.api.types.generate_time_ordered_id", return_value=GENERATED_ID)
def test_time_ordered_id_should_stringify_provided_value(_generate, model_cls):
    # Arrange
    value = uuid_utils.UUID(PROVIDED_ID)

    # Act
    result = model_cls(id=value)

    # Assert
    actual = (type(result.id), result.id)
    expected = (str, PROVIDED_ID)
    assert actual == expected


# =============================================================================
# TechnicalTime
# =============================================================================


@pytest.mark.parametrize(
    "value",
    [
        datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone(timedelta(hours=-3))),
        pendulum.datetime(2026, 1, 15, 9, 0, 0, tz="America/Sao_Paulo"),
    ],
)
def test_technical_time_should_normalize_aware_datetime_to_utc(value):
    # Act
    result = TECHNICAL_TIME.validate_python(value)

    # Assert
    actual = result
    expected = pendulum.datetime(2026, 1, 15, 12, 0, 0, tz="UTC")
    assert actual == expected


def test_technical_time_should_return_pendulum_datetime():
    # Arrange
    value = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)

    # Act
    result = TECHNICAL_TIME.validate_python(value)

    # Assert
    assert isinstance(result, pendulum.DateTime)


def test_technical_time_should_preserve_seconds_and_microseconds():
    # Arrange
    value = datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)

    # Act
    result = TECHNICAL_TIME.validate_python(value)

    # Assert
    actual = result
    expected = pendulum.datetime(2026, 1, 15, 10, 30, 45, 123456, tz="UTC")
    assert actual == expected


def test_technical_time_should_raise_validation_error_when_datetime_is_naive():
    # Arrange
    value = datetime(2026, 1, 15, 12, 0, 0)

    # Act / Assert
    with pytest.raises(ValidationError):
        TECHNICAL_TIME.validate_python(value)


# =============================================================================
# NominalTime
# =============================================================================


def test_nominal_time_should_truncate_to_minute():
    # Arrange
    value = datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)

    # Act
    result = NOMINAL_TIME.validate_python(value)

    # Assert
    actual = result
    expected = pendulum.datetime(2026, 1, 15, 10, 30, 0, tz="UTC")
    assert actual == expected


def test_nominal_time_should_convert_to_utc_before_truncating():
    # Arrange
    value = datetime(2026, 1, 15, 10, 15, 45, tzinfo=timezone(timedelta(hours=5, minutes=30)))

    # Act
    result = NOMINAL_TIME.validate_python(value)

    # Assert
    actual = result
    expected = pendulum.datetime(2026, 1, 15, 4, 45, 0, tz="UTC")
    assert actual == expected


def test_nominal_time_should_return_pendulum_datetime():
    # Arrange
    value = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)

    # Act
    result = NOMINAL_TIME.validate_python(value)

    # Assert
    assert isinstance(result, pendulum.DateTime)


def test_nominal_time_should_raise_validation_error_when_datetime_is_naive():
    # Arrange
    value = datetime(2026, 1, 15, 12, 30, 0)

    # Act / Assert
    with pytest.raises(ValidationError):
        NOMINAL_TIME.validate_python(value)


# =============================================================================
# Watermark
# =============================================================================


@pytest.mark.parametrize(
    "value, expected",
    [
        (42, 42),
        (date(2026, 1, 15), date(2026, 1, 15)),
    ],
)
def test_watermark_should_accept_value(value, expected):
    # Act
    result = WATERMARK.validate_python(value)

    # Assert
    actual = result
    assert actual == expected


def test_watermark_should_normalize_datetime_to_utc():
    # Arrange
    value = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))

    # Act
    result = WATERMARK.validate_python(value)

    # Assert
    actual = result
    expected = datetime(2026, 1, 15, 9, 0, 0, tzinfo=UTC)
    assert actual == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("00000000000000000042", 42),
        ("2026-01-15", date(2026, 1, 15)),
        ("2026-01-15T10:30:45.123456+00:00", datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)),
    ],
)
def test_watermark_should_parse_canonical_string(value, expected):
    # Act
    result = WATERMARK.validate_python(value)

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    ["not-a-watermark", "42", -1, 10**20],
)
def test_watermark_should_raise_validation_error_when_value_is_invalid(value):
    # Act / Assert
    with pytest.raises(ValidationError):
        WATERMARK.validate_python(value)
