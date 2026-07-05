from pathlib import Path

import pytest

from tiozin.family.tio_kernel import IcebergBatchRegistry


# ============================================================================
# _catalog_properties
# ============================================================================
def test_catalog_properties_should_build_sql_uri_and_file_warehouse_for_sqlite_catalog(
    tmp_path: Path,
):
    # Arrange
    registry = IcebergBatchRegistry(location=str(tmp_path), catalog_type="sqlite")

    # Act
    result = registry._catalog_properties()

    # Assert
    actual = result
    expected = {
        "type": "sql",
        "uri": f"sqlite:///{tmp_path}/catalog.db",
        "warehouse": f"file://{tmp_path}",
    }
    assert actual == expected


def test_catalog_properties_should_default_to_sqlite_catalog_when_type_not_provided(
    tmp_path: Path,
):
    # Arrange
    registry = IcebergBatchRegistry(location=str(tmp_path))

    # Act
    result = registry._catalog_properties()

    # Assert
    actual = result
    expected = {
        "type": "sql",
        "uri": f"sqlite:///{tmp_path}/catalog.db",
        "warehouse": f"file://{tmp_path}",
    }
    assert actual == expected


def test_catalog_properties_should_create_location_directory_for_sqlite_catalog(tmp_path: Path):
    # Arrange
    location = tmp_path / "warehouse"
    registry = IcebergBatchRegistry(location=str(location), catalog_type="sqlite")

    # Act
    registry._catalog_properties()

    # Assert
    assert location.exists()


def test_catalog_properties_should_build_uri_from_location_for_rest_catalog():
    # Arrange
    registry = IcebergBatchRegistry(location="https://catalog.example.com", catalog_type="rest")

    # Act
    result = registry._catalog_properties()

    # Assert
    actual = result
    expected = {
        "type": "rest",
        "uri": "https://catalog.example.com",
    }
    assert actual == expected


def test_catalog_properties_should_build_only_type_for_generic_catalog():
    # Arrange
    registry = IcebergBatchRegistry(location="s3://bucket/lake", catalog_type="glue")

    # Act
    result = registry._catalog_properties()

    # Assert
    actual = result
    expected = {
        "type": "glue",
    }
    assert actual == expected


@pytest.mark.parametrize(
    "catalog_type, location",
    [
        ("sqlite", None),
        ("rest", "https://catalog.example.com"),
        ("glue", "s3://bucket/lake"),
    ],
)
def test_catalog_properties_should_pass_extra_options_through(
    tmp_path: Path, catalog_type: str, location: str
):
    # Arrange
    location = location or str(tmp_path)
    registry = IcebergBatchRegistry(location=location, catalog_type=catalog_type, extra1="value1")

    # Act
    result = registry._catalog_properties()

    # Assert
    actual = result["extra1"]
    expected = "value1"
    assert actual == expected
