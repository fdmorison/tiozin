from unittest.mock import MagicMock, patch

import pytest

from tiozin.api.metadata.schema.exceptions import SchemaNotFoundError
from tiozin.api.metadata.schema.proxy import SchemaRegistryProxy

# ============================================================================
# SchemaRegistryProxy - delegation
# ============================================================================


def test_proxy_should_delegate_get():
    # Arrange
    subject = "acme.eu.sales.orders.raw.crm.order"
    version = "v2"
    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject

    # Act
    SchemaRegistryProxy(wrapped_registry).get(subject, version)

    # Assert
    wrapped_registry.get.assert_called_with(subject, version)


def test_proxy_should_delegate_register():
    # Arrange
    schema = "id INT, name STRING"
    subject = "acme.eu.sales.orders.raw.crm.order"
    wrapped_registry = MagicMock()

    # Act
    SchemaRegistryProxy(wrapped_registry).register(subject, schema)

    # Assert
    wrapped_registry.register.assert_called_with(subject, schema)


def test_proxy_should_delegate_attribute_access():
    # Arrange
    location = "schema://test-registry"
    wrapped_registry = MagicMock(location=location)

    # Act
    result = SchemaRegistryProxy(wrapped_registry).location

    # Assert
    actual = result
    expected = location
    assert actual == expected


# ============================================================================
# SchemaRegistryProxy - get()
# ============================================================================


def test_get_should_retrieve_schema():
    # Arrange
    schema = "id INT, name STRING"
    subject = "acme.eu.sales.orders.raw.crm.order"

    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = schema

    # Act
    result = SchemaRegistryProxy(wrapped_registry).get(subject)

    # Assert
    actual = result
    expected = schema
    assert actual == expected


def test_get_should_retrieve_schema_by_version():
    # Arrange
    schema = "id INT, name STRING"
    subject = "acme.eu.sales.orders.raw.crm.order"
    version = "v2"

    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = schema

    # Act
    result = SchemaRegistryProxy(wrapped_registry).get(subject, version)

    # Assert
    actual = result
    expected = schema
    assert actual == expected


@pytest.mark.parametrize("args", [(), (None, None)])
def test_get_should_retrieve_schema_by_default_parameters(args):
    # Arrange
    template = "{{org}}.{{region}}.{{domain}}.{{subdomain}}.{{layer}}.{{product}}.{{model}}"
    subject = "acme.eu.sales.orders.raw.crm.order"
    version = "latest"

    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject

    # Act
    with patch("tiozin.api.metadata.schema.proxy.DEFAULT_SUBJECT_TEMPLATE", template):
        SchemaRegistryProxy(wrapped_registry).get(*args)

    # Assert
    wrapped_registry.get.assert_called_with(subject, version)


def test_get_should_not_raise_when_schema_not_found():
    # Arrange
    subject = "missing-subject"

    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.side_effect = SchemaNotFoundError(subject)

    # Act
    result = SchemaRegistryProxy(wrapped_registry).get(subject)

    # Assert
    actual = result
    expected = None
    assert actual == expected
