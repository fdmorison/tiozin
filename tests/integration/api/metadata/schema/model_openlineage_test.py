from pathlib import Path

import pytest
from openlineage.client.generated.schema_dataset import SchemaDatasetFacet, SchemaDatasetFacetFields

from tiozin.api.metadata.schema.model import Schema

_TIOZIN_SCHEMA_YAML = Path("tests/mocks/schemas/user/tiozin.odcs.yaml").read_text()


def test_export_should_build_openlineage_facet():
    # Arrange
    tiozin_schema = Schema.from_yaml(_TIOZIN_SCHEMA_YAML)

    # Act
    result = tiozin_schema.export("openlineage")

    # Assert
    actual = result
    expected = SchemaDatasetFacet(
        fields=[
            SchemaDatasetFacetFields(name="name", type="string", description=None),
            SchemaDatasetFacetFields(name="profile", type="object", description=None),
            SchemaDatasetFacetFields(name="profile.age", type="integer", description=None),
            SchemaDatasetFacetFields(name="friends", type="array", description=None),
            SchemaDatasetFacetFields(name="friends[].name", type="string", description=None),
        ]
    )
    assert actual == expected


def test_import_should_raise_not_implemented():
    # Arrange
    facet = SchemaDatasetFacet(fields=[])

    # Act / Assert
    with pytest.raises(NotImplementedError):
        Schema.import_("openlineage", facet)
