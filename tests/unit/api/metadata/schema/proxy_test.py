from unittest.mock import MagicMock, call

import pytest

from tiozin import Schema
from tiozin.api.metadata.schema.exceptions import SchemaNotFoundError
from tiozin.api.metadata.schema.proxy import SchemaRegistryProxy
from tiozin.exceptions import RequiredArgumentError

# ============================================================================
# SchemaRegistryProxy - get()
# ============================================================================


def test_get_should_retrieve_schema():
    # Arrange
    schema = Schema(name="orders").string("id")
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
    schema = Schema(name="orders").string("id")
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
    schema = Schema(name="orders").string("id")

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
    schema = Schema(name="orders").string("id").object("customer").string("customer.name")
    subject = "acme.eu.sales.orders.raw.crm.order"

    wrapped_registry = MagicMock()
    wrapped_registry.show_schema = True
    wrapped_registry.context.name = "read_orders"
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = schema

    # Act
    SchemaRegistryProxy(wrapped_registry).get(subject)

    # Assert
    actual = wrapped_registry.info.call_args
    expected = call("📄 `read_orders` received schema `orders` with 3 properties")
    assert actual == expected


def test_get_should_log_subject_as_schema_name_when_schema_has_no_name():
    # Arrange
    schema = Schema().string("id")
    subject = "acme.eu.sales.orders.raw.crm.order"

    wrapped_registry = MagicMock()
    wrapped_registry.show_schema = True
    wrapped_registry.context.name = "read_orders"
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = schema

    # Act
    SchemaRegistryProxy(wrapped_registry).get(subject)

    # Assert
    actual = wrapped_registry.info.call_args
    expected = call(
        "📄 `read_orders` received schema `acme.eu.sales.orders.raw.crm.order` with 1 properties"
    )
    assert actual == expected


def test_get_should_show_schema_when_show_schema_is_true(capsys):
    # Arrange
    schema = Schema(name="orders").string("id").object("customer").string("customer.name")
    subject = "acme.eu.sales.orders.raw.crm.order"

    wrapped_registry = MagicMock()
    wrapped_registry.show_schema = True
    wrapped_registry.context.name = "read_orders"
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = schema

    # Act
    SchemaRegistryProxy(wrapped_registry).get(subject)

    # Assert
    actual = capsys.readouterr().out
    expected = (
        "name: orders\n"
        "properties:\n"
        "- name: id\n"
        "  logicalType: string\n"
        "- name: customer\n"
        "  logicalType: object\n"
        "  properties:\n"
        "  - name: name\n"
        "    logicalType: string\n"
        "\n"
    )
    assert actual == expected


def test_get_should_not_log_schema_when_show_schema_is_false():
    # Arrange
    schema = Schema(name="orders").string("id")
    subject = "acme.eu.sales.orders.raw.crm.order"

    wrapped_registry = MagicMock()
    wrapped_registry.show_schema = False
    wrapped_registry.context.name = "read_orders"
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = schema

    # Act
    SchemaRegistryProxy(wrapped_registry).get(subject)

    # Assert
    actual = wrapped_registry.info.call_args_list
    expected = [
        call("🔍 `read_orders` requested schema `acme.eu.sales.orders.raw.crm.order`"),
    ]
    assert actual == expected


def test_get_should_not_show_schema_when_show_schema_is_false(capsys):
    # Arrange
    schema = Schema(name="orders").string("id")
    subject = "acme.eu.sales.orders.raw.crm.order"

    wrapped_registry = MagicMock()
    wrapped_registry.show_schema = False
    wrapped_registry.context.name = "read_orders"
    wrapped_registry.context.render.return_value = subject
    wrapped_registry.get.return_value = schema

    # Act
    SchemaRegistryProxy(wrapped_registry).get(subject)

    # Assert
    actual = capsys.readouterr().out
    expected = ""
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
