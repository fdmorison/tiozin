import pytest

from tiozin import Schema
from tiozin.api.metadata.schema.merges import BackwardCompatibleEvolution
from tiozin.api.metadata.schema.model import Property
from tiozin.exceptions import SchemaError


def test_merge_should_add_new_property():
    # Arrange
    contract = Schema(name="contract").string("id")
    observed = Schema(name="observed").string("id").string("email")

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    actual = list(result.flatten())
    expected = ["id", "email"]
    assert actual == expected


def test_merge_should_add_new_property_as_optional():
    # Arrange
    contract = Schema(name="contract").string("id")
    observed = Schema(name="observed").string("email", required=True)

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    assert result["email"].required is False


def test_merge_should_add_new_property_without_constraints():
    # Arrange
    contract = Schema(name="contract").string("id")
    observed = Schema(name="observed").string(
        "email",
        primaryKey=True,
        primaryKeyPosition=1,
        unique=True,
        partitioned=True,
        partitionKeyPosition=1,
    )

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    actual = (
        result["email"].primaryKey,
        result["email"].primaryKeyPosition,
        result["email"].unique,
        result["email"].partitioned,
        result["email"].partitionKeyPosition,
    )
    expected = (
        None,
        -1,
        False,
        False,
        -1,
    )
    assert actual == expected


def test_merge_should_preserve_attributes_of_new_property():
    # Arrange
    contract = Schema(name="contract").string("id")
    observed = Schema(name="observed").string(
        "email",
        description="Contact email",
        physicalType="varchar(100)",
        tags=["pii"],
    )

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    actual = (
        result["email"].description,
        result["email"].physicalType,
        result["email"].tags,
    )
    expected = (
        "Contact email",
        "varchar(100)",
        ["pii"],
    )
    assert actual == expected


def test_merge_should_preserve_existing_property():
    # Arrange
    contract = Schema(name="contract").string("id", required=True, primaryKey=True)
    observed = Schema(name="observed").string("id", required=False, unique=True)

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    actual = (
        result["id"].required,
        result["id"].primaryKey,
        result["id"].unique,
    )
    expected = (
        True,
        True,
        False,
    )
    assert actual == expected


def test_merge_should_never_remove_target_property():
    # Arrange
    contract = Schema(name="contract").string("id").string("phone", required=True)
    observed = Schema(name="observed").string("id")

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "contract",
        "properties": [
            {"name": "id", "logicalType": "string"},
            {"name": "phone", "logicalType": "string", "required": True},
        ],
    }
    assert actual == expected


def test_merge_should_add_everything_when_target_is_empty():
    # Arrange
    contract = Schema(name="contract")
    observed = Schema(name="observed").string("id").object("address").string("address.city")

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    actual = list(result.flatten())
    expected = ["id", "address", "address.city"]
    assert actual == expected


def test_merge_should_preserve_target_when_source_is_empty():
    # Arrange
    contract = Schema(name="contract").string("id", required=True)
    observed = Schema(name="observed")

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "contract",
        "properties": [
            {"name": "id", "logicalType": "string", "required": True},
        ],
    }
    assert actual == expected


def test_merge_should_return_evolved_target():
    # Arrange
    contract = Schema(name="contract").string("id")
    observed = Schema(name="observed").string("email")

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    assert result is contract


def test_merge_should_not_change_source():
    # Arrange
    contract = Schema(name="contract").string("id")
    observed = Schema(name="observed").string("email", required=True, primaryKey=True)

    # Act
    BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    actual = observed.model_dump(exclude_unset=True)
    expected = {
        "name": "observed",
        "properties": [
            {
                "name": "email",
                "logicalType": "string",
                "required": True,
                "primaryKey": True,
            },
        ],
    }
    assert actual == expected


def test_merge_should_add_copy_of_source_property():
    # Arrange
    contract = Schema(name="contract").string("id")
    observed = Schema(name="observed").string("email")

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)
    result["email"].description = "Changed after merge"

    # Assert
    assert observed["email"].description is None


