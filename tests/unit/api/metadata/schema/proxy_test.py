from unittest.mock import MagicMock

import pytest

from tiozin.api.metadata.schema.exceptions import SchemaNotFoundError
from tiozin.api.metadata.schema.model import Schema
from tiozin.api.metadata.schema.proxy import SchemaRegistryProxy
from tiozin.exceptions import RequiredArgumentError, TiozinInternalError

# ============================================================================
# SchemaRegistryProxy - delegation
# ============================================================================


def test_proxy_should_delegate_get():
    # Arrange
    schema = MagicMock(spec=Schema)
    subject = "acme.eu.sales.orders.raw.crm.order"
    version = "v2"
    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = schema

    # Act
    SchemaRegistryProxy(wrapped_registry).get(subject, version)

    # Assert
    wrapped_registry.get.assert_called_with(subject, version)


def test_proxy_should_delegate_register():
    # Arrange
    schema = MagicMock(spec=Schema)
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
    schema = MagicMock(spec=Schema)
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
    schema = MagicMock(spec=Schema)
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


def test_get_should_retrieve_schema_by_default_registry_args():
    # Arrange
    template = "{{org}}.{{region}}.{{domain}}.{{subdomain}}.{{layer}}.{{product}}.{{model}}"
    subject = "acme.eu.sales.orders.raw.crm.order"
    version = "v2"

    schema = MagicMock(spec=Schema)
    wrapped_registry = MagicMock()
    wrapped_registry.subject_template = template
    wrapped_registry.default_version = version
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = schema

    # Act
    SchemaRegistryProxy(wrapped_registry).get()

    # Assert
    wrapped_registry.get.assert_called_with(subject, version)


def test_get_should_raise_when_schema_not_found():
    # Arrange
    subject = "missing-subject"

    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.side_effect = SchemaNotFoundError(subject)

    # Act
    with pytest.raises(SchemaNotFoundError):
        SchemaRegistryProxy(wrapped_registry).get(subject)


def test_get_should_raise_when_registry_returns_none():
    # Arrange
    subject = "acme.eu.sales.orders.raw.crm.order"

    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = None

    # Act
    with pytest.raises(SchemaNotFoundError):
        SchemaRegistryProxy(wrapped_registry).get(subject)


def test_get_should_raise_when_registry_returns_wrong_type():
    # Arrange
    subject = "acme.eu.sales.orders.raw.crm.order"

    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = "id INT, name STRING"

    # Act
    with pytest.raises(TiozinInternalError):
        SchemaRegistryProxy(wrapped_registry).get(subject)


def test_get_should_raise_when_no_identifier_and_no_subject_template():
    # Arrange
    wrapped_registry = MagicMock()
    wrapped_registry.subject_template = None

    # Act
    with pytest.raises(RequiredArgumentError):
        SchemaRegistryProxy(wrapped_registry).get()


def test_get_should_log_schema_when_show_schema_is_true():
    # Arrange
    schema = MagicMock(spec=Schema)
    schema.to_yaml.return_value = "name: orders\n"
    subject = "acme.eu.sales.orders.raw.crm.order"

    wrapped_registry = MagicMock()
    wrapped_registry.show_schema = True
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = schema

    # Act
    SchemaRegistryProxy(wrapped_registry).get(subject)

    # Assert
    actual = schema.to_yaml.called
    expected = True
    assert actual == expected


# ============================================================================
# SchemaRegistryProxy - try_get()
# ============================================================================


def test_try_get_should_retrieve_schema():
    # Arrange
    schema = MagicMock(spec=Schema)
    subject = "acme.eu.sales.orders.raw.crm.order"

    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = schema

    # Act
    result = SchemaRegistryProxy(wrapped_registry).try_get(subject)

    # Assert
    actual = result
    expected = schema
    assert actual == expected


def test_try_get_should_return_none_when_schema_not_found():
    # Arrange
    subject = "missing-subject"

    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.side_effect = SchemaNotFoundError(subject)

    # Act
    result = SchemaRegistryProxy(wrapped_registry).try_get(subject)

    # Assert
    actual = result
    expected = None
    assert actual == expected


def test_try_get_should_warn_when_schema_not_found():
    # Arrange
    subject = "missing-subject"

    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.side_effect = SchemaNotFoundError(subject)

    # Act
    SchemaRegistryProxy(wrapped_registry).try_get(subject)

    # Assert
    actual = wrapped_registry.warning.called
    expected = True
    assert actual == expected


def test_try_get_should_warn_when_registry_returns_none():
    # Arrange
    subject = "acme.eu.sales.orders.raw.crm.order"

    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = None

    # Act
    SchemaRegistryProxy(wrapped_registry).try_get(subject)

    # Assert
    actual = wrapped_registry.warning.called
    expected = True
    assert actual == expected
