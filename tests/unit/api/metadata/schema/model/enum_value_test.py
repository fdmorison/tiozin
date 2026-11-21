import pytest

from tiozin.api.metadata.schema.model import EnumValue
from tiozin.exceptions import ModelError


def test_enum_value_should_hold_value():
    # Act
    result = EnumValue(value="open")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"value": "open"}
    assert actual == expected


def test_enum_value_should_raise_model_error_when_value_is_missing():
    # Act / Assert
    with pytest.raises(ModelError):
        EnumValue()