def test_merge_should_add_new_property_inside_object():
    # Arrange
    contract = Schema(name="contract").object("address").string("address.city")
    observed = Schema(name="observed").object("address").string("address.zip")

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    actual = list(result.flatten())
    expected = ["address", "address.city", "address.zip"]
    assert actual == expected


def test_merge_should_add_new_property_inside_array_of_objects():
    # Arrange
    contract = Schema(name="contract").array("friends", of="object").string("friends.name")
    observed = Schema(name="observed").array("friends", of="object").integer("friends.age")

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    actual = list(result.flatten())
    expected = ["friends", "friends.name", "friends.age"]
    assert actual == expected


def test_merge_should_add_new_property_inside_map_of_objects():
    # Arrange
    contract = Schema(name="contract").map("scores", value="object").integer("scores.points")
    observed = Schema(name="observed").map("scores", value="object").string("scores.label")

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    actual = list(result.flatten())
    expected = ["scores", "scores.points", "scores.label"]
    assert actual == expected


def test_merge_should_relax_descendants_of_new_object():
    # Arrange
    contract = Schema(name="contract").string("id")
    observed = (
        Schema(name="observed")
        .object("address", required=True)
        .string(
            "address.zip",
            required=True,
            primaryKey=True,
            unique=True,
            partitioned=True,
        )
    )

    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    actual = (
        result["address.zip"].required,
        result["address.zip"].primaryKey,
        result["address.zip"].unique,
        result["address.zip"].partitioned,
    )
    expected = (
        False,
        None,
        False,
        False,
    )
    assert actual == expected


@pytest.mark.parametrize(
    "contract, observed, expected",
    [
        (
            Schema(name="contract").string("id"),
            Schema(name="observed").integer("id"),
            {
                "name": "contract",
                "properties": [
                    {"name": "id", "logicalType": "string"},
                ],
            },
        ),
        (
            Schema(name="contract").object("x").string("x.a"),
            Schema(name="observed").array("x", of="object").string("x.b"),
            {
                "name": "contract",
                "properties": [
                    {
                        "name": "x",
                        "logicalType": "object",
                        "properties": [{"name": "a", "logicalType": "string"}],
                    },
                ],
            },
        ),
        (
            Schema(name="contract").array("m", of="object").string("m.a"),
            Schema(
                name="observed",
                properties=[
                    Property(
                        name="m",
                        logicalType="array",
                        items=Property(
                            logicalType="array",
                            items=Property(
                                logicalType="object",
                                properties=[Property(name="b", logicalType="string")],
                            ),
                        ),
                    ),
                ],
            ),
            {
                "name": "contract",
                "properties": [
                    {
                        "name": "m",
                        "logicalType": "array",
                        "items": {
                            "logicalType": "object",
                            "properties": [{"name": "a", "logicalType": "string"}],
                        },
                    },
                ],
            },
        ),
    ],
    ids=[
        "scalar_type_differs",
        "object_vs_array_of_objects",
        "array_nesting_differs",
    ],
)
def test_merge_should_preserve_target_type(contract: Schema, observed: Schema, expected: dict):
    # Act
    result = BackwardCompatibleEvolution().merge(contract, observed)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    assert actual == expected


@pytest.mark.parametrize(
    "contract, observed, message",
    [
        (
            Schema(name="contract").string("id"),
            Schema(name="observed").string("ID"),
            "Duplicate property `ID`",
        ),
        (
            Schema(name="contract").object("address").string("address.city"),
            Schema(name="observed").object("address").string("address.City"),
            "Duplicate property `City`",
        ),
    ],
    ids=["top_level", "nested"],
)
def test_merge_should_raise_schema_error_when_names_differ_only_by_case(
    contract: Schema, observed: Schema, message: str
):
    # Act / Assert
    with pytest.raises(SchemaError, match=message):
        BackwardCompatibleEvolution().merge(contract, observed)
