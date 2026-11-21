import pytest

from tiozin.api.metadata.schema.converters.avro.named_types import (
    full_name,
    inline_named_types,
    reference_named_types,
)
from tiozin.exceptions import SchemaError


def test_full_name_should_return_name_without_namespace():
    # Act
    result = full_name({"name": "User"})

    # Assert
    actual = result
    expected = "User"
    assert actual == expected


@pytest.mark.parametrize(
    "named_type, namespace, expected",
    [
        ({"name": "User"}, "com.acme", "com.acme.User"),
        ({"name": "User", "namespace": "com.geo"}, "com.acme", "com.geo.User"),
        ({"name": "geo.User"}, "com.acme", "geo.User"),
    ],
    ids=["enclosing_namespace", "own_namespace_wins", "dotted_name_is_full"],
)
def test_full_name_should_qualify_name_with_namespace(named_type, namespace, expected):
    # Act
    result = full_name(named_type, namespace)

    # Assert
    actual = result
    assert actual == expected


def test_inline_named_types_should_replace_reference_with_definition():
    # Arrange
    avro_type = {
        "type": "record",
        "name": "User",
        "fields": [
            {"name": "status", "type": {"type": "enum", "name": "Status", "symbols": ["A"]}},
            {"name": "old_status", "type": "Status"},
        ],
    }

    # Act
    result = inline_named_types(avro_type)

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "User",
        "fields": [
            {"name": "status", "type": {"type": "enum", "name": "Status", "symbols": ["A"]}},
            {"name": "old_status", "type": {"type": "enum", "name": "Status", "symbols": ["A"]}},
        ],
    }
    assert actual == expected


def test_inline_named_types_should_preserve_types_without_references():
    # Arrange
    avro_type = {"type": "array", "items": ["null", "long"]}

    # Act
    result = inline_named_types(avro_type)

    # Assert
    actual = result
    expected = {"type": "array", "items": ["null", "long"]}
    assert actual == expected


@pytest.mark.parametrize(
    "reference, expected",
    [
        (
            "Address",
            {"type": "record", "name": "Address", "fields": [{"name": "city", "type": "string"}]},
        ),
        (
            "com.acme.Address",
            {"type": "record", "name": "Address", "fields": [{"name": "city", "type": "string"}]},
        ),
        (
            ["null", "Address"],
            [
                "null",
                {
                    "type": "record",
                    "name": "Address",
                    "fields": [{"name": "city", "type": "string"}],
                },
            ],
        ),
        (
            {"type": "array", "items": "Address"},
            {
                "type": "array",
                "items": {
                    "type": "record",
                    "name": "Address",
                    "fields": [{"name": "city", "type": "string"}],
                },
            },
        ),
        (
            {"type": "map", "values": "Address"},
            {
                "type": "map",
                "values": {
                    "type": "record",
                    "name": "Address",
                    "fields": [{"name": "city", "type": "string"}],
                },
            },
        ),
    ],
    ids=["simple_name", "full_name", "union", "array_items", "map_values"],
)
def test_inline_named_types_should_resolve_reference_inside_namespace(reference, expected):
    # Arrange
    avro_type = {
        "type": "record",
        "name": "User",
        "namespace": "com.acme",
        "fields": [
            {
                "name": "home",
                "type": {
                    "type": "record",
                    "name": "Address",
                    "fields": [{"name": "city", "type": "string"}],
                },
            },
            {"name": "work", "type": reference},
        ],
    }

    # Act
    result = inline_named_types(avro_type)

    # Assert
    actual = result["fields"][1]["type"]
    assert actual == expected


def test_inline_named_types_should_raise_schema_error_when_name_is_unknown():
    # Arrange
    avro_type = {"type": "record", "name": "User", "fields": [{"name": "home", "type": "Address"}]}

    # Act / Assert
    with pytest.raises(SchemaError, match="Unsupported Avro type `Address`"):
        inline_named_types(avro_type)


def test_inline_named_types_should_raise_schema_error_when_type_refers_to_itself():
    # Arrange
    avro_type = {
        "type": "record",
        "name": "Node",
        "fields": [{"name": "next", "type": ["null", "Node"], "default": None}],
    }

    # Act / Assert
    with pytest.raises(
        SchemaError,
        match="Avro type `Node` refers to itself, which a schema cannot represent",
    ):
        inline_named_types(avro_type)


def test_reference_named_types_should_refer_to_repeated_type_by_name():
    # Arrange
    avro_type = {
        "type": "record",
        "name": "User",
        "fields": [
            {
                "name": "home",
                "type": {
                    "type": "record",
                    "name": "Address",
                    "fields": [{"name": "city", "type": "string"}],
                },
            },
            {
                "name": "work",
                "type": {
                    "type": "record",
                    "name": "Address",
                    "fields": [{"name": "city", "type": "string"}],
                },
            },
        ],
    }

    # Act
    result = reference_named_types(avro_type)

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "User",
        "fields": [
            {
                "name": "home",
                "type": {
                    "type": "record",
                    "name": "Address",
                    "fields": [{"name": "city", "type": "string"}],
                },
            },
            {"name": "work", "type": "Address"},
        ],
    }
    assert actual == expected


def test_reference_named_types_should_preserve_types_defined_once():
    # Arrange
    avro_type = {"type": "array", "items": {"type": "enum", "name": "Status", "symbols": ["A"]}}

    # Act
    result = reference_named_types(avro_type)

    # Assert
    actual = result
    expected = {"type": "array", "items": {"type": "enum", "name": "Status", "symbols": ["A"]}}
    assert actual == expected


def test_reference_named_types_should_refer_by_full_name_from_other_namespace():
    # Arrange
    avro_type = {
        "type": "record",
        "name": "User",
        "namespace": "com.acme",
        "fields": [
            {
                "name": "home",
                "type": {
                    "type": "record",
                    "name": "Address",
                    "namespace": "com.acme.geo",
                    "fields": [{"name": "city", "type": "string"}],
                },
            },
            {
                "name": "work",
                "type": [
                    "null",
                    {
                        "type": "record",
                        "name": "Address",
                        "namespace": "com.acme.geo",
                        "fields": [{"name": "city", "type": "string"}],
                    },
                ],
            },
        ],
    }

    # Act
    result = reference_named_types(avro_type)

    # Assert
    actual = result["fields"][1]["type"]
    expected = ["null", "com.acme.geo.Address"]
    assert actual == expected


def test_reference_named_types_should_raise_schema_error_when_definitions_differ():
    # Arrange
    avro_type = {
        "type": "record",
        "name": "User",
        "fields": [
            {
                "name": "home",
                "type": {
                    "type": "record",
                    "name": "Address",
                    "fields": [{"name": "city", "type": "string"}],
                },
            },
            {
                "name": "work",
                "type": {
                    "type": "record",
                    "name": "Address",
                    "fields": [{"name": "street", "type": "string"}],
                },
            },
        ],
    }

    # Act / Assert
    with pytest.raises(SchemaError, match="Avro types named `Address` have different definitions"):
        reference_named_types(avro_type)
