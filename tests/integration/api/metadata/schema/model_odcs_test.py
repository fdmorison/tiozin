from pathlib import Path

from open_data_contract_standard.model import SchemaObject

from tiozin.api.metadata.schema.model import SchemaManifest
from tiozin.utils import load_yaml

_TIOZIN_SCHEMA_YAML = Path("tests/mocks/schemas/user/tiozin.odcs.yaml").read_text()


def test_export_should_build_odcs_schema():
    # Arrange
    tiozin_schema = SchemaManifest.from_yaml(_TIOZIN_SCHEMA_YAML)

    # Act
    result: SchemaObject = tiozin_schema.export("odcs")

    # Assert
    actual = result.model_dump()
    expected = tiozin_schema.schema.model_dump()
    assert actual == expected


def test_import_should_parse_odcs_schema():
    # Arrange
    odcs_schema = SchemaObject(**load_yaml(_TIOZIN_SCHEMA_YAML))

    # Act
    result = SchemaManifest.import_("odcs", odcs_schema)

    # Assert
    actual = result.schema.model_dump()
    expected = odcs_schema.model_dump()
    assert actual == expected


def test_roundtrip_should_preserve_schema():
    # Arrange
    original = SchemaManifest.from_yaml(_TIOZIN_SCHEMA_YAML)

    # Act
    restored = SchemaManifest.import_("odcs", original.export("odcs"))

    # Assert
    actual = restored.model_dump()
    expected = original.model_dump()
    assert actual == expected
