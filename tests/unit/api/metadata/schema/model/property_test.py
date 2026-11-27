import pytest

from tiozin.api.metadata.schema.model import (
    ArrayOptions,
    Case,
    DateOptions,
    IntegerOptions,
    LogicalType,
    Map,
    NumberOptions,
    ObjectOptions,
    Property,
    SemanticType,
    StringOptions,
    TimestampOptions,
    VectorOptions,
)
from tiozin.exceptions import ModelError, PropertyNotFoundError, SchemaError


def test_effective_type_should_return_logical_type():
    # Arrange
    prop = Property(name="age", logicalType="integer")

    # Act
    result = prop.effective_type()

    # Assert
    actual = result
    expected = "integer"
    assert actual == expected


@pytest.mark.parametrize(
    "prop, expected",
    [
        (Property(name="tags", items=Property(logicalType="string")), "array"),
        (
            Property(
                name="attributes",
                map=Map(key=Property(logicalType="string"), value=Property(logicalType="string")),
            ),
            "map",
        ),
        (Property(name="profile", properties=[]), "object"),
    ],
)
def test_effective_type_should_infer_type_from_structure(prop, expected):
    # Act
    result = prop.effective_type()

    # Assert
    actual = result
    assert actual == expected


def test_effective_type_should_return_none_when_property_has_no_type():
    # Arrange
    prop = Property(name="anything")

    # Act
    result = prop.effective_type()

    # Assert
    assert result is None


@pytest.mark.parametrize(
    "prop",
    [
        Property(name="profile", logicalType="object"),
        Property(name="friends", logicalType="array", items=Property(logicalType="object")),
        Property(
            name="attributes",
            logicalType="map",
            map=Map(key=Property(logicalType="string"), value=Property(logicalType="object")),
        ),
    ],
)
def test_is_composite_should_pass_when_property_holds_objects(prop):
    # Act / Assert
    assert prop.is_composite()


@pytest.mark.parametrize(
    "prop",
    [
        Property(name="name", logicalType="string"),
        Property(name="tags", logicalType="array", items=Property(logicalType="string")),
    ],
)
def test_is_composite_should_not_pass_when_property_holds_no_objects(prop):
    # Act / Assert
    assert not prop.is_composite()


def test_children_should_return_nested_properties():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[
            Property(name="age", logicalType="integer"),
            Property(name="city", logicalType="string"),
        ],
    )

    # Act
    result = prop.children()

    # Assert
    actual = [child.name for child in result]
    expected = ["age", "city"]
    assert actual == expected


def test_children_should_be_empty_when_property_is_not_nested():
    # Arrange
    prop = Property(name="name", logicalType="string")

    # Act
    result = prop.children()

    # Assert
    actual = result
    expected = []
    assert actual == expected


def test_children_should_go_through_arrays():
    # Arrange
    prop = Property(
        name="friends",
        logicalType="array",
        items=Property(
            logicalType="object",
            properties=[Property(name="name", logicalType="string")],
        ),
    )

    # Act
    result = prop.children()

    # Assert
    actual = [child.name for child in result]
    expected = ["name"]
    assert actual == expected


def test_children_should_go_through_maps():
    # Arrange
    prop = Property(
        name="attributes",
        logicalType="map",
        map=Map(
            key=Property(logicalType="string"),
            value=Property(
                logicalType="object",
                properties=[Property(name="color", logicalType="string")],
            ),
        ),
    )

    # Act
    result = prop.children()

    # Assert
    actual = [child.name for child in result]
    expected = ["color"]
    assert actual == expected


def test_child_should_return_child_by_name():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[Property(name="age", logicalType="integer")],
    )

    # Act
    result = prop.child("age")

    # Assert
    actual = result.logicalType
    expected = "integer"
    assert actual == expected


def test_child_should_ignore_case():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[Property(name="Age", logicalType="integer")],
    )

    # Act
    result = prop.child("AGE")

    # Assert
    actual = result.name
    expected = "Age"
    assert actual == expected


def test_child_should_return_none_when_child_does_not_exist():
    # Arrange
    prop = Property(name="profile", logicalType="object", properties=[])

    # Act
    result = prop.child("age")

    # Assert
    assert result is None


def test_getitem_should_return_property_at_path():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[
            Property(
                name="address",
                logicalType="object",
                properties=[Property(name="city", logicalType="string")],
            )
        ],
    )

    # Act
    result = prop["address.city"]

    # Assert
    actual = result.name
    expected = "city"
    assert actual == expected


