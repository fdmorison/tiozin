from tiozin import Schema
from tiozin.api.metadata.schema.merges import DocumentationMerge
from tiozin.api.metadata.schema.model import AuthoritativeDefinition, Synonym


def test_merge_should_copy_property_documentation():
    # Arrange
    observed = Schema(name="observed").string("id")
    contract = Schema(name="contract").string("id", description="Customer identifier")

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = result["id"].description
    expected = "Customer identifier"
    assert actual == expected


def test_merge_should_copy_every_documentation_attribute():
    # Arrange
    observed = Schema(name="observed").string("id")
    contract = Schema(name="contract").string(
        "id",
        description="Customer identifier",
        businessName="Customer ID",
        tags=["key"],
        synonyms=[{"synonym": "customer_number"}],
        authoritativeDefinitions=[{"url": "https://example.com/id", "type": "businessDefinition"}],
        classification="public",
        examples=["c-001"],
        criticalDataElement=True,
    )

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = (
        result["id"].description,
        result["id"].businessName,
        result["id"].tags,
        result["id"].synonyms,
        result["id"].authoritativeDefinitions,
        result["id"].classification,
        result["id"].examples,
        result["id"].criticalDataElement,
    )
    expected = (
        "Customer identifier",
        "Customer ID",
        ["key"],
        [Synonym(synonym="customer_number")],
        [AuthoritativeDefinition(url="https://example.com/id", type="businessDefinition")],
        "public",
        ["c-001"],
        True,
    )
    assert actual == expected


def test_merge_should_replace_target_documentation():
    # Arrange
    observed = Schema(name="observed").string(
        "id",
        description="Old note",
        tags=["old"],
        classification="internal",
    )
    contract = Schema(name="contract").string(
        "id",
        description="Customer identifier",
        tags=["key"],
        classification="public",
    )

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = (
        result["id"].description,
        result["id"].tags,
        result["id"].classification,
    )
    expected = (
        "Customer identifier",
        ["key"],
        "public",
    )
    assert actual == expected


def test_merge_should_match_property_ignoring_case():
    # Arrange
    observed = Schema(name="observed").string("ID")
    contract = Schema(name="contract").string("id", description="Customer identifier")

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = result["ID"].description
    expected = "Customer identifier"
    assert actual == expected


def test_merge_should_copy_schema_documentation():
    # Arrange
    observed = Schema(name="observed")
    contract = Schema(name="contract", description="Customers", tags=["gold"])

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = (
        result.description,
        result.tags,
    )
    expected = (
        "Customers",
        ["gold"],
    )
    assert actual == expected


def test_merge_should_preserve_target_structure_and_types():
    # Arrange
    observed = Schema(name="observed").integer("ID")
    contract = Schema(name="contract").string(
        "id",
        description="Customer identifier",
        required=True,
        primaryKey=True,
    )

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = (
        result["ID"].name,
        result["ID"].logicalType,
        result["ID"].required,
        result["ID"].primaryKey,
    )
    expected = (
        "ID",
        "integer",
        False,
        None,
    )
    assert actual == expected


def test_merge_should_preserve_target_documentation_when_source_has_none():
    # Arrange
    observed = Schema(name="observed").string("id", description="Observed note")
    contract = Schema(name="contract").string("id")

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = result["id"].description
    expected = "Observed note"
    assert actual == expected


def test_merge_should_preserve_target_documentation_when_source_only_has_default():
    # Arrange
    observed = Schema(name="observed").string("id", criticalDataElement=True)
    contract = Schema(name="contract").string("id")

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    assert result["id"].criticalDataElement is True


def test_merge_should_preserve_unmatched_target_property():
    # Arrange
    observed = (
        Schema(name="observed")
        .string("id")
        .string(
            "extra",
            description="Observed note",
        )
    )
    contract = Schema(name="contract").string(
        "id",
        description="Customer identifier",
    )

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = result["extra"].description
    expected = "Observed note"
    assert actual == expected


def test_merge_should_return_documented_target():
    # Arrange
    observed = Schema(name="observed").string("id")
    contract = Schema(name="contract").string("id", description="Customer identifier")

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    assert result is observed


def test_merge_should_not_change_source():
    # Arrange
    observed = Schema(name="observed", description="Observed note").integer("ID").string("extra")
    contract = Schema(name="contract").string("id", description="Customer identifier")

    # Act
    DocumentationMerge().merge(observed, contract)

    # Assert
    actual = contract.model_dump(exclude_unset=True)
    expected = {
        "name": "contract",
        "properties": [
            {
                "name": "id",
                "logicalType": "string",
                "description": "Customer identifier",
            },
        ],
    }
    assert actual == expected


def test_merge_should_copy_documentation_values_independently():
    # Arrange
    observed = Schema(name="observed").string("id")
    contract = Schema(name="contract").string("id", tags=["key"])

    # Act
    result = DocumentationMerge().merge(observed, contract)
    result["id"].tags.append("changed")

    # Assert
    actual = contract["id"].tags
    expected = ["key"]
    assert actual == expected


def test_merge_should_document_property_inside_object():
    # Arrange
    observed = Schema(name="observed").object("address").string("address.city")
    contract = (
        Schema(name="contract").object("address").string("address.city", description="City name")
    )

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = result["address.city"].description
    expected = "City name"
    assert actual == expected


def test_merge_should_document_property_inside_array_of_objects():
    # Arrange
    observed = Schema(name="observed").array("friends", of="object").string("friends.name")
    contract = (
        Schema(name="contract")
        .array("friends", of="object")
        .string("friends.name", description="Friend name")
    )

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = result["friends.name"].description
    expected = "Friend name"
    assert actual == expected


def test_merge_should_document_property_inside_map_of_objects():
    # Arrange
    observed = Schema(name="observed").map("scores", value="object").integer("scores.points")
    contract = (
        Schema(name="contract")
        .map("scores", value="object")
        .integer("scores.points", description="Points earned")
    )

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = result["scores.points"].description
    expected = "Points earned"
    assert actual == expected


def test_merge_should_document_array_items():
    # Arrange
    observed = Schema(name="observed").array("tags", of="string")
    contract = Schema(name="contract").array("tags", of="string")
    contract["tags"].items.description = "One tag"

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = result["tags"].items.description
    expected = "One tag"
    assert actual == expected


def test_merge_should_document_map_key():
    # Arrange
    observed = Schema(name="observed").map("labels", value="string")
    contract = Schema(name="contract").map("labels", value="string")
    contract["labels"].map.key.description = "Label name"

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = result["labels"].map.key.description
    expected = "Label name"
    assert actual == expected


def test_merge_should_document_map_value():
    # Arrange
    observed = Schema(name="observed").map("labels", value="string")
    contract = Schema(name="contract").map("labels", value="string")
    contract["labels"].map.value.description = "Label text"

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = result["labels"].map.value.description
    expected = "Label text"
    assert actual == expected


def test_merge_should_copy_documentation_when_types_differ():
    # Arrange
    observed = Schema(name="observed").integer("amount")
    contract = Schema(name="contract").string("amount", description="Amount in cents")

    # Act
    result = DocumentationMerge().merge(observed, contract)

    # Assert
    actual = result["amount"].description
    expected = "Amount in cents"
    assert actual == expected
