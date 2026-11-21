import pytest

from tiozin.api.metadata.schema.model import CustomProperty
from tiozin.exceptions import ModelError


def test_custom_property_should_hold_property_and_value():
    # Act
    result = CustomProperty(property="owner", value="sales")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"property": "owner", "value": "sales"}
    assert actual == expected


@pytest.mark.parametrize(
    "attributes",
    [
        {"value": "sales"},
        {"property": "owner"},
    ],
)
def test_custom_property_should_raise_model_error_when_required_attribute_is_missing(attributes):
    # Act / Assert
    with pytest.raises(ModelError):
        CustomProperty(**attributes)