def test_getitem_should_accept_sequence_of_names():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[
            Property(
                name="address",
                logicalType="object",
                properties=[Property(name="city", logicalType="string")],
            )
        ],
    )

    # Act
    result = prop[["address", "city"]]

    # Assert
    actual = result.name
    expected = "city"
    assert actual == expected


def test_getitem_should_raise_property_not_found_when_path_does_not_exist():
    # Arrange
    prop = Property(name="profile", logicalType="object", properties=[])

    # Act / Assert
    with pytest.raises(PropertyNotFoundError, match="Property `address.city` not found."):
        prop["address.city"]


def test_contains_should_pass_when_path_exists():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[Property(name="age", logicalType="integer")],
    )

    # Act / Assert
    assert "AGE" in prop


def test_contains_should_not_pass_when_path_does_not_exist():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[Property(name="age", logicalType="integer")],
    )

    # Act / Assert
    assert "age.years" not in prop


def test_add_should_append_child():
    # Arrange
    prop = Property(name="profile", logicalType="object")

    # Act
    prop.add(Property(name="age", logicalType="integer"))

    # Assert
    actual = [child.name for child in prop.children()]
    expected = ["age"]
    assert actual == expected


def test_add_should_return_same_property():
    # Arrange
    prop = Property(name="profile", logicalType="object")

    # Act
    result = prop.add(Property(name="age", logicalType="integer"))

    # Assert
    assert result is prop


def test_add_should_add_child_to_array_elements():
    # Arrange
    prop = Property(name="friends", logicalType="array", items=Property(logicalType="object"))

    # Act
    prop.add(Property(name="name", logicalType="string"))

    # Assert
    actual = [child.name for child in prop.items.properties]
    expected = ["name"]
    assert actual == expected


def test_add_should_add_child_to_map_values():
    # Arrange
    prop = Property(
        name="attributes",
        logicalType="map",
        map=Map(key=Property(logicalType="string"), value=Property(logicalType="object")),
    )

    # Act
    prop.add(Property(name="color", logicalType="string"))

    # Assert
    actual = [child.name for child in prop.map.value.properties]
    expected = ["color"]
    assert actual == expected


def test_add_should_raise_schema_error_when_property_cannot_hold_children():
    # Arrange
    prop = Property(name="name", logicalType="string")

    # Act / Assert
    with pytest.raises(SchemaError):
        prop.add(Property(name="first", logicalType="string"))


def test_add_should_raise_schema_error_when_name_exists_ignoring_case():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[Property(name="age", logicalType="integer")],
    )

    # Act / Assert
    with pytest.raises(SchemaError):
        prop.add(Property(name="AGE", logicalType="string"))


def test_remove_should_remove_child():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[
            Property(name="age", logicalType="integer"),
            Property(name="city", logicalType="string"),
        ],
    )

    # Act
    prop.remove("age")

    # Assert
    actual = [child.name for child in prop.children()]
    expected = ["city"]
    assert actual == expected


def test_remove_should_return_same_property():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[Property(name="age", logicalType="integer")],
    )

    # Act
    result = prop.remove("age")

    # Assert
    assert result is prop


def test_remove_should_ignore_case():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[Property(name="Age", logicalType="integer")],
    )

    # Act
    prop.remove("AGE")

    # Assert
    actual = prop.children()
    expected = []
    assert actual == expected


def test_remove_should_remove_child_of_array_elements():
    # Arrange
    prop = Property(
        name="friends",
        logicalType="array",
        items=Property(
            logicalType="object",
            properties=[
                Property(name="name", logicalType="string"),
                Property(name="email", logicalType="string"),
            ],
        ),
    )

    # Act
    prop.remove("email")

    # Assert
    actual = [child.name for child in prop.items.properties]
    expected = ["name"]
    assert actual == expected


def test_remove_should_raise_property_not_found_when_child_does_not_exist():
    # Arrange
    prop = Property(name="profile", logicalType="object", properties=[])

    # Act / Assert
    with pytest.raises(PropertyNotFoundError):
        prop.remove("age")


def test_rename_should_change_name():
    # Arrange
    prop = Property(name="age", logicalType="integer")

    # Act
    result = prop.rename("years")

    # Assert
    actual = (
        result is prop,
        prop.name,
    )
    expected = (
        True,
        "years",
    )
    assert actual == expected


def test_clone_should_copy_property():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[Property(name="age", logicalType="integer")],
    )

    # Act
    result = prop.clone()

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "profile",
        "logicalType": "object",
        "properties": [{"name": "age", "logicalType": "integer"}],
    }
    assert actual == expected


