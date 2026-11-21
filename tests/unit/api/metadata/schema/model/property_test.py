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
