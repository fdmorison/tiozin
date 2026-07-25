from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import patch

import pendulum
import pytest
import uuid_utils
from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from tiozin.api.types import (
    Attributes,
    Bookmarks,
    Counter,
    NominalTime,
    Slug,
    TechnicalTime,
    TimeOrderedId,
)

GENERATED_ID = "01920000-0000-7000-8000-000000000001"
PROVIDED_ID = "01920000-0000-7000-8000-000000000000"
TECHNICAL_TIME = TypeAdapter(TechnicalTime)
NOMINAL_TIME = TypeAdapter(NominalTime)
SLUG = TypeAdapter(Slug)


class TestModel(BaseModel):
    model_config = ConfigDict(
        validate_default=True,
        validate_assignment=True,
    )


class TimeOrderedIdModel(TestModel):
    id: TimeOrderedId


class TimeOrderedIdModelWithDefault(TestModel):
    id: TimeOrderedId = None


class OptionalTimeOrderedIdModel(TestModel):
    id: TimeOrderedId | None = None


class CounterModel(TestModel):
    count: Counter


class AttributesModel(TestModel):
    attributes: Attributes


class BookmarksModel(TestModel):
    bookmarks: Bookmarks


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
# Counter
# =============================================================================


def test_counter_should_default_to_zero_when_omitted():
    # Act
    result = CounterModel()

    # Assert
    actual = result.count
    expected = 0
    assert actual == expected


def test_counter_should_preserve_provided_non_negative_value():
    # Act
    result = CounterModel(count=5)

    # Assert
    actual = result.count
    expected = 5
    assert actual == expected


def test_counter_should_raise_validation_error_when_value_is_negative():
    # Act / Assert
    with pytest.raises(ValidationError):
        CounterModel(count=-1)


# =============================================================================
# Attributes
# =============================================================================


def test_attributes_should_default_to_empty_dict_when_omitted():
    # Act
    result = AttributesModel()

    # Assert
    actual = result.attributes
    expected = {}
    assert actual == expected


def test_attributes_should_default_to_empty_dict_when_none():
    # Act
    result = AttributesModel(attributes=None)

    # Assert
    actual = result.attributes
    expected = {}
    assert actual == expected


def test_attributes_should_preserve_provided_mapping():
    # Act
    result = AttributesModel(attributes={"k": "v", "n": 1})

    # Assert
    actual = result.attributes
    expected = {"k": "v", "n": 1}
    assert actual == expected


def test_attributes_should_not_mutate_provided_mapping():
    # Arrange
    source = {"k": "v"}
    model = AttributesModel(attributes=source)

    # Act
    model.attributes["k2"] = "v2"

    # Assert
    actual = source
    expected = {"k": "v"}
    assert actual == expected


def test_attributes_should_not_share_default_between_instances():
    # Arrange
    first = AttributesModel()
    second = AttributesModel()

    # Act
    first.attributes["k"] = "v"

    # Assert
    actual = second.attributes
    expected = {}
    assert actual == expected


def test_attributes_should_convert_pairs_to_mapping():
    # Act
    result = AttributesModel(attributes=(("a", 1), ("b", 2)))

    # Assert
    actual = result.attributes
    expected = {"a": 1, "b": 2}
    assert actual == expected


def test_attributes_should_support_keypath_access():
    # Act
    result = AttributesModel(attributes={"a": {"b": 1}})

    # Assert
    actual = result.attributes["a.b"]
    expected = 1
    assert actual == expected


def test_attributes_should_support_keypath_access_on_assignment():
    # Arrange
    model = AttributesModel()

    # Act
    model.attributes = {"a": {"b": 1}}

    # Assert
    actual = model.attributes["a.b"]
    expected = 1
    assert actual == expected


def test_attributes_should_serialize_key_added_after_construction():
    # Arrange
    model = AttributesModel()
    model.attributes["seen"] = True
    model.attributes["cursor.page"] = 2

    # Act
    result = model.model_dump()

    # Assert
    actual = result["attributes"]
    expected = {"seen": True, "cursor": {"page": 2}}
    assert actual == expected