def test_clone_should_be_independent_from_original():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[Property(name="age", logicalType="integer")],
    )

    # Act
    result = prop.clone()
    result.remove("age")

    # Assert
    actual = list(prop.flatten())
    expected = ["age"]
    assert actual == expected


def test_cast_should_change_logical_type():
    # Arrange
    prop = Property(name="age", logicalType="integer")

    # Act
    result = prop.cast("string")

    # Assert
    actual = (
        result is prop,
        prop.logicalType,
    )
    expected = (
        True,
        "string",
    )
    assert actual == expected


def test_cast_should_drop_physical_type():
    # Arrange
    prop = Property(name="age", logicalType="integer", physicalType="int")

    # Act
    prop.cast("string")

    # Assert
    actual = prop.model_dump(exclude_unset=True)
    expected = {"name": "age", "logicalType": "string"}
    assert actual == expected


def test_cast_should_store_logical_type_value():
    # Arrange
    prop = Property(name="age", logicalType="integer")

    # Act
    result = prop.cast("string")

    # Assert
    assert result.logicalType is LogicalType.STRING


def test_cast_should_raise_schema_error_when_logical_type_is_unknown():
    # Arrange
    prop = Property(name="age", logicalType="integer")

    # Act / Assert
    with pytest.raises(SchemaError):
        prop.cast("varchar")


def test_retype_should_change_type():
    # Arrange
    prop = Property(name="active", logicalType="string")

    # Act
    result = prop.retype("boolean")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"name": "active", "logicalType": "boolean"}
    assert actual == expected


def test_retype_should_return_same_property():
    # Arrange
    prop = Property(name="active", logicalType="string")

    # Act
    result = prop.retype("boolean")

    # Assert
    assert result is prop


def test_retype_should_drop_physical_type():
    # Arrange
    prop = Property(name="age", logicalType="integer", physicalType="int")

    # Act
    result = prop.retype("string")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"name": "age", "logicalType": "string"}
    assert actual == expected


def test_retype_should_drop_type_options():
    # Arrange
    prop = Property(name="code", logicalType="string", logicalTypeOptions={"maxLength": 3})

    # Act
    result = prop.retype("string")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"name": "code", "logicalType": "string"}
    assert actual == expected


def test_retype_should_drop_conventions():
    # Arrange
    prop = Property(name="hash", logicalType="string", binary=True, typeSize=16)

    # Act
    result = prop.retype("string")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"name": "hash", "logicalType": "string"}
    assert actual == expected


def test_retype_should_drop_nested_properties():
    # Arrange
    prop = Property(
        name="address",
        logicalType="object",
        properties=[Property(name="city", logicalType="string")],
    )

    # Act
    result = prop.retype("string")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"name": "address", "logicalType": "string"}
    assert actual == expected


def test_retype_should_drop_items():
    # Arrange
    prop = Property(
        name="tags",
        logicalType="array",
        items=Property(logicalType="string"),
    )

    # Act
    result = prop.retype("string")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"name": "tags", "logicalType": "string"}
    assert actual == expected


def test_retype_should_drop_map():
    # Arrange
    prop = Property(
        name="labels",
        logicalType="map",
        map=Map(key=Property(logicalType="string"), value=Property(logicalType="string")),
    )

    # Act
    result = prop.retype("string")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"name": "labels", "logicalType": "string"}
    assert actual == expected


def test_retype_should_drop_vendor_custom_property():
    # Arrange
    prop = Property(
        name="email",
        logicalType="string",
        customProperties=[{"property": "avro.java.string", "value": "String", "vendor": "avro"}],
    )

    # Act
    result = prop.retype("string")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"name": "email", "logicalType": "string"}
    assert actual == expected


def test_retype_should_drop_default():
    # Arrange
    prop = Property(
        name="score",
        logicalType="integer",
        customProperties=[{"property": "default", "value": 0}],
    )

    # Act
    result = prop.retype("string")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"name": "score", "logicalType": "string"}
    assert actual == expected


def test_retype_should_keep_documentation():
    # Arrange
    prop = Property(
        name="id",
        logicalType="string",
        description="User id",
        examples=["42"],
    )

    # Act
    result = prop.retype("boolean")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "id",
        "logicalType": "boolean",
        "description": "User id",
        "examples": ["42"],
    }
    assert actual == expected


def test_retype_should_keep_constraints():
    # Arrange
    prop = Property(
        name="id",
        logicalType="string",
        required=True,
        unique=True,
        primaryKey=True,
    )

    # Act
    result = prop.retype("boolean")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "id",
        "logicalType": "boolean",
        "required": True,
        "unique": True,
        "primaryKey": True,
    }
    assert actual == expected


