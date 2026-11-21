import pytest

from tiozin.api.metadata.schema.model import AuthoritativeDefinition
from tiozin.exceptions import ModelError


def test_authoritative_definition_should_hold_url_and_type():
    # Act
    result = AuthoritativeDefinition(url="https://example.com/orders", type="glossary")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"url": "https://example.com/orders", "type": "glossary"}
    assert actual == expected


@pytest.mark.parametrize(
    "attributes",
    [
        {"type": "glossary"},
        {"url": "https://example.com/orders"},
    ],
)
def test_authoritative_definition_should_raise_model_error_when_required_attribute_is_missing(
    attributes,
):
    # Act / Assert
    with pytest.raises(ModelError):
        AuthoritativeDefinition(**attributes)