def test_attributes_should_serialize_key_added_before_construction():
    # Arrange
    model = AttributesModel(attributes={"a": 1})
    model.attributes["seen"] = True
    model.attributes["cursor.page"] = 2

    # Act
    result = model.model_dump()

    # Assert
    actual = result["attributes"]
    expected = {"a": 1, "seen": True, "cursor": {"page": 2}}
    assert actual == expected


# =============================================================================
# Bookmarks
# =============================================================================


def test_bookmarks_should_default_to_empty_dict_when_omitted():
    # Act
    result = BookmarksModel()

    # Assert
    actual = result.bookmarks
    expected = {}
    assert actual == expected


def test_bookmarks_should_default_to_empty_dict_when_none():
    # Act
    result = BookmarksModel(bookmarks=None)

    # Assert
    actual = result.bookmarks
    expected = {}
    assert actual == expected


def test_bookmarks_should_preserve_provided_mapping():
    # Act
    result = BookmarksModel(bookmarks={"k": "v", "n": 1})

    # Assert
    actual = result.bookmarks
    expected = {"k": "v", "n": 1}
    assert actual == expected


def test_bookmarks_should_not_mutate_provided_mapping():
    # Arrange
    source = {"k": "v"}
    model = BookmarksModel(bookmarks=source)

    # Act
    model.bookmarks["k2"] = "v2"

    # Assert
    actual = source
    expected = {"k": "v"}
    assert actual == expected


def test_bookmarks_should_not_share_default_between_instances():
    # Arrange
    first = BookmarksModel()
    second = BookmarksModel()

    # Act
    first.bookmarks["k"] = "v"

    # Assert
    actual = second.bookmarks
    expected = {}
    assert actual == expected


def test_bookmarks_should_convert_pairs_to_mapping():
    # Act
    result = BookmarksModel(bookmarks=(("a", 1), ("b", 2)))

    # Assert
    actual = result.bookmarks
    expected = {"a": 1, "b": 2}
    assert actual == expected


def test_bookmarks_should_support_keypath_access():
    # Act
    result = BookmarksModel(bookmarks={"a": {"b": 1}})

    # Assert
    actual = result.bookmarks["a.b"]
    expected = 1
    assert actual == expected


def test_bookmarks_should_support_keypath_access_on_assignment():
    # Arrange
    model = BookmarksModel()

    # Act
    model.bookmarks = {"a": {"b": 1}}

    # Assert
    actual = model.bookmarks["a.b"]
    expected = 1
    assert actual == expected


def test_bookmarks_should_serialize_key_added_after_construction():
    # Arrange
    model = BookmarksModel()
    model.bookmarks["seen"] = True
    model.bookmarks["cursor.page"] = 2

    # Act
    result = model.model_dump()

    # Assert
    actual = result["bookmarks"]
    expected = {"seen": True, "cursor": {"page": 2}}
    assert actual == expected


def test_bookmarks_should_serialize_key_added_before_construction():
    # Arrange
    model = BookmarksModel(bookmarks={"a": 1})
    model.bookmarks["seen"] = True
    model.bookmarks["cursor.page"] = 2

    # Act
    result = model.model_dump()

    # Assert
    actual = result["bookmarks"]
    expected = {"a": 1, "seen": True, "cursor": {"page": 2}}
    assert actual == expected


# =============================================================================
# Slug
# =============================================================================


def test_slug_should_normalize_non_slug_value():
    # Act
    result = SLUG.validate_python("My Job Name")

    # Assert
    actual = result
    expected = "my_job_name"
    assert actual == expected


def test_slug_should_preserve_already_safe_value():
    # Act
    result = SLUG.validate_python("my_job_name")

    # Assert
    actual = result
    expected = "my_job_name"
    assert actual == expected