def test_retype_should_keep_custom_property_without_vendor():
    # Arrange
    prop = Property(
        name="id",
        logicalType="integer",
        customProperties=[{"property": "order", "value": "descending"}],
    )

    # Act
    result = prop.retype("string")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "id",
        "logicalType": "string",
        "customProperties": [{"property": "order", "value": "descending"}],
    }
    assert actual == expected


def test_retype_should_keep_type_name_with_namespace():
    # Arrange
    prop = Property(
        name="status",
        logicalType="integer",
        typeName="Status",
        namespace="com.acme",
    )

    # Act
    result = prop.retype("string")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "status",
        "logicalType": "string",
        "customProperties": [
            {"property": "typeName", "value": "Status"},
            {"property": "namespace", "value": "com.acme"},
        ],
    }
    assert actual == expected


def test_to_integer_should_write_i64_format():
    # Arrange
    prop = Property(name="age", logicalType="string")

    # Act
    result = prop.to_integer()

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "age",
        "logicalType": "integer",
        "logicalTypeOptions": {"format": "i64"},
    }
    assert actual == expected


def test_to_number_should_write_f64_format():
    # Arrange
    prop = Property(name="score", logicalType="string")

    # Act
    result = prop.to_number()

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "score",
        "logicalType": "number",
        "logicalTypeOptions": {"format": "f64"},
    }
    assert actual == expected


def test_to_time_should_write_micros():
    # Arrange
    prop = Property(name="opens_at", logicalType="string")

    # Act
    result = prop.to_time()

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "opens_at",
        "logicalType": "time",
        "customProperties": [{"property": "timeUnit", "value": "micros"}],
    }
    assert actual == expected


def test_to_timestamp_should_write_micros_with_timezone():
    # Arrange
    prop = Property(name="created_at", logicalType="string")

    # Act
    result = prop.to_timestamp()

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "created_at",
        "logicalType": "timestamp",
        "logicalTypeOptions": {"timezone": True},
        "customProperties": [{"property": "timeUnit", "value": "micros"}],
    }
    assert actual == expected


def test_to_timestamp_ntz_should_write_micros_without_timezone():
    # Arrange
    prop = Property(name="created_at", logicalType="string")

    # Act
    result = prop.to_timestamp_ntz()

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "created_at",
        "logicalType": "timestamp",
        "logicalTypeOptions": {"timezone": False},
        "customProperties": [{"property": "timeUnit", "value": "micros"}],
    }
    assert actual == expected


def test_to_decimal_should_default_to_ten_digits_without_scale():
    # Arrange
    prop = Property(name="price", logicalType="string")

    # Act
    result = prop.to_decimal()

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "price",
        "logicalType": "number",
        "customProperties": [
            {"property": "precision", "value": 10},
            {"property": "scale", "value": 0},
        ],
    }
    assert actual == expected


def test_to_decimal_should_write_given_digits():
    # Arrange
    prop = Property(name="price", logicalType="string")

    # Act
    result = prop.to_decimal(precision=12, scale=2)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "price",
        "logicalType": "number",
        "customProperties": [
            {"property": "precision", "value": 12},
            {"property": "scale", "value": 2},
        ],
    }
    assert actual == expected


def test_to_object_should_start_without_properties():
    # Arrange
    prop = Property(name="address", logicalType="string")

    # Act
    result = prop.to_object()

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"name": "address", "logicalType": "object", "properties": []}
    assert actual == expected


def test_to_array_should_default_items_to_string():
    # Arrange
    prop = Property(name="tags", logicalType="string")

    # Act
    result = prop.to_array()

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "tags",
        "logicalType": "array",
        "items": {"logicalType": "string"},
    }
    assert actual == expected


def test_to_array_should_retype_items_to_given_type():
    # Arrange
    prop = Property(name="scores", logicalType="string")

    # Act
    result = prop.to_array(of="int32")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "scores",
        "logicalType": "array",
        "items": {"logicalType": "integer", "logicalTypeOptions": {"format": "i32"}},
    }
    assert actual == expected


def test_to_map_should_default_entries_to_string():
    # Arrange
    prop = Property(name="labels", logicalType="string")

    # Act
    result = prop.to_map()

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "labels",
        "logicalType": "map",
        "map": {
            "key": {"logicalType": "string"},
            "value": {"logicalType": "string"},
        },
    }
    assert actual == expected


