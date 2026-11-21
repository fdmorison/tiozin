from pathlib import Path

from openlineage.client.generated.schema_dataset import SchemaDatasetFacet, SchemaDatasetFacetFields

from tiozin import LineageDataset, Schema

_TIOZIN_SCHEMA_YAML = Path("tests/mocks/schemas/user/tiozin.odcs.yaml").read_text()


def test_facets_should_build_openlineage_schema_facet():
    # Arrange
    dataset = LineageDataset(
        namespace="s3://my-bucket",
        name="users",
        schema=Schema.from_yaml(_TIOZIN_SCHEMA_YAML),
    )

    # Act
    result = dataset.facets()

    # Assert
    actual = result
    expected = {
        "schema": SchemaDatasetFacet(
            fields=[
                SchemaDatasetFacetFields(name="name", type="string", fields=[]),
                SchemaDatasetFacetFields(
                    name="profile",
                    type="object",
                    fields=[SchemaDatasetFacetFields(name="age", type="integer", fields=[])],
                ),
                SchemaDatasetFacetFields(
                    name="friends",
                    type="array",
                    fields=[
                        SchemaDatasetFacetFields(
                            name="_element",
                            type="object",
                            fields=[
                                SchemaDatasetFacetFields(name="name", type="string", fields=[]),
                            ],
                        )
                    ],
                ),
            ]
        )
    }
    assert actual == expected
