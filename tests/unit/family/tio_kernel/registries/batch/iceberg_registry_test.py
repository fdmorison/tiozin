from pathlib import Path

from tiozin.family.tio_kernel import IcebergBatchRegistry


# ============================================================================
# catalog_type
# ============================================================================
def test_catalog_type_should_default_to_sqlite_when_not_provided(tmp_path: Path):
    # Act
    result = IcebergBatchRegistry(location=str(tmp_path))

    # Assert
    actual = result.catalog_type
    expected = "sqlite"
    assert actual == expected