def test_to_map_should_retype_keys_to_given_type():
    # Arrange
    prop = Property(name="labels", logicalType="string")

    # Act
    result = prop.to_map(key="int32")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "labels",
        "logicalType": "map",
        "map": {
            "key": {"logicalType": "integer", "logicalTypeOptions": {"format": "i32"}},
            "value": {"logicalType": "string"},
        },
    }
    assert actual == expected


def test_to_map_should_retype_values_to_given_type():
    # Arrange
    prop = Property(name="labels", logicalType="string")

    # Act
    result = prop.to_map(value="int32")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "labels",
        "logicalType": "map",
        "map": {
            "key": {"logicalType": "string"},
            "value": {"logicalType": "integer", "logicalTypeOptions": {"format": "i32"}},
        },
    }
    assert actual == expected


def test_retype_should_accept_tiozin_logical_type():
    # Arrange
    prop = Property(name="age", logicalType="string")

    # Act
    result = prop.retype("int32")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "age",
        "logicalType": "integer",
        "logicalTypeOptions": {"format": "i32"},
    }
    assert actual == expected


def test_retype_should_turn_number_into_decimal_when_precision_is_given():
    # Arrange
    prop = Property(name="price", logicalType="string")

    # Act
    result = prop.retype("number", precision=12)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "price",
        "logicalType": "number",
        "customProperties": [
            {"property": "precision", "value": 12},
            {"property": "scale", "value": 0},
        ],
    }
    assert actual == expected


def test_retype_should_turn_number_into_decimal_when_scale_is_given():
    # Arrange
    prop = Property(name="price", logicalType="string")

    # Act
    result = prop.retype("number", scale=2)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "price",
        "logicalType": "number",
        "customProperties": [
            {"property": "precision", "value": 10},
            {"property": "scale", "value": 2},
        ],
    }
    assert actual == expected


def test_retype_should_turn_varchar_into_unbounded_string_when_length_is_not_given():
    # Arrange
    prop = Property(name="code", logicalType="integer")

    # Act
    result = prop.retype("varchar")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "code",
        "logicalType": "string",
    }
    assert actual == expected


def test_retype_should_pass_length_to_varchar():
    # Arrange
    prop = Property(name="code", logicalType="integer")

    # Act
    result = prop.retype("varchar", length=3)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "code",
        "logicalType": "string",
        "logicalTypeOptions": {"maxLength": 3},
    }
    assert actual == expected


def test_retype_should_write_char_of_length_one():
    # Arrange
    prop = Property(name="grade", logicalType="integer")

    # Act
    result = prop.retype("char")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "grade",
        "logicalType": "string",
        "logicalTypeOptions": {"minLength": 1, "maxLength": 1},
    }
    assert actual == expected


def test_retype_should_pass_size_to_fixed():
    # Arrange
    prop = Property(name="hash", logicalType="integer")

    # Act
    result = prop.retype("fixed", size=16)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "hash",
        "logicalType": "string",
        "customProperties": [
            {"property": "binary", "value": True},
            {"property": "typeSize", "value": 16},
        ],
    }
    assert actual == expected


def test_retype_should_pass_time_unit_to_timestamp_ntz():
    # Arrange
    prop = Property(name="created_at", logicalType="string")

    # Act
    result = prop.retype("timestamp_ntz", time_unit="millis")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "created_at",
        "logicalType": "timestamp",
        "logicalTypeOptions": {"timezone": False},
        "customProperties": [{"property": "timeUnit", "value": "millis"}],
    }
    assert actual == expected


def test_retype_should_pass_time_unit_to_time():
    # Arrange
    prop = Property(name="opens_at", logicalType="string")

    # Act
    result = prop.retype("time", time_unit="nanos")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "opens_at",
        "logicalType": "time",
        "customProperties": [{"property": "timeUnit", "value": "nanos"}],
    }
    assert actual == expected


def test_retype_should_raise_schema_error_when_type_is_unknown():
    # Arrange
    prop = Property(name="age", logicalType="integer")

    # Act / Assert
    with pytest.raises(SchemaError):
        prop.retype("text")


def test_retype_should_raise_schema_error_when_fixed_has_no_size():
    # Arrange
    prop = Property(name="hash", logicalType="integer")

    # Act / Assert
    with pytest.raises(SchemaError):
        prop.retype("fixed")


def test_retype_should_raise_type_error_when_argument_does_not_apply():
    # Arrange
    prop = Property(name="x")

    # Act / Assert
    with pytest.raises(TypeError):
        prop.retype("int32", length=5)


def test_retype_should_raise_type_error_when_char_has_length():
    # Arrange
    prop = Property(name="grade", logicalType="integer")

    # Act / Assert
    with pytest.raises(TypeError):
        prop.retype("char", length=2)


