import pytest

from tiozin.api.metadata.schema.model import Relationship, RelationshipType
from tiozin.exceptions import ModelError


def test_relationship_should_default_type_to_foreign_key():
    # Act
    result = Relationship(to="customers.id")

    # Assert
    actual = result.type
    expected = "foreignKey"
    assert actual == expected


def test_relationship_should_parse_type_into_relationship_type():
    # Act
    result = Relationship(type="foreignKey", to="customers.id")

    # Assert
    assert result.type is RelationshipType.FOREIGN_KEY


def test_relationship_should_write_source_as_from():
    # Act
    result = Relationship(from_="orders.customer_id", to="customers.id")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"from": "orders.customer_id", "to": "customers.id"}
    assert actual == expected


def test_relationship_should_raise_model_error_when_to_is_missing():
    # Act / Assert
    with pytest.raises(ModelError):
        Relationship(from_="orders.customer_id")


def test_relationship_should_raise_model_error_when_type_is_unknown():
    # Act / Assert
    with pytest.raises(ModelError):
        Relationship(type="primaryKey", to="customers.id")
