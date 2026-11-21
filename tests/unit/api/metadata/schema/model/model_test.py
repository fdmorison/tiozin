import pytest

from tiozin.api.metadata.schema.model import CustomProperty, Property, Schema
from tiozin.exceptions import ModelError


@pytest.mark.parametrize(
    "model, attributes",
    [
        (Schema, {"name": "orders"}),
        (Property, {"name": "id"}),
        (CustomProperty, {"property": "owner", "value": "sales"}),
    ],
    ids=["schema", "property", "custom_property"],
)
def test_model_should_raise_model_error_when_attribute_is_unknown(model, attributes):
    # Act / Assert
    with pytest.raises(ModelError, match="Field `colour` is not allowed"):
        model(**attributes, colour="blue")