def test_retype_should_raise_schema_error_when_precision_is_zero():
    # Arrange
    prop = Property(name="price", logicalType="string")

    # Act / Assert
    with pytest.raises(SchemaError):
        prop.retype("decimal", precision=0)


@pytest.mark.parametrize(
    "type, arguments",
    [
        ("number", {"precision": 0}),
        ("decimal", {"scale": -1}),
        ("number", {"scale": -1}),
        ("fixed", {"size": 0}),
        ("varchar", {"length": 0}),
        ("array", {"of": "bad"}),
        ("map", {"key": "bad"}),
        ("map", {"value": "bad"}),
        ("time", {"time_unit": "bad"}),
        ("timestamp", {"time_unit": "bad"}),
        ("timestamp_ntz", {"time_unit": "bad"}),
    ],
)
def test_retype_should_raise_schema_error_when_argument_is_invalid(type, arguments):
    # Arrange
    prop = Property(name="code", logicalType="string")

    # Act / Assert
    with pytest.raises(SchemaError):
        prop.retype(type, **arguments)


@pytest.mark.parametrize(
    "type, arguments",
    [
        ("fixed", {}),
        ("decimal", {"precision": 0}),
        ("number", {"precision": 0}),
        ("decimal", {"scale": -1}),
        ("number", {"scale": -1}),
        ("fixed", {"size": 0}),
        ("varchar", {"length": 0}),
        ("array", {"of": "bad"}),
        ("map", {"key": "bad"}),
        ("map", {"value": "bad"}),
        ("time", {"time_unit": "bad"}),
        ("timestamp", {"time_unit": "bad"}),
        ("timestamp_ntz", {"time_unit": "bad"}),
    ],
)
def test_retype_should_leave_property_unchanged_when_argument_is_invalid(type, arguments):
    # Arrange
    prop = Property(
        name="code",
        description="Customer code",
        logicalType="string",
        logicalTypeOptions={"maxLength": 3},
    )

    # Act
    with pytest.raises(SchemaError):
        prop.retype(type, **arguments)

    # Assert
    actual = prop.model_dump(exclude_unset=True)
    expected = {
        "name": "code",
        "description": "Customer code",
        "logicalType": "string",
        "logicalTypeOptions": {"maxLength": 3},
    }
    assert actual == expected


def test_require_should_mark_property_as_required():
    # Arrange
    prop = Property(name="age", logicalType="integer")

    # Act
    result = prop.require()

    # Assert
    actual = (
        result is prop,
        prop.required,
    )
    expected = (
        True,
        True,
    )
    assert actual == expected


def test_optional_should_mark_property_as_optional():
    # Arrange
    prop = Property(name="age", logicalType="integer", required=True)

    # Act
    result = prop.optional()

    # Assert
    actual = (
        result is prop,
        prop.required,
    )
    expected = (
        True,
        False,
    )
    assert actual == expected


def test_flatten_should_return_descendants_by_path():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[
            Property(
                name="address",
                logicalType="object",
                properties=[Property(name="city", logicalType="string")],
            ),
            Property(name="age", logicalType="integer"),
        ],
    )

    # Act
    result = prop.flatten()

    # Assert
    actual = list(result)
    expected = ["address", "address.city", "age"]
    assert actual == expected


def test_flatten_should_go_through_arrays_and_maps():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[
            Property(
                name="friends",
                logicalType="array",
                items=Property(
                    logicalType="object",
                    properties=[Property(name="name", logicalType="string")],
                ),
            ),
            Property(
                name="attributes",
                logicalType="map",
                map=Map(
                    key=Property(logicalType="string"),
                    value=Property(
                        logicalType="object",
                        properties=[Property(name="color", logicalType="string")],
                    ),
                ),
            ),
        ],
    )

    # Act
    result = prop.flatten()

    # Assert
    actual = list(result)
    expected = ["friends", "friends.name", "attributes", "attributes.color"]
    assert actual == expected


def test_sort_should_sort_children_by_name_at_every_level():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[
            Property(name="name", logicalType="string"),
            Property(
                name="Address",
                logicalType="object",
                properties=[
                    Property(name="zip", logicalType="string"),
                    Property(name="City", logicalType="string"),
                ],
            ),
        ],
    )

    # Act
    result = prop.sort()

    # Assert
    actual = (
        result is prop,
        list(prop.flatten()),
    )
    expected = (
        True,
        ["Address", "Address.City", "Address.zip", "name"],
    )
    assert actual == expected


