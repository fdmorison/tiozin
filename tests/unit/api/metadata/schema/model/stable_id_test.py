import pytest

from tiozin.api.metadata.schema.model import (
    AuthoritativeDefinition,
    CustomProperty,
    Element,
    EnumValue,
    Quality,
    Synonym,
)
from tiozin.exceptions import ModelError


def test_stable_id_should_accept_letters_digits_underscores_and_hyphens():
    # Act
    result = Element(id="Order_line-01")

    # Assert
    actual = result.id
    expected = "Order_line-01"
    assert actual == expected


@pytest.mark.parametrize(
    "model, attributes",
    [
        (Element, {}),
        (CustomProperty, {"property": "owner", "value": "sales"}),
        (Synonym, {"synonym": "purchases"}),
        (EnumValue, {"value": "open"}),
        (Quality, {"description": "Orders are never empty"}),
        (AuthoritativeDefinition, {"url": "https://example.com/orders", "type": "glossary"}),
    ],
    ids=[
        "element",
        "custom_property",
        "synonym",
        "enum_value",
        "quality",
        "authoritative_definition",
    ],
)
@pytest.mark.parametrize("stable_id", ["order.line", "order line", "order@line"])
def test_stable_id_should_raise_model_error_when_id_has_other_characters(
    model, attributes, stable_id
):
    # Act / Assert
    with pytest.raises(ModelError):
        model(**attributes, id=stable_id)
