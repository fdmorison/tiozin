from unittest.mock import MagicMock

import pytest

from tiozin.api.metadata.schema.exceptions import SchemaNotFoundError
from tiozin.api.metadata.schema.model import Schema
from tiozin.api.metadata.schema.proxy import SchemaRegistryProxy
from tiozin.exceptions import RequiredArgumentError, TiozinInternalError

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


def test_get_should_retrieve_schema_by_auto_subject():
    # Arrange
    template = "{{org}}.{{region}}.{{domain}}"
    subject = "acme.eu.sales"
    schema = MagicMock(spec=Schema)

    wrapped_registry = MagicMock()
    wrapped_registry.subject_template = template
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = schema

    # Act
    SchemaRegistryProxy(wrapped_registry).get("auto")

    # Assert
    wrapped_registry.context.render.assert_called_with(template)


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


def test_get_should_raise_when_identifier_is_empty():
    # Arrange
    wrapped_registry = MagicMock()

    # Act
    with pytest.raises(RequiredArgumentError):
        SchemaRegistryProxy(wrapped_registry).get("")


def test_get_should_raise_when_identifier_is_none():
    # Arrange
    wrapped_registry = MagicMock()

    # Act
    with pytest.raises(RequiredArgumentError):
        SchemaRegistryProxy(wrapped_registry).get(None)


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
# SchemaRegistryProxy - register()
# ============================================================================


def test_register_should_send_schema_to_registry():
    # Arrange
    schema = MagicMock(spec=Schema)
    subject = "acme.eu.sales.orders.raw.crm.order"

    wrapped_registry = MagicMock()
    wrapped_registry.context.render.return_value = subject

    # Act
    SchemaRegistryProxy(wrapped_registry).register(subject, schema)

    # Assert
    wrapped_registry.register.assert_called_with(subject, schema)


def test_register_should_resolve_subject_when_auto():
    # Arrange
    template = "{{org}}.{{region}}.{{domain}}"
    subject = "acme.eu.sales"
    schema = MagicMock(spec=Schema)

    wrapped_registry = MagicMock()
    wrapped_registry.subject_template = template
    wrapped_registry.context.render.return_value = subject

    # Act
    SchemaRegistryProxy(wrapped_registry).register("auto", schema)

    # Assert
    wrapped_registry.context.render.assert_called_with(template)


def test_register_should_raise_when_identifier_is_empty():
    # Arrange
    schema = MagicMock(spec=Schema)
    wrapped_registry = MagicMock()

    # Act
    with pytest.raises(RequiredArgumentError):
        SchemaRegistryProxy(wrapped_registry).register("", schema)


def test_register_should_raise_when_identifier_is_none():
    # Arrange
    schema = MagicMock(spec=Schema)
    wrapped_registry = MagicMock()

    # Act
    with pytest.raises(RequiredArgumentError):
        SchemaRegistryProxy(wrapped_registry).register(None, schema)