def test_normalize_field_names_should_rename_descendants_to_case():
    # Arrange
    prop = Property(
        name="Profile",
        logicalType="object",
        properties=[
            Property(
                name="HomeAddress",
                logicalType="object",
                properties=[Property(name="ZipCode", logicalType="string")],
            )
        ],
    )

    # Act
    result = prop.normalize_field_names(Case.SNAKE)

    # Assert
    actual = (
        result is prop,
        prop.name,
        list(prop.flatten()),
    )
    expected = (
        True,
        "Profile",
        ["home_address", "home_address.zip_code"],
    )
    assert actual == expected


def test_normalize_field_names_should_raise_schema_error_when_siblings_collide():
    # Arrange
    prop = Property(
        name="profile",
        logicalType="object",
        properties=[
            Property(name="FirstName", logicalType="string"),
            Property(name="first_name", logicalType="string"),
        ],
    )

    # Act / Assert
    with pytest.raises(SchemaError):
        prop.normalize_field_names(Case.SNAKE)


def test_has_unique_names_should_return_properties_when_names_are_unique():
    # Arrange
    properties = [
        Property(name="age", logicalType="integer"),
        Property(name="city", logicalType="string"),
    ]

    # Act
    result = Property.has_unique_names(properties)

    # Assert
    assert result is properties


def test_has_unique_names_should_raise_schema_error_when_a_property_has_no_name():
    # Arrange
    properties = [Property(logicalType="string")]

    # Act / Assert
    with pytest.raises(SchemaError):
        Property.has_unique_names(properties)


def test_property_should_default_to_spec_values():
    # Act
    result = Property(name="id")

    # Assert
    actual = (
        result.required,
        result.unique,
        result.partitioned,
        result.criticalDataElement,
        result.deprecated,
        result.primaryKeyPosition,
        result.partitionKeyPosition,
        result.semanticType,
        result.primaryKey,
    )
    expected = (
        False,
        False,
        False,
        False,
        False,
        -1,
        -1,
        "column",
        None,
    )
    assert actual == expected


def test_property_should_write_semantic_type_member_as_text():
    # Act
    result = Property(name="amount", semanticType=SemanticType.MEASURE)

    # Assert
    actual = result.to_yaml()
    expected = "name: amount\nsemanticType: measure\n"
    assert actual == expected


@pytest.mark.parametrize(
    "logical_type, options_type",
    [
        ("string", StringOptions),
        ("date", DateOptions),
        ("timestamp", TimestampOptions),
        ("time", TimestampOptions),
        ("integer", IntegerOptions),
        ("number", NumberOptions),
        ("object", ObjectOptions),
        ("array", ArrayOptions),
        ("vector", VectorOptions),
    ],
)
def test_property_should_read_options_of_its_logical_type(logical_type, options_type):
    # Act
    result = Property(name="value", logicalType=logical_type, logicalTypeOptions={})

    # Assert
    assert type(result.logicalTypeOptions) is options_type


@pytest.mark.parametrize("logical_type", ["boolean", "map", None])
def test_property_should_accept_any_option_when_logical_type_has_no_options(logical_type):
    # Act
    result = Property(
        name="value",
        logicalType=logical_type,
        logicalTypeOptions={"precision": 3},
    )

    # Assert
    actual = result.logicalTypeOptions.model_dump()
    expected = {"precision": 3}
    assert actual == expected


@pytest.mark.parametrize(
    "attributes, expected",
    [
        (
            {"logicalType": "object", "typeName": "Address"},
            [{"property": "typeName", "value": "Address"}],
        ),
        (
            {"logicalType": "object", "namespace": "com.acme"},
            [{"property": "namespace", "value": "com.acme"}],
        ),
        ({"logicalType": "string", "binary": True}, [{"property": "binary", "value": True}]),
        ({"logicalType": "number", "precision": 10}, [{"property": "precision", "value": 10}]),
        ({"logicalType": "number", "scale": 2}, [{"property": "scale", "value": 2}]),
        ({"logicalType": "string", "typeSize": 16}, [{"property": "typeSize", "value": 16}]),
        (
            {"logicalType": "timestamp", "timeUnit": "millis"},
            [{"property": "timeUnit", "value": "millis"}],
        ),
    ],
    ids=["typeName", "namespace", "binary", "precision", "scale", "typeSize", "timeUnit"],
)
def test_model_dump_should_write_convention_field_as_custom_property(attributes, expected):
    # Arrange
    prop = Property(name="field", **attributes)

    # Act
    result = prop.model_dump(mode="json", exclude_unset=True)

    # Assert
    actual = result["customProperties"]
    assert actual == expected


def test_model_dump_should_write_convention_fields_first_in_their_order():
    # Arrange
    prop = Property(
        name="price",
        logicalType="number",
        scale=2,
        precision=10,
        customProperties=[{"property": "pii", "value": True}],
    )

    # Act
    result = prop.model_dump(mode="json", exclude_unset=True)

    # Assert
    actual = result["customProperties"]
    expected = [
        {"property": "precision", "value": 10},
        {"property": "scale", "value": 2},
        {"property": "pii", "value": True},
    ]
    assert actual == expected


def test_model_dump_should_not_write_convention_fields_that_are_not_set():
    # Arrange
    prop = Property(name="price", logicalType="number")

    # Act
    result = prop.model_dump(mode="json", exclude_unset=True)

    # Assert
    actual = result
    expected = {"name": "price", "logicalType": "number"}
    assert actual == expected


def test_model_dump_should_not_write_convention_fields_when_custom_properties_are_excluded():
    # Arrange
    prop = Property(name="price", logicalType="number", precision=10)

    # Act
    result = prop.model_dump(mode="json", exclude_unset=True, exclude={"customProperties"})

    # Assert
    actual = result
    expected = {"name": "price", "logicalType": "number"}
    assert actual == expected


def test_property_should_take_convention_field_from_custom_property():
    # Act
    result = Property(
        name="price",
        logicalType="number",
        customProperties=[{"property": "precision", "value": 10}],
    )

    # Assert
    actual = (
        result.precision,
        result.customProperties,
    )
    expected = (
        10,
        None,
    )
    assert actual == expected


def test_property_should_read_back_convention_field_it_wrote():
    # Arrange
    written = Property(
        name="at",
        logicalType="timestamp",
        timeUnit="millis",
    ).model_dump(mode="json", exclude_unset=True)

    # Act
    result = Property.model_validate(written)

    # Assert
    actual = result.timeUnit
    expected = "millis"
    assert actual == expected


@pytest.mark.parametrize(
    "custom_property",
    [
        {"property": "precision", "value": 10, "vendor": "avro"},
        {"property": "precision", "value": 10, "description": "Digits"},
        {"property": "precision", "value": 10, "id": "precision_id"},
    ],
    ids=["vendor", "description", "id"],
)
def test_property_should_keep_custom_property_with_more_than_name_and_value(custom_property):
    # Act
    result = Property(name="price", logicalType="number", customProperties=[custom_property])

    # Assert
    actual = (
        result.precision,
        result.model_dump(mode="json", exclude_unset=True)["customProperties"],
    )
    expected = (
        None,
        [custom_property],
    )
    assert actual == expected


def test_property_should_prefer_convention_field_over_custom_property():
    # Act
    result = Property(
        name="price",
        logicalType="number",
        precision=12,
        customProperties=[{"property": "precision", "value": 10}],
    )

    # Assert
    actual = result.precision
    expected = 12
    assert actual == expected


def test_property_should_raise_model_error_when_logical_type_is_unknown():
    # Act / Assert
    with pytest.raises(ModelError):
        Property(name="code", logicalType="varchar")


def test_property_should_raise_model_error_when_option_belongs_to_another_type():
    # Act / Assert
    with pytest.raises(ModelError):
        Property(name="code", logicalType="string", logicalTypeOptions={"minimum": 1})


def test_property_should_raise_schema_error_when_relationship_has_from():
    # Act / Assert
    with pytest.raises(SchemaError, match="A property relationship cannot have `from`"):
        Property(
            name="customer_id",
            logicalType="integer",
            relationships=[{"from": "orders.customer_id", "to": "customers.id"}],
        )


def test_property_should_raise_schema_error_when_built_with_duplicate_children():
    # Act / Assert
    with pytest.raises(SchemaError):
        Property(
            name="profile",
            logicalType="object",
            properties=[
                Property(name="age", logicalType="integer"),
                Property(name="Age", logicalType="integer"),
            ],
        )


@pytest.mark.parametrize(
    "attributes",
    [
        {"logicalType": "number", "precision": 0},
        {"logicalType": "number", "scale": -1},
        {"logicalType": "string", "typeSize": 0},
        {"logicalType": "timestamp", "timeUnit": "seconds"},
    ],
    ids=["precision", "scale", "typeSize", "timeUnit"],
)
def test_property_should_raise_model_error_when_convention_field_is_invalid(attributes):
    # Act / Assert
    with pytest.raises(ModelError):
        Property(name="field", **attributes)
